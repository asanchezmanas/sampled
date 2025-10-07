# backend/payments.py
import stripe
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
from utils import Logger

# Configurar Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

class SubscriptionPlan(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"

# Configuración de planes
PLANS = {
    SubscriptionPlan.FREE: {
        "name": "Free",
        "price": 0,
        "stripe_price_id": None,
        "limits": {
            "experiments": 2,
            "arms_per_experiment": 2,
            "elements_per_experiment": 1,
            "monthly_visitors": 1000,
            "data_retention_days": 30,
            "team_members": 1,
            "api_calls_per_month": 10000,
            "enable_advanced_analytics": False,
            "enable_heatmaps": False,
            "enable_targeting": False,
            "enable_api_access": False,
            "support": "community"
        }
    },
    SubscriptionPlan.STARTER: {
        "name": "Starter",
        "price": 29,
        "stripe_price_id": os.environ.get("STRIPE_STARTER_PRICE_ID"),
        "limits": {
            "experiments": 10,
            "arms_per_experiment": 5,
            "elements_per_experiment": 3,
            "monthly_visitors": 50000,
            "data_retention_days": 90,
            "team_members": 3,
            "api_calls_per_month": 100000,
            "enable_advanced_analytics": True,
            "enable_heatmaps": True,
            "enable_targeting": True,
            "enable_api_access": True,
            "support": "email"
        }
    },
    SubscriptionPlan.PROFESSIONAL: {
        "name": "Professional",
        "price": 99,
        "stripe_price_id": os.environ.get("STRIPE_PRO_PRICE_ID"),
        "limits": {
            "experiments": 50,
            "arms_per_experiment": 10,
            "elements_per_experiment": 10,
            "monthly_visitors": 500000,
            "data_retention_days": 365,
            "team_members": 10,
            "api_calls_per_month": 1000000,
            "enable_advanced_analytics": True,
            "enable_heatmaps": True,
            "enable_targeting": True,
            "enable_api_access": True,
            "support": "priority"
        }
    },
    SubscriptionPlan.ENTERPRISE: {
        "name": "Enterprise",
        "price": 299,
        "stripe_price_id": os.environ.get("STRIPE_ENTERPRISE_PRICE_ID"),
        "limits": {
            "experiments": -1,  # Unlimited
            "arms_per_experiment": -1,
            "elements_per_experiment": -1,
            "monthly_visitors": -1,
            "data_retention_days": -1,
            "team_members": -1,
            "api_calls_per_month": -1,
            "enable_advanced_analytics": True,
            "enable_heatmaps": True,
            "enable_targeting": True,
            "enable_api_access": True,
            "support": "dedicated"
        }
    }
}

class StripeManager:
    """
    Gestor de pagos con Stripe
    Maneja suscripciones, webhooks, y límites de uso
    """
    
    def __init__(self, database_manager):
        self.db = database_manager
        self.logger = Logger()
        self.webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    
    # ===== CUSTOMER MANAGEMENT =====
    
    async def get_or_create_customer(self, user_id: str, email: str, name: str) -> str:
        """
        Obtener o crear customer de Stripe
        """
        try:
            # Verificar si el usuario ya tiene un customer_id
            customer_id = await self.db.get_user_stripe_customer_id(user_id)
            
            if customer_id:
                # Verificar que el customer existe en Stripe
                try:
                    stripe.Customer.retrieve(customer_id)
                    return customer_id
                except stripe.error.InvalidRequestError:
                    # Customer no existe, crear uno nuevo
                    pass
            
            # Crear nuevo customer en Stripe
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    "user_id": user_id
                }
            )
            
            # Guardar customer_id en la base de datos
            await self.db.update_user_stripe_customer(user_id, customer.id)
            
            self.logger.info(f"Created Stripe customer {customer.id} for user {user_id}")
            return customer.id
            
        except Exception as e:
            self.logger.error(f"Failed to get/create Stripe customer: {str(e)}")
            raise
    
    # ===== SUBSCRIPTION MANAGEMENT =====
    
    async def create_checkout_session(
        self,
        user_id: str,
        plan: SubscriptionPlan,
        success_url: str,
        cancel_url: str,
        trial_days: int = 14
    ) -> Dict[str, Any]:
        """
        Crear sesión de checkout de Stripe
        """
        try:
            # Obtener usuario
            user = await self.db.get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Obtener o crear customer
            customer_id = await self.get_or_create_customer(
                user_id, user['email'], user['name']
            )
            
            # Configuración del plan
            plan_config = PLANS[plan]
            
            if not plan_config['stripe_price_id']:
                raise ValueError(f"Stripe price ID not configured for plan {plan}")
            
            # Crear checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': plan_config['stripe_price_id'],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                subscription_data={
                    'trial_period_days': trial_days,
                    'metadata': {
                        'user_id': user_id,
                        'plan': plan.value
                    }
                },
                metadata={
                    'user_id': user_id,
                    'plan': plan.value
                }
            )
            
            self.logger.info(f"Created checkout session {session.id} for user {user_id}")
            
            return {
                'session_id': session.id,
                'url': session.url
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create checkout session: {str(e)}")
            raise
    
    async def create_portal_session(
        self,
        user_id: str,
        return_url: str
    ) -> Dict[str, Any]:
        """
        Crear sesión del portal de cliente (para gestionar suscripción)
        """
        try:
            customer_id = await self.db.get_user_stripe_customer_id(user_id)
            
            if not customer_id:
                raise ValueError("User has no Stripe customer")
            
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            
            return {
                'url': session.url
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create portal session: {str(e)}")
            raise
    
    async def cancel_subscription(self, user_id: str, immediate: bool = False) -> bool:
        """
        Cancelar suscripción
        """
        try:
            subscription = await self.db.get_user_subscription(user_id)
            
            if not subscription or not subscription['stripe_subscription_id']:
                return False
            
            if immediate:
                # Cancelar inmediatamente
                stripe.Subscription.delete(subscription['stripe_subscription_id'])
            else:
                # Cancelar al final del periodo
                stripe.Subscription.modify(
                    subscription['stripe_subscription_id'],
                    cancel_at_period_end=True
                )
            
            # Actualizar en base de datos
            await self.db.update_subscription_status(
                user_id,
                SubscriptionStatus.CANCELED if immediate else subscription['status']
            )
            
            self.logger.info(f"Canceled subscription for user {user_id} (immediate: {immediate})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel subscription: {str(e)}")
            raise
    
    # ===== WEBHOOK HANDLING =====
    
    def verify_webhook_signature(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """
        Verificar firma del webhook de Stripe
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            return event
        except ValueError as e:
            self.logger.error(f"Invalid webhook payload: {str(e)}")
            raise
        except stripe.error.SignatureVerificationError as e:
            self.logger.error(f"Invalid webhook signature: {str(e)}")
            raise
    
    async def handle_webhook(self, event: Dict[str, Any]) -> bool:
        """
        Manejar eventos de webhook de Stripe
        """
        event_type = event['type']
        data = event['data']['object']
        
        try:
            if event_type == 'checkout.session.completed':
                await self.handle_checkout_completed(data)
                
            elif event_type == 'customer.subscription.created':
                await self.handle_subscription_created(data)
                
            elif event_type == 'customer.subscription.updated':
                await self.handle_subscription_updated(data)
                
            elif event_type == 'customer.subscription.deleted':
                await self.handle_subscription_deleted(data)
                
            elif event_type == 'invoice.payment_succeeded':
                await self.handle_payment_succeeded(data)
                
            elif event_type == 'invoice.payment_failed':
                await self.handle_payment_failed(data)
                
            else:
                self.logger.info(f"Unhandled webhook event type: {event_type}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to handle webhook {event_type}: {str(e)}")
            raise
    
    async def handle_checkout_completed(self, session: Dict[str, Any]):
        """Manejar checkout completado"""
        user_id = session['metadata']['user_id']
        plan = session['metadata']['plan']
        
        self.logger.info(f"Checkout completed for user {user_id}, plan {plan}")
        
        # La suscripción se actualizará con el evento subscription.created
    
    async def handle_subscription_created(self, subscription: Dict[str, Any]):
        """Manejar suscripción creada"""
        user_id = subscription['metadata']['user_id']
        plan = subscription['metadata']['plan']
        
        # Crear o actualizar suscripción en base de datos
        await self.db.create_or_update_subscription(
            user_id=user_id,
            plan=SubscriptionPlan(plan),
            status=SubscriptionStatus(subscription['status']),
            stripe_subscription_id=subscription['id'],
            stripe_customer_id=subscription['customer'],
            current_period_start=datetime.fromtimestamp(
                subscription['current_period_start'], 
                tz=timezone.utc
            ),
            current_period_end=datetime.fromtimestamp(
                subscription['current_period_end'],
                tz=timezone.utc
            ),
            cancel_at_period_end=subscription['cancel_at_period_end']
        )
        
        self.logger.info(f"Subscription created for user {user_id}")
    
    async def handle_subscription_updated(self, subscription: Dict[str, Any]):
        """Manejar suscripción actualizada"""
        user_id = subscription['metadata']['user_id']
        
        await self.db.update_subscription(
            user_id=user_id,
            status=SubscriptionStatus(subscription['status']),
            current_period_end=datetime.fromtimestamp(
                subscription['current_period_end'],
                tz=timezone.utc
            ),
            cancel_at_period_end=subscription['cancel_at_period_end']
        )
        
        self.logger.info(f"Subscription updated for user {user_id}")
    
    async def handle_subscription_deleted(self, subscription: Dict[str, Any]):
        """Manejar suscripción eliminada"""
        user_id = subscription['metadata']['user_id']
        
        # Downgrade a plan gratuito
        await self.db.update_subscription_plan(user_id, SubscriptionPlan.FREE)
        await self.db.update_subscription_status(user_id, SubscriptionStatus.CANCELED)
        
        self.logger.info(f"Subscription deleted for user {user_id}, downgraded to FREE")
    
    async def handle_payment_succeeded(self, invoice: Dict[str, Any]):
        """Manejar pago exitoso"""
        subscription_id = invoice['subscription']
        
        # Actualizar última fecha de pago
        await self.db.update_subscription_last_payment(subscription_id)
        
        self.logger.info(f"Payment succeeded for subscription {subscription_id}")
    
    async def handle_payment_failed(self, invoice: Dict[str, Any]):
        """Manejar pago fallido"""
        subscription_id = invoice['subscription']
        customer_email = invoice['customer_email']
        
        # Marcar como past_due
        await self.db.update_subscription_status_by_stripe_id(
            subscription_id, 
            SubscriptionStatus.PAST_DUE
        )
        
        # TODO: Enviar email de notificación
        self.logger.warning(
            f"Payment failed for subscription {subscription_id} ({customer_email})"
        )
    
    # ===== USAGE TRACKING =====
    
    async def check_usage_limit(
        self,
        user_id: str,
        resource: str,
        current_count: int = None
    ) -> Dict[str, Any]:
        """
        Verificar si el usuario puede crear más del recurso especificado
        
        Returns:
            {
                'allowed': bool,
                'limit': int,
                'current': int,
                'remaining': int
            }
        """
        try:
            # Obtener suscripción del usuario
            subscription = await self.db.get_user_subscription(user_id)
            
            plan = SubscriptionPlan(subscription['plan']) if subscription else SubscriptionPlan.FREE
            plan_limits = PLANS[plan]['limits']
            
            limit = plan_limits.get(resource, 0)
            
            # -1 significa unlimited
            if limit == -1:
                return {
                    'allowed': True,
                    'limit': -1,
                    'current': current_count or 0,
                    'remaining': -1,
                    'unlimited': True
                }
            
            # Obtener count actual si no se proporciona
            if current_count is None:
                current_count = await self.db.get_user_resource_count(user_id, resource)
            
            allowed = current_count < limit
            remaining = max(0, limit - current_count)
            
            return {
                'allowed': allowed,
                'limit': limit,
                'current': current_count,
                'remaining': remaining,
                'unlimited': False
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check usage limit: {str(e)}")
            # En caso de error, permitir por defecto
            return {'allowed': True, 'limit': -1, 'current': 0, 'remaining': -1}
    
    async def track_api_call(self, user_id: str) -> bool:
        """
        Registrar llamada a la API y verificar límite
        """
        try:
            # Incrementar contador mensual
            count = await self.db.increment_api_calls(user_id)
            
            # Verificar límite
            usage = await self.check_usage_limit(user_id, 'api_calls_per_month', count)
            
            if not usage['allowed']:
                self.logger.warning(f"User {user_id} exceeded API call limit")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to track API call: {str(e)}")
            return True  # Permitir en caso de error
    
    async def get_feature_access(self, user_id: str, feature: str) -> bool:
        """
        Verificar si el usuario tiene acceso a una feature específica
        """
        try:
            subscription = await self.db.get_user_subscription(user_id)
            
            plan = SubscriptionPlan(subscription['plan']) if subscription else SubscriptionPlan.FREE
            plan_limits = PLANS[plan]['limits']
            
            return plan_limits.get(f'enable_{feature}', False)
            
        except Exception as e:
            self.logger.error(f"Failed to check feature access: {str(e)}")
            return False
    
    # ===== PLAN INFORMATION =====
    
    def get_plan_info(self, plan: SubscriptionPlan) -> Dict[str, Any]:
        """Obtener información completa del plan"""
        return PLANS[plan]
    
    def get_all_plans(self) -> Dict[str, Dict[str, Any]]:
        """Obtener información de todos los planes"""
        return PLANS
    
    async def get_user_plan_info(self, user_id: str) -> Dict[str, Any]:
        """Obtener información del plan actual del usuario"""
        try:
            subscription = await self.db.get_user_subscription(user_id)
            
            if not subscription:
                return {
                    'plan': SubscriptionPlan.FREE.value,
                    'status': None,
                    'limits': PLANS[SubscriptionPlan.FREE]['limits'],
                    'price': 0
                }
            
            plan = SubscriptionPlan(subscription['plan'])
            
            return {
                'plan': plan.value,
                'status': subscription['status'],
                'limits': PLANS[plan]['limits'],
                'price': PLANS[plan]['price'],
                'current_period_end': subscription['current_period_end'],
                'cancel_at_period_end': subscription.get('cancel_at_period_end', False)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get user plan info: {str(e)}")
            return {
                'plan': SubscriptionPlan.FREE.value,
                'status': None,
                'limits': PLANS[SubscriptionPlan.FREE]['limits'],
                'price': 0
            }
    
    # ===== TRIAL MANAGEMENT =====
    
    async def start_trial(
        self,
        user_id: str,
        plan: SubscriptionPlan,
        trial_days: int = 14
    ) -> bool:
        """
        Iniciar periodo de prueba
        """
        try:
            trial_end = datetime.now(timezone.utc) + timedelta(days=trial_days)
            
            await self.db.create_or_update_subscription(
                user_id=user_id,
                plan=plan,
                status=SubscriptionStatus.TRIALING,
                trial_end=trial_end
            )
            
            self.logger.info(f"Started {trial_days}-day trial for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start trial: {str(e)}")
            return False
    
    async def check_trial_status(self, user_id: str) -> Dict[str, Any]:
        """
        Verificar estado del trial
        """
        try:
            subscription = await self.db.get_user_subscription(user_id)
            
            if not subscription:
                return {'has_trial': False}
            
            if subscription['status'] != SubscriptionStatus.TRIALING.value:
                return {'has_trial': False}
            
            trial_end = subscription.get('trial_end')
            if not trial_end:
                return {'has_trial': False}
            
            now = datetime.now(timezone.utc)
            days_remaining = (trial_end - now).days
            
            return {
                'has_trial': True,
                'trial_end': trial_end,
                'days_remaining': max(0, days_remaining),
                'expired': days_remaining < 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to check trial status: {str(e)}")
            return {'has_trial': False}
