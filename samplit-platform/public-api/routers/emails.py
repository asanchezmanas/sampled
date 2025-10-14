# public-api/routers/emails.py

"""
Email Optimization API - IMPLEMENTACIÓN COMPLETA

Tres métodos de instalación:
1. OAuth (Mailchimp, SendGrid, Klaviyo) - SIN CÓDIGO
2. API Manual - Para desarrolladores
3. Webhook - Para integraciones custom
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

from public_api.routers.auth import get_current_user
from data_access.database import get_database, DatabaseManager
from orchestration.services.email_oauth_service import EmailOAuthService

router = APIRouter()

# ============================================
# MODELS
# ============================================

class ConnectEmailPlatformRequest(BaseModel):
    """Request para conectar plataforma via OAuth"""
    platform: str  # mailchimp, sendgrid, klaviyo
    redirect_uri: str

class EmailElementRequest(BaseModel):
    """Elemento de email a testear"""
    element_type: str  # subject_line, headline, cta_button
    name: str
    variants: List[Dict[str, Any]]

class CreateEmailCampaignRequest(BaseModel):
    """Crear campaña de email"""
    name: str
    from_email: EmailStr
    from_name: str
    reply_to: Optional[EmailStr] = None
    platform: str
    template_html: str
    elements: List[EmailElementRequest]

class SendEmailRequest(BaseModel):
    """Enviar campaña"""
    campaign_id: str
    recipients: List[Dict[str, str]]  # [{'email': 'user@x.com', 'name': 'User'}]

# ============================================
# OAUTH INTEGRATION
# ============================================

@router.post("/integrations/connect")
async def connect_email_platform(
    request: ConnectEmailPlatformRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Paso 1 de OAuth: Obtener URL de autorización
    
    El frontend redirige al usuario a esta URL.
    """
    
    service = EmailOAuthService(db)
    
    try:
        oauth_url = await service.get_oauth_url(
            platform=request.platform,
            user_id=user_id,
            redirect_uri=request.redirect_uri
        )
        
        return {
            'oauth_url': oauth_url,
            'platform': request.platform
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate OAuth URL: {str(e)}"
        )

@router.get("/integrations/callback")
async def oauth_callback(
    platform: str = Query(...),
    code: str = Query(...),
    state: str = Query(...),
    db: DatabaseManager = Depends(get_database)
):
    """
    Paso 2 de OAuth: Callback
    
    El ESP redirige aquí después de que el usuario autoriza.
    Este endpoint NO requiere auth (es callback público).
    """
    
    service = EmailOAuthService(db)
    
    try:
        result = await service.handle_oauth_callback(
            platform=platform,
            code=code,
            state=state
        )
        
        # Redirigir al frontend con éxito
        return {
            'status': 'success',
            'message': f'{platform.title()} connected successfully',
            'redirect': f'/settings/integrations?connected={platform}'
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth callback failed: {str(e)}"
        )

@router.get("/integrations")
async def list_email_integrations(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Listar integraciones de email conectadas"""
    
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT platform, status, created_at, updated_at
            FROM email_integrations
            WHERE user_id = $1
            """,
            user_id
        )
    
    return {
        'integrations': [dict(row) for row in rows]
    }

@router.delete("/integrations/{platform}")
async def disconnect_email_platform(
    platform: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Desconectar plataforma de email"""
    
    async with db.pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE email_integrations
            SET status = 'inactive', updated_at = NOW()
            WHERE user_id = $1 AND platform = $2
            """,
            user_id, platform
        )
    
    if result == "UPDATE 0":
        raise HTTPException(404, "Integration not found")
    
    return {'status': 'disconnected', 'platform': platform}

# ============================================
# CAMPAIGNS
# ============================================

@router.post("/campaigns", status_code=201)
async def create_email_campaign(
    request: CreateEmailCampaignRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Crear campaña de email con optimización
    
    El usuario define:
    - Template HTML con placeholders
    - Elementos a testear (subject, headline, CTA)
    - Variantes de cada elemento
    
    Samplit se encarga del resto.
    """
    
    try:
        # Verificar que tenga integración
        async with db.pool.acquire() as conn:
            integration = await conn.fetchrow(
                """
                SELECT * FROM email_integrations
                WHERE user_id = $1 AND platform = $2 AND status = 'active'
                """,
                user_id, request.platform
            )
        
        if not integration:
            raise HTTPException(
                status_code=400,
                detail=f"No active {request.platform} integration. Connect first."
            )
        
        # Crear campaña
        async with db.pool.acquire() as conn:
            campaign_id = await conn.fetchval(
                """
                INSERT INTO email_campaigns (
                    user_id, name, from_email, from_name, reply_to,
                    platform, template_html, status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'draft')
                RETURNING id
                """,
                user_id, request.name, request.from_email, request.from_name,
                request.reply_to, request.platform, request.template_html
            )
            
            # Crear elementos y variantes
            for element in request.elements:
                element_id = await conn.fetchval(
                    """
                    INSERT INTO email_elements (
                        campaign_id, element_type, name
                    ) VALUES ($1, $2, $3)
                    RETURNING id
                    """,
                    campaign_id, element.element_type, element.name
                )
                
                for variant in element.variants:
                    await conn.execute(
                        """
                        INSERT INTO email_variants (
                            element_id, name, content
                        ) VALUES ($1, $2, $3)
                        """,
                        element_id,
                        variant.get('name', 'Variant'),
                        variant  # JSONB
                    )
        
        return {
            'campaign_id': str(campaign_id),
            'status': 'draft',
            'message': 'Campaign created. Ready to send.'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create campaign: {str(e)}"
        )

@router.get("/campaigns")
async def list_email_campaigns(
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """Listar campañas de email"""
    
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT 
                ec.*,
                COUNT(DISTINCT es.id) as total_sends,
                COUNT(DISTINCT es.id) FILTER (WHERE es.opened_at IS NOT NULL) as opens,
                COUNT(DISTINCT es.id) FILTER (WHERE es.clicked_at IS NOT NULL) as clicks
            FROM email_campaigns ec
            LEFT JOIN email_sends es ON ec.id = es.campaign_id
            WHERE ec.user_id = $1 AND ec.status != 'archived'
            GROUP BY ec.id
            ORDER BY ec.created_at DESC
            """,
            user_id
        )
    
    campaigns = []
    for row in rows:
        data = dict(row)
        
        # Calculate rates
        total = data['total_sends'] or 1
        data['open_rate'] = (data['opens'] or 0) / total
        data['click_rate'] = (data['clicks'] or 0) / total
        
        campaigns.append(data)
    
    return {'campaigns': campaigns}

@router.post("/campaigns/send")
async def send_email_campaign(
    request: SendEmailRequest,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Enviar campaña de email
    
    Samplit:
    1. Por cada recipient, decide qué variantes usar (Thompson Sampling)
    2. Construye el email con esas variantes
    3. Lo envía via API del ESP
    4. Registra para tracking
    
    TODO AUTOMÁTICO.
    """
    
    service = EmailOAuthService(db)
    
    try:
        # Verificar ownership
        async with db.pool.acquire() as conn:
            campaign = await conn.fetchrow(
                """
                SELECT * FROM email_campaigns
                WHERE id = $1 AND user_id = $2
                """,
                request.campaign_id, user_id
            )
        
        if not campaign:
            raise HTTPException(404, "Campaign not found")
        
        # Enviar
        result = await service.send_campaign(
            campaign_id=request.campaign_id,
            recipients=request.recipients
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send campaign: {str(e)}"
        )

# ============================================
# ANALYTICS
# ============================================

@router.get("/campaigns/{campaign_id}/analytics")
async def get_email_campaign_analytics(
    campaign_id: str,
    user_id: str = Depends(get_current_user),
    db: DatabaseManager = Depends(get_database)
):
    """
    Analytics de campaña con insights de Thompson Sampling
    
    Muestra qué variantes están ganando.
    """
    
    async with db.pool.acquire() as conn:
        # Verify ownership
        campaign = await conn.fetchrow(
            "SELECT * FROM email_campaigns WHERE id = $1 AND user_id = $2",
            campaign_id, user_id
        )
        
        if not campaign:
            raise HTTPException(404, "Campaign not found")
        
        # Stats globales
        stats = await conn.fetchrow(
            """
            SELECT 
                COUNT(*) as total_sends,
                COUNT(*) FILTER (WHERE opened_at IS NOT NULL) as opens,
                COUNT(*) FILTER (WHERE clicked_at IS NOT NULL) as clicks,
                COUNT(*) FILTER (WHERE bounced_at IS NOT NULL) as bounces
            FROM email_sends
            WHERE campaign_id = $1
            """,
            campaign_id
        )
        
        # Performance por variante
        variant_stats = await conn.fetch(
            """
            SELECT 
                ev.id, ev.name, ee.element_type,
                COUNT(es.id) as sends,
                COUNT(es.id) FILTER (WHERE es.opened_at IS NOT NULL) as opens,
                COUNT(es.id) FILTER (WHERE es.clicked_at IS NOT NULL) as clicks,
                CASE 
                    WHEN COUNT(es.id) > 0 
                    THEN COUNT(es.id) FILTER (WHERE es.opened_at IS NOT NULL)::FLOAT / 
                         COUNT(es.id)::FLOAT
                    ELSE 0
                END as open_rate
            FROM email_variants ev
            JOIN email_elements ee ON ev.element_id = ee.id
            LEFT JOIN email_sends es ON ev.id = es.variant_id
            WHERE ee.campaign_id = $1
            GROUP BY ev.id, ev.name, ee.element_type
            ORDER BY open_rate DESC
            """,
            campaign_id
        )
    
    total = stats['total_sends'] or 1
    
    return {
        'campaign_id': campaign_id,
        'campaign_name': campaign['name'],
        'total_sends': stats['total_sends'],
        'open_rate': (stats['opens'] or 0) / total,
        'click_rate': (stats['clicks'] or 0) / total,
        'bounce_rate': (stats['bounces'] or 0) / total,
        'variants': [dict(row) for row in variant_stats],
        'recommendations': _generate_email_recommendations(stats, variant_stats)
    }

# ============================================
# TRACKING (PÚBLICO)
# ============================================

@router.get("/track/open/{send_id}")
async def track_email_open(
    send_id: str,
    db: DatabaseManager = Depends(get_database)
):
    """
    Tracking pixel para opens
    
    Endpoint público - se inserta como imagen en el email:
    <img src="https://api.samplit.com/emails/track/open/{send_id}" width="1" height="1" />
    """
    
    service = EmailOAuthService(db)
    await service.track_open(send_id)
    
    # Retornar pixel transparente
    from fastapi.responses import Response
    pixel = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    return Response(content=pixel, media_type="image/png")

@router.get("/track/click/{send_id}")
async def track_email_click(
    send_id: str,
    url: str = Query(...),
    db: DatabaseManager = Depends(get_database)
):
    """
    Click tracking redirect
    
    Los links en el email apuntan a:
    https://api.samplit.com/emails/track/click/{send_id}?url=https://destino.com
    
    Este endpoint registra el click y redirige.
    """
    
    service = EmailOAuthService(db)
    await service.track_click(send_id)
    
    # Redirigir a URL original
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=url)

# ============================================
# HELPERS
# ============================================

def _generate_email_recommendations(stats: Dict, variants: List) -> List[str]:
    """Generar recomendaciones basadas en performance"""
    
    recommendations = []
    
    total = stats['total_sends'] or 1
    open_rate = (stats['opens'] or 0) / total
    
    if open_rate < 0.15:
        recommendations.append(
            "⚠️ Low open rate (<15%). Try testing more compelling subject lines."
        )
    
    if open_rate > 0.25:
        recommendations.append(
            "🎉 Great open rate (>25%)! Your subject lines are working well."
        )
    
    # Encontrar best performer
    if variants:
        best = max(variants, key=lambda v: v['open_rate'])
        if best['sends'] > 50 and best['open_rate'] > 0.2:
            recommendations.append(
                f"🏆 Winner: '{best['name']}' with {best['open_rate']:.1%} open rate"
            )
    
    return recommendations
