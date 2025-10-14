# orchestration/services/email_oauth_service.py

"""
Email OAuth Integration Service

Maneja OAuth con plataformas de email populares y envío de campañas.
El usuario NO necesita código - todo via UI.
"""

import aiohttp
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from data_access.database import DatabaseManager
from engine.state.encryption import get_encryptor
from orchestration.factories.optimizer_factory import OptimizerFactory
from orchestration.interfaces.optimization_interface import OptimizationStrategy

logger = logging.getLogger(__name__)

class EmailOAuthService:
    """
    Servicio para integración OAuth con ESPs
    
    Soporta:
    - Mailchimp
    - SendGrid
    - Klaviyo
    - Brevo
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.encryptor = get_encryptor()
        self.optimizer = OptimizerFactory.create(OptimizationStrategy.ADAPTIVE)
    
    # ============================================
    # OAUTH FLOW
    # ============================================
    
    async def get_oauth_url(self, platform: str, user_id: str, redirect_uri: str) -> str:
        """
        Generar URL de OAuth para plataforma
        
        Args:
            platform: 'mailchimp', 'sendgrid', 'klaviyo'
            user_id: ID del usuario
            redirect_uri: URL de callback
        """
        
        # Estado para verificar callback
        import secrets
        state = secrets.token_urlsafe(32)
        
        # Guardar state temporalmente
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO oauth_states (state, user_id, platform, redirect_uri, expires_at)
                VALUES ($1, $2, $3, $4, NOW() + INTERVAL '10 minutes')
                """,
                state, user_id, platform, redirect_uri
            )
        
        # URLs de OAuth según plataforma
        oauth_configs = {
            'mailchimp': {
                'auth_url': 'https://login.mailchimp.com/oauth2/authorize',
                'client_id': 'YOUR_MAILCHIMP_CLIENT_ID',
                'scope': 'campaigns:read campaigns:write'
            },
            'sendgrid': {
                'auth_url': 'https://api.sendgrid.com/oauth/authorize',
                'client_id': 'YOUR_SENDGRID_CLIENT_ID',
                'scope': 'mail.send marketing.read marketing.write'
            },
            'klaviyo': {
                'auth_url': 'https://www.klaviyo.com/oauth/authorize',
                'client_id': 'YOUR_KLAVIYO_CLIENT_ID',
                'scope': 'campaigns:read campaigns:write lists:read'
            }
        }
        
        config = oauth_configs.get(platform)
        if not config:
            raise ValueError(f"Platform {platform} not supported")
        
        # Construir URL
        params = {
            'client_id': config['client_id'],
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': config['scope'],
            'state': state
        }
        
        from urllib.parse import urlencode
        oauth_url = f"{config['auth_url']}?{urlencode(params)}"
        
        return oauth_url
    
    async def handle_oauth_callback(
        self, 
        platform: str, 
        code: str, 
        state: str
    ) -> Dict[str, Any]:
        """
        Procesar callback de OAuth
        
        Intercambia code por access token y lo guarda cifrado.
        """
        
        # Verificar state
        async with self.db.pool.acquire() as conn:
            oauth_state = await conn.fetchrow(
                """
                SELECT * FROM oauth_states 
                WHERE state = $1 AND platform = $2 AND expires_at > NOW()
                """,
                state, platform
            )
        
        if not oauth_state:
            raise ValueError("Invalid or expired OAuth state")
        
        user_id = oauth_state['user_id']
        
        # Intercambiar code por token
        token_data = await self._exchange_code_for_token(platform, code)
        
        # Guardar credenciales cifradas
        encrypted_creds = self.encryptor.encrypt_state({
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token'),
            'expires_at': token_data.get('expires_at'),
            'platform_data': token_data.get('metadata', {})
        })
        
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO email_integrations (user_id, platform, credentials, status)
                VALUES ($1, $2, $3, 'active')
                ON CONFLICT (user_id, platform) 
                DO UPDATE SET credentials = $3, status = 'active', updated_at = NOW()
                """,
                user_id, platform, encrypted_creds
            )
            
            # Limpiar state usado
            await conn.execute(
                "DELETE FROM oauth_states WHERE state = $1",
                state
            )
        
        logger.info(f"OAuth connected: {platform} for user {user_id}")
        
        return {
            'status': 'connected',
            'platform': platform,
            'user_id': user_id
        }
    
    async def _exchange_code_for_token(self, platform: str, code: str) -> Dict[str, Any]:
        """Intercambiar authorization code por access token"""
        
        token_endpoints = {
            'mailchimp': 'https://login.mailchimp.com/oauth2/token',
            'sendgrid': 'https://api.sendgrid.com/oauth/token',
            'klaviyo': 'https://www.klaviyo.com/oauth/token'
        }
        
        endpoint = token_endpoints.get(platform)
        if not endpoint:
            raise ValueError(f"Platform {platform} not supported")
        
        # Credenciales de app (desde env)
        import os
        client_id = os.getenv(f'{platform.upper()}_CLIENT_ID')
        client_secret = os.getenv(f'{platform.upper()}_CLIENT_SECRET')
        redirect_uri = os.getenv('EMAIL_OAUTH_REDIRECT_URI')
        
        async with aiohttp.ClientSession() as session:
            data = {
                'grant_type': 'authorization_code',
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
                'redirect_uri': redirect_uri
            }
            
            async with session.post(endpoint, data=data) as response:
                if response.status != 200:
                    error = await response.text()
                    raise Exception(f"OAuth token exchange failed: {error}")
                
                result = await response.json()
                
                return {
                    'access_token': result['access_token'],
                    'refresh_token': result.get('refresh_token'),
                    'expires_at': result.get('expires_in'),
                    'metadata': result.get('metadata', {})
                }
    
    # ============================================
    # ENVÍO DE CAMPAÑAS
    # ============================================
    
    async def send_campaign(
        self, 
        campaign_id: str, 
        recipients: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Enviar campaña de email con optimización
        
        Flujo:
        1. Por cada recipient, decide qué variante usar (Thompson Sampling)
        2. Inyecta contenido de la variante
        3. Envía via API del ESP
        4. Registra envío para tracking
        
        Args:
            campaign_id: ID de la campaña
            recipients: Lista de {'email': 'user@example.com', 'name': 'User'}
        """
        
        # Obtener campaña
        async with self.db.pool.acquire() as conn:
            campaign = await conn.fetchrow(
                "SELECT * FROM email_campaigns WHERE id = $1",
                campaign_id
            )
        
        if not campaign or campaign['status'] != 'active':
            raise ValueError("Campaign not found or not active")
        
        user_id = campaign['user_id']
        platform = campaign['platform']
        
        # Obtener credenciales
        credentials = await self._get_credentials(user_id, platform)
        
        # Obtener elementos y variantes
        elements = await self._get_campaign_elements(campaign_id)
        
        # Enviar a cada recipient
        send_results = []
        
        for recipient in recipients:
            try:
                # Decidir variantes (Thompson Sampling)
                selected_variants = await self._select_variants_for_recipient(
                    elements, 
                    recipient
                )
                
                # Construir email con variantes seleccionadas
                email_content = await self._build_email(
                    campaign=campaign,
                    variants=selected_variants,
                    recipient=recipient
                )
                
                # Enviar via ESP
                send_result = await self._send_via_esp(
                    platform=platform,
                    credentials=credentials,
                    email_content=email_content,
                    recipient=recipient
                )
                
                # Registrar envío
                await self._record_send(
                    campaign_id=campaign_id,
                    recipient=recipient,
                    selected_variants=selected_variants,
                    send_result=send_result
                )
                
                send_results.append({
                    'email': recipient['email'],
                    'status': 'sent',
                    'variants': selected_variants
                })
                
            except Exception as e:
                logger.error(f"Failed to send to {recipient['email']}: {e}")
                send_results.append({
                    'email': recipient['email'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        return {
            'campaign_id': campaign_id,
            'total': len(recipients),
            'sent': sum(1 for r in send_results if r['status'] == 'sent'),
            'failed': sum(1 for r in send_results if r['status'] == 'failed'),
            'results': send_results
        }
    
    async def _select_variants_for_recipient(
        self, 
        elements: List[Dict], 
        recipient: Dict
    ) -> Dict[str, str]:
        """
        Decidir qué variante usar para cada elemento
        
        Usa Thompson Sampling para optimizar.
        """
        
        selected = {}
        
        for element in elements:
            # Preparar opciones para el optimizer
            options = []
            for variant in element['variants']:
                options.append({
                    'id': variant['id'],
                    'content': variant['content'],
                    'performance': await self._get_variant_performance(variant['id'])
                })
            
            # Seleccionar usando optimizer (Thompson Sampling)
            context = {
                'recipient_email': recipient['email'],
                'element_id': element['id']
            }
            
            selected_id = await self.optimizer.select(options, context)
            
            selected[element['element_type']] = selected_id
        
        return selected
    
    async def _build_email(
        self, 
        campaign: Dict, 
        variants: Dict[str, str], 
        recipient: Dict
    ) -> Dict[str, Any]:
        """
        Construir email con las variantes seleccionadas
        
        Reemplaza placeholders en el template HTML.
        """
        
        template = campaign['template_html']
        
        # Obtener contenido de cada variante seleccionada
        async with self.db.pool.acquire() as conn:
            for element_type, variant_id in variants.items():
                variant = await conn.fetchrow(
                    "SELECT content FROM email_variants WHERE id = $1",
                    variant_id
                )
                
                if variant:
                    content = variant['content']
                    
                    # Reemplazar en template
                    if element_type == 'subject_line':
                        subject = content.get('text', '')
                    elif element_type == 'headline':
                        template = template.replace(
                            '{{headline}}', 
                            content.get('text', '')
                        )
                    elif element_type == 'cta_button':
                        template = template.replace(
                            '{{cta_text}}', 
                            content.get('text', '')
                        )
                        template = template.replace(
                            '{{cta_url}}', 
                            content.get('url', '')
                        )
        
        # Personalización con datos del recipient
        template = template.replace('{{name}}', recipient.get('name', 'there'))
        template = template.replace('{{email}}', recipient['email'])
        
        return {
            'subject': subject,
            'html': template,
            'from_email': campaign['from_email'],
            'from_name': campaign['from_name'],
            'reply_to': campaign.get('reply_to')
        }
    
    async def _send_via_esp(
        self, 
        platform: str, 
        credentials: Dict, 
        email_content: Dict, 
        recipient: Dict
    ) -> Dict[str, Any]:
        """
        Enviar email via API del ESP
        
        Implementación específica por plataforma.
        """
        
        if platform == 'mailchimp':
            return await self._send_mailchimp(credentials, email_content, recipient)
        elif platform == 'sendgrid':
            return await self._send_sendgrid(credentials, email_content, recipient)
        elif platform == 'klaviyo':
            return await self._send_klaviyo(credentials, email_content, recipient)
        else:
            raise ValueError(f"Platform {platform} not supported")
    
    async def _send_mailchimp(
        self, 
        credentials: Dict, 
        email: Dict, 
        recipient: Dict
    ) -> Dict[str, Any]:
        """Enviar via Mailchimp API"""
        
        async with aiohttp.ClientSession() as session:
            # Mailchimp API v3
            dc = credentials['platform_data'].get('dc', 'us1')
            url = f"https://{dc}.api.mailchimp.com/3.0/campaigns"
            
            headers = {
                'Authorization': f"Bearer {credentials['access_token']}",
                'Content-Type': 'application/json'
            }
            
            # Crear campaña
            campaign_data = {
                'type': 'regular',
                'recipients': {
                    'list_id': credentials['platform_data'].get('list_id')
                },
                'settings': {
                    'subject_line': email['subject'],
                    'from_name': email['from_name'],
                    'reply_to': email['reply_to'] or email['from_email']
                }
            }
            
            async with session.post(url, json=campaign_data, headers=headers) as response:
                result = await response.json()
                campaign_id = result['id']
            
            # Set content
            content_url = f"{url}/{campaign_id}/content"
            content_data = {'html': email['html']}
            
            async with session.put(content_url, json=content_data, headers=headers) as response:
                await response.json()
            
            # Send
            send_url = f"{url}/{campaign_id}/actions/send"
            async with session.post(send_url, headers=headers) as response:
                result = await response.json()
            
            return {
                'message_id': campaign_id,
                'status': 'sent'
            }
    
    async def _send_sendgrid(
        self, 
        credentials: Dict, 
        email: Dict, 
        recipient: Dict
    ) -> Dict[str, Any]:
        """Enviar via SendGrid API"""
        
        async with aiohttp.ClientSession() as session:
            url = "https://api.sendgrid.com/v3/mail/send"
            
            headers = {
                'Authorization': f"Bearer {credentials['access_token']}",
                'Content-Type': 'application/json'
            }
            
            data = {
                'personalizations': [{
                    'to': [{'email': recipient['email'], 'name': recipient.get('name')}]
                }],
                'from': {
                    'email': email['from_email'],
                    'name': email['from_name']
                },
                'subject': email['subject'],
                'content': [{
                    'type': 'text/html',
                    'value': email['html']
                }]
            }
            
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 202:
                    return {'status': 'sent'}
                else:
                    error = await response.text()
                    raise Exception(f"SendGrid error: {error}")
    
    # ============================================
    # TRACKING
    # ============================================
    
    async def _record_send(
        self, 
        campaign_id: str, 
        recipient: Dict, 
        selected_variants: Dict, 
        send_result: Dict
    ):
        """Registrar envío para tracking"""
        
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO email_sends (
                    campaign_id, recipient_email, recipient_name,
                    variant_selections, status, message_id
                ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                campaign_id,
                recipient['email'],
                recipient.get('name'),
                selected_variants,  # JSONB
                send_result.get('status', 'sent'),
                send_result.get('message_id')
            )
    
    async def track_open(self, send_id: str):
        """Registrar que se abrió el email"""
        
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE email_sends 
                SET opened_at = NOW()
                WHERE id = $1 AND opened_at IS NULL
                """,
                send_id
            )
            
            # Actualizar optimizer (reward = 0.3 por open)
            send = await conn.fetchrow(
                "SELECT * FROM email_sends WHERE id = $1",
                send_id
            )
            
            if send:
                await self.optimizer.update(
                    option_id=send['variant_id'],
                    reward=0.3,
                    context={'event': 'open'}
                )
    
    async def track_click(self, send_id: str):
        """Registrar click en email"""
        
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE email_sends 
                SET clicked_at = NOW()
                WHERE id = $1 AND clicked_at IS NULL
                """,
                send_id
            )
            
            send = await conn.fetchrow(
                "SELECT * FROM email_sends WHERE id = $1",
                send_id
            )
            
            if send:
                await self.optimizer.update(
                    option_id=send['variant_id'],
                    reward=0.7,
                    context={'event': 'click'}
                )
    
    # ============================================
    # HELPERS
    # ============================================
    
    async def _get_credentials(self, user_id: str, platform: str) -> Dict:
        """Obtener credenciales descifradas"""
        
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT credentials FROM email_integrations
                WHERE user_id = $1 AND platform = $2 AND status = 'active'
                """,
                user_id, platform
            )
        
        if not row:
            raise ValueError(f"No {platform} integration found")
        
        return self.encryptor.decrypt_state(row['credentials'])
    
    async def _get_campaign_elements(self, campaign_id: str) -> List[Dict]:
        """Obtener elementos y variantes de campaña"""
        
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    ee.id, ee.element_type, ee.name,
                    json_agg(
                        json_build_object(
                            'id', ev.id,
                            'name', ev.name,
                            'content', ev.content
                        )
                    ) as variants
                FROM email_elements ee
                JOIN email_variants ev ON ee.id = ev.element_id
                WHERE ee.campaign_id = $1
                GROUP BY ee.id
                """,
                campaign_id
            )
        
        return [dict(row) for row in rows]
    
    async def _get_variant_performance(self, variant_id: str) -> float:
        """Obtener performance de variante (para optimizer)"""
        
        async with self.db.pool.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as sends,
                    COUNT(*) FILTER (WHERE opened_at IS NOT NULL) as opens,
                    COUNT(*) FILTER (WHERE clicked_at IS NOT NULL) as clicks
                FROM email_sends
                WHERE variant_id = $1
                """,
                variant_id
            )
        
        if not stats or stats['sends'] == 0:
            return 0.0
        
        # Performance = weighted score
        open_rate = stats['opens'] / stats['sends']
        click_rate = stats['clicks'] / stats['sends']
        
        return (open_rate * 0.4) + (click_rate * 0.6)
