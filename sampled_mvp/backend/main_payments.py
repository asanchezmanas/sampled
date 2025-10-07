# backend/main_payments.py
"""
Endpoints de pagos para agregar a main.py
"""

from fastapi import HTTPException, Depends, Request, Header
from typing import Optional
from payments import StripeManager, SubscriptionPlan, PLANS
from pydantic import BaseModel

# Inicializar Stripe Manager
stripe_manager = StripeManager(db)

# ===== MODELS =====

class CheckoutRequest(BaseModel):
    plan: str
    trial_days: int = 14

class PortalRequest(BaseModel):
    return_url: str

class CancelSubscriptionRequest(BaseModel):
    immediate: bool = False

# ===== MIDDLEWARE PARA VERIFICAR LÍMITES =====

async def check_experiment_limit(
    user_id: str = Depends(get_current_user)
):
    """Middleware para verificar límite de experimentos"""
    # Obtener count actual
    experiments = await db.get_user_experiments(user_id)
    current_count = len(experiments)
    
    # Verificar límite
    usage = await stripe_manager.check_usage_limit(
        user_id, 
        'experiments', 
        current_count
    )
    
    if not usage['allowed']:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                'error': 'Experiment limit reached',
                'message': f"Your plan allows {usage['limit']} experiments. Please upgrade to create more.",
                'limit': usage['limit'],
                'current': usage['current'],
                'upgrade_url': '/settings/billing'
            }
        )
    
    return usage

async def check_feature_access(
    feature: str,
    user_id: str = Depends(get_current_user)
):
    """Middleware para verificar acceso a feature"""
    has_access = await stripe_manager.get_feature_access(user_id, feature)
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                'error': f'Feature not available',
                'message': f'This feature is not available in your current plan. Please upgrade.',
                'feature': feature,
                'upgrade_url': '/settings/billing'
            }
        )
    
    return True

# ===== SUBSCRIPTION ENDPOINTS =====

@app.get("/api/billing/plans")
async def get_available_plans():
    """Obtener información de todos los planes disponibles"""
    plans = stripe_manager.get_all_plans()
    
    # Formatear para el frontend
    formatted_plans = []
    for plan_id, plan_data in plans.items():
        formatted_plans.append({
            'id': plan_id,
            'name': plan_data['name'],
            'price': plan_data['price'],
            'limits': plan_data['limits'],
            'features': [
                f"{plan_data['limits']['experiments']} experiments" if plan_data['limits']['experiments'] != -1 else "Unlimited experiments",
                f"{plan_data['limits']['monthly_visitors']:,} monthly visitors" if plan_data['limits']['monthly_visitors'] != -1 else "Unlimited visitors",
                f"{plan_data['limits']['team_members']} team members" if plan_data['limits']['team_members'] != -1 else "Unlimited team members",
                f"{plan_data['limits']['data_retention_days']} days data retention" if plan_data['limits']['data_retention_days'] != -1 else "Unlimited data retention",
                "Advanced Analytics" if plan_data['limits']['enable_advanced_analytics'] else None,
                "Heatmaps" if plan_data['limits']['enable_heatmaps'] else None,
                "Advanced Targeting" if plan_data['limits']['enable_targeting'] else None,
                "API Access" if plan_data['limits']['enable_api_access'] else None,
            ],
            'support': plan_data['limits']['support'],
            'recommended': plan_id == 'professional'  # Highlight recommended plan
        })
    
    # Filter out None features
    for plan in formatted_plans:
        plan['features'] = [f for f in plan['features'] if f is not None]
    
    return {
        'plans': formatted_plans
    }

@app.get("/api/billing/subscription")
async def get_current_subscription(user_id: str = Depends(get_current_user)):
    """Obtener información de suscripción actual del usuario"""
    try:
        plan_info = await stripe_manager.get_user_plan_info(user_id)
        trial_info = await stripe_manager.check_trial_status(user_id)
        
        # Obtener usage actual
        experiments_usage = await stripe_manager.check_usage_limit(
            user_id, 'experiments'
        )
        
        api_calls_usage = await stripe_manager.check_usage_limit(
            user_id, 'api_calls_per_month'
        )
        
        return {
            'plan': plan_info,
            'trial': trial_info,
            'usage': {
                'experiments': experiments_usage,
                'api_calls': api_calls_usage
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscription information"
        )

@app.post("/api/billing/checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    user_id: str = Depends(get_current_user)
):
    """Crear sesión de checkout de Stripe"""
    try:
        # Validar plan
        try:
            plan = SubscriptionPlan(request.plan)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid plan"
            )
        
        # No permitir downgrade a FREE
        if plan == SubscriptionPlan.FREE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot checkout for free plan"
            )
        
        # URLs de success/cancel
        base_url = os.environ.get("BASE_URL", "http://localhost:8000")
        success_url = f"{base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{base_url}/settings/billing"
        
        # Crear sesión
        session = await stripe_manager.create_checkout_session(
            user_id=user_id,
            plan=plan,
            success_url=success_url,
            cancel_url=cancel_url,
            trial_days=request.trial_days
        )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )

@app.post("/api/billing/portal")
async def create_portal_session(
    request: PortalRequest,
    user_id: str = Depends(get_current_user)
):
    """Crear sesión del portal de cliente de Stripe"""
    try:
        session = await stripe_manager.create_portal_session(
            user_id=user_id,
            return_url=request.return_url
        )
        
        return session
        
    except Exception as e:
        logger.error(f"Failed to create portal session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portal session"
        )

@app.post("/api/billing/cancel")
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    user_id: str = Depends(get_current_user)
):
    """Cancelar suscripción"""
    try:
        success = await stripe_manager.cancel_subscription(
            user_id=user_id,
            immediate=request.immediate
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found"
            )
        
        return {
            "status": "success",
            "message": "Subscription canceled" if request.immediate else "Subscription will cancel at period end"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )

@app.get("/api/billing/invoices")
async def get_user_invoices(
    user_id: str = Depends(get_current_user),
    limit: int = 20
):
    """Obtener facturas del usuario"""
    try:
        invoices = await db.get_user_invoices(user_id, limit)
        return {"invoices": invoices}
        
    except Exception as e:
        logger.error(f"Failed to get invoices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get invoices"
        )

@app.get("/api/billing/payment-history")
async def get_payment_history(
    user_id: str = Depends(get_current_user),
    limit: int = 20
):
    """Obtener historial de pagos"""
    try:
        payments = await db.get_user_payment_history(user_id, limit)
        return {"payments": payments}
        
    except Exception as e:
        logger.error(f"Failed to get payment history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment history"
        )

# ===== WEBHOOKS =====

@app.post("/api/webhooks/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """Webhook de Stripe para eventos de pago"""
    try:
        payload = await request.body()
        
        # Verificar firma
        event = stripe_manager.verify_webhook_signature(payload, stripe_signature)
        
        # Procesar evento
        await stripe_manager.handle_webhook(event)
        
        return {"status": "success"}
        
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload"
        )
    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )

# ===== USAGE TRACKING =====

@app.get("/api/billing/usage")
async def get_usage_stats(user_id: str = Depends(get_current_user)):
    """Obtener estadísticas de uso"""
    try:
        experiments_usage = await stripe_manager.check_usage_limit(
            user_id, 'experiments'
        )
        
        monthly_visitors_usage = await stripe_manager.check_usage_limit(
            user_id, 'monthly_visitors'
        )
        
        api_calls_usage = await stripe_manager.check_usage_limit(
            user_id, 'api_calls_per_month'
        )
        
        team_members_usage = await stripe_manager.check_usage_limit(
            user_id, 'team_members'
        )
        
        return {
            'experiments': experiments_usage,
            'monthly_visitors': monthly_visitors_usage,
            'api_calls': api_calls_usage,
            'team_members': team_members_usage
        }
        
    except Exception as e:
        logger.error(f"Failed to get usage stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get usage stats"
        )

# ===== ADMIN ENDPOINTS =====

@app.get("/api/admin/billing/stats")
async def get_billing_stats(
    user_id: str = Depends(get_current_user)
):
    """Obtener estadísticas de billing (admin only)"""
    # TODO: Verificar que el usuario es admin
    
    try:
        subscription_stats = await db.get_subscription_stats()
        churn_data = await db.get_churn_data(days=30)
        
        return {
            'subscriptions': subscription_stats,
            'churn': churn_data
        }
        
    except Exception as e:
        logger.error(f"Failed to get billing stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get billing stats"
        )

# ===== MODIFICAR ENDPOINT DE CREAR EXPERIMENTO =====

# En el endpoint create_experiment existente, añadir verificación de límites:

@app.post("/api/experiments", response_model=CreateExperimentResponse)
async def create_experiment(
    request: CreateExperimentRequest,
    user_id: str = Depends(get_current_user),
    usage: Dict = Depends(check_experiment_limit)  # ← Añadir esto
):
    """
    Crear experimento - UNIFICADO (con verificación de límites)
    """
    try:
        # ... resto del código existente ...
        
        # Código de creación de experimento aquí
        result = await db.create_experiment(...)
        
        return CreateExperimentResponse(...)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Experiment creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Experiment creation failed: {str(e)}"
        )

# ===== MODIFICAR ENDPOINTS DE FASE 2 PARA VERIFICAR FEATURES =====

@app.post("/api/experiments/{experiment_id}/sessions")
async def create_session_analytics(
    experiment_id: str,
    request: SessionAnalyticsRequest,
    # Verificar acceso a analytics avanzadas (público, no requiere auth)
):
    """Crear sesión de analytics"""
    # ... código existente ...

@app.get("/api/experiments/{experiment_id}/analytics/advanced")
async def get_advanced_analytics(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    _: bool = Depends(lambda user_id=Depends(get_current_user): 
                     check_feature_access("advanced_analytics", user_id))  # ← Verificar feature
):
    """Obtener analytics avanzadas (requiere plan PRO+)"""
    # ... código existente ...

# ===== TASK PARA RESET MENSUAL DE USAGE =====

# Agregar a un cron job o scheduler
async def reset_monthly_usage_task():
    """
    Task para resetear usage mensual
    Ejecutar el día 1 de cada mes
    """
    try:
        # Obtener todos los usuarios con suscripción activa
        async with db.pool.acquire() as conn:
            users = await conn.fetch(
                "SELECT user_id FROM subscriptions WHERE status = 'active'"
            )
        
        for user in users:
            await db.reset_monthly_usage(user['user_id'])
        
        logger.info(f"Reset monthly usage for {len(users)} users")
        
    except Exception as e:
        logger.error(f"Failed to reset monthly usage: {str(e)}")
