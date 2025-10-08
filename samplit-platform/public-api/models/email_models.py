# public-api/models/email_models.py

"""
Modelos para Email A/B Testing
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

# ============================================
# ENUMS
# ============================================

class EmailPlatform(str, Enum):
    """Plataformas de email soportadas"""
    MAILGUN = "mailgun"
    SENDGRID = "sendgrid"
    AMAZON_SES = "amazon_ses"
    MOCK = "mock"  # Para testing sin envíos reales

class EmailElementType(str, Enum):
    """Tipos de elementos testables en email"""
    SUBJECT_LINE = "subject_line"
    PREHEADER = "preheader"
    FROM_NAME = "from_name"
    HEADLINE = "headline"
    BODY_TEXT = "body_text"
    CTA_BUTTON = "cta_button"
    IMAGE = "image"

# ============================================
# EMAIL VARIANT
# ============================================

class EmailVariant(BaseModel):
    """Variante de un elemento de email"""
    name: str = Field(..., description="Nombre de la variante")
    content: Dict[str, Any] = Field(..., description="Contenido de la variante")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Subject A",
                "content": {
                    "text": "Get 50% OFF Today! 🎉",
                    "emoji": True
                }
            }
        }

class EmailElement(BaseModel):
    """Elemento testeable en email"""
    element_type: EmailElementType
    name: str = Field(..., description="Nombre descriptivo")
    variants: List[EmailVariant] = Field(..., min_items=2)
    
    @validator('variants')
    def validate_variants(cls, v):
        if len(v) < 2:
            raise ValueError('Se necesitan al menos 2 variantes')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "element_type": "subject_line",
                "name": "Subject Line Test",
                "variants": [
                    {"name": "Control", "content": {"text": "Newsletter #42"}},
                    {"name": "Urgent", "content": {"text": "🔥 Last Chance - Don't Miss Out!"}},
                    {"name": "Question", "content": {"text": "Ready to 10x your results?"}}
                ]
            }
        }

# ============================================
# EMAIL CAMPAIGN
# ============================================

class CreateEmailCampaignRequest(BaseModel):
    """Crear campaña de email A/B testing"""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    
    # Configuración de email
    from_email: EmailStr
    from_name: str
    reply_to: Optional[EmailStr] = None
    
    # Elementos a testear
    elements: List[EmailElement] = Field(..., min_items=1)
    
    # Template HTML base
    template_html: str = Field(..., description="Template HTML con placeholders")
    
    # Plataforma de envío
    platform: EmailPlatform = EmailPlatform.MOCK
    
    # Configuración de test
    test_percentage: float = Field(default=0.1, ge=0.01, le=0.5)
    winner_criteria: str = Field(default="open_rate", regex="^(open_rate|click_rate|conversion_rate)$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Newsletter April Test",
                "description": "Testing subject lines for engagement",
                "from_email": "newsletter@company.com",
                "from_name": "Company Newsletter",
                "elements": [
                    {
                        "element_type": "subject_line",
                        "name": "Subject Test",
                        "variants": [
                            {"name": "Control", "content": {"text": "Monthly Update"}},
                            {"name": "Personalized", "content": {"text": "{{name}}, your update is here!"}}
                        ]
                    }
                ],
                "template_html": "<html><body><h1>{{headline}}</h1><p>{{body}}</p></body></html>",
                "platform": "mock"
            }
        }

# ============================================
# EMAIL SENDING
# ============================================

class EmailRecipient(BaseModel):
    """Destinatario de email"""
    email: EmailStr
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SendEmailCampaignRequest(BaseModel):
    """Enviar campaña de email"""
    campaign_id: str
    recipients: List[EmailRecipient] = Field(..., min_items=1)
    schedule_time: Optional[datetime] = None
    send_test_emails: bool = False
    test_recipients: Optional[List[EmailStr]] = None

# ============================================
# EMAIL TRACKING
# ============================================

class EmailInteractionType(str, Enum):
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    COMPLAINED = "complained"

class RecordEmailInteractionRequest(BaseModel):
    """Registrar interacción con email"""
    campaign_id: str
    recipient_email: EmailStr
    interaction_type: EmailInteractionType
    metadata: Optional[Dict[str, Any]] = None

# ============================================
# RESPONSES
# ============================================

class EmailCampaignResponse(BaseModel):
    """Respuesta de campaña creada"""
    campaign_id: str
    name: str
    status: str
    elements_count: int
    total_variants: int
    created_at: datetime

class EmailCampaignListResponse(BaseModel):
    """Lista de campañas"""
    id: str
    name: str
    status: str
    from_email: str
    created_at: datetime
    total_sent: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0

class EmailVariantPerformance(BaseModel):
    """Performance de variante de email"""
    variant_id: str
    variant_name: str
    element_type: EmailElementType
    content: Dict[str, Any]
    
    # Métricas
    sent_count: int = 0
    delivered_count: int = 0
    opened_count: int = 0
    clicked_count: int = 0
    bounced_count: int = 0
    unsubscribed_count: int = 0
    
    # Tasas
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    click_to_open_rate: float = 0.0

class EmailCampaignAnalytics(BaseModel):
    """Analytics de campaña de email"""
    campaign_id: str
    campaign_name: str
    status: str
    
    # Stats globales
    total_sent: int
    total_delivered: int
    total_opened: int
    total_clicked: int
    total_bounced: int
    total_unsubscribed: int
    
    # Tasas globales
    delivery_rate: float
    open_rate: float
    click_rate: float
    
    # Performance por variante
    variants: List[EmailVariantPerformance]
    
    # Ganador
    winner_variant_id: Optional[str] = None
    winner_confidence: Optional[float] = None
    
    # Recomendaciones
    recommendations: List[str] = []

class SendEmailResponse(BaseModel):
    """Respuesta de envío de email"""
    send_id: str
    campaign_id: str
    total_queued: int
    status: str
    estimated_delivery_time_minutes: int
    mock: bool = False  # True si es mock
