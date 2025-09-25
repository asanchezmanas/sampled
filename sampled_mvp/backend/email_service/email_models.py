# backend/email_models.py
"""
Email A/B Testing Models - Extensión sin breaking changes
Se integra perfectamente con models_extended.py existente
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import re

# Importar modelos base existentes (sin modificar)
from models_extended import (
    ElementConfig, TargetingConfig, VariantContent, 
    ExperimentConfigExtended, ElementStability
)

# ===== EMAIL-SPECIFIC ENUMS =====

class EmailElementType(str, Enum):
    """Tipos de elementos testeable en emails"""
    SUBJECT_LINE = "subject_line"
    PREHEADER = "preheader"  
    SENDER_NAME = "sender_name"
    HEADLINE = "headline"
    SUBHEADLINE = "subheadline"
    BODY_TEXT = "body_text"
    CTA_BUTTON = "cta_button"
    CTA_TEXT = "cta_text"
    IMAGE = "image"
    IMAGE_ALT = "image_alt"
    FOOTER_TEXT = "footer_text"
    PERSONALIZATION = "personalization"

class EmailPlatform(str, Enum):
    """Plataformas de email soportadas"""
    MAILGUN = "mailgun"
    SENDGRID = "sendgrid"
    AMAZON_SES = "amazon_ses"
    MAILCHIMP = "mailchimp"
    CUSTOM_SMTP = "custom_smtp"

class EmailClient(str, Enum):
    """Email clients para testing"""
    GMAIL_WEB = "gmail_web"
    GMAIL_MOBILE = "gmail_mobile"
    OUTLOOK_DESKTOP = "outlook_desktop"
    OUTLOOK_WEB = "outlook_web"
    APPLE_MAIL = "apple_mail"
    YAHOO_MAIL = "yahoo_mail"
    THUNDERBIRD = "thunderbird"

class WinnerCriteria(str, Enum):
    """Criterios para seleccionar ganador"""
    OPEN_RATE = "open_rate"
    CLICK_RATE = "click_rate"
    CONVERSION_RATE = "conversion_rate"
    REVENUE_PER_EMAIL = "revenue_per_email"
    ENGAGEMENT_SCORE = "engagement_score"

# ===== EMAIL TARGETING =====

class EmailSegment(BaseModel):
    """Segmento de email específico"""
    segment_id: str
    name: str
    description: Optional[str] = None
    size: int = 0
    criteria: Dict[str, Any] = Field(default_factory=dict)

class EmailTargeting(BaseModel):
    """Targeting específico para emails - EXTIENDE TargetingConfig base"""
    # Reutilizar targeting base
    base_targeting: TargetingConfig = Field(default_factory=TargetingConfig)
    
    # Email-specific targeting
    email_segments: List[EmailSegment] = Field(default_factory=list)
    engagement_level: Optional[str] = Field(None, regex=r'^(high|medium|low|new)$')
    last_open_days: Optional[int] = Field(None, ge=0, le=365)
    last_click_days: Optional[int] = Field(None, ge=0, le=365)
    purchase_history: Optional[str] = Field(None, regex=r'^(buyer|prospect|customer|churned)$')
    email_client: Optional[EmailClient] = None
    list_source: List[str] = Field(default_factory=list)
    
    # Advanced targeting
    domain_filters: List[str] = Field(default_factory=list)  # gmail.com, company.com
    exclude_domains: List[str] = Field(default_factory=list)
    subscriber_age_days: Optional[int] = Field(None, ge=0)
    lifetime_value_min: Optional[float] = Field(None, ge=0)
    
    @validator('engagement_level')
    def validate_engagement(cls, v):
        if v and v not in ['high', 'medium', 'low', 'new']:
            raise ValueError('Invalid engagement level')
        return v

# ===== EMAIL ELEMENTS =====

class EmailSelector(BaseModel):
    """Selector específico para elementos de email"""
    token: str  # ej: "{{subject_line}}", "{{cta_button_1}}"
    html_selector: Optional[str] = None  # ej: ".cta-button", "#headline"
    placeholder_pattern: str  # Patrón para encontrar en template
    
    @validator('token')
    def validate_token_format(cls, v):
        if not re.match(r'^\{\{[a-zA-Z0-9_]+\}\}$', v):
            raise ValueError('Token must be in format {{token_name}}')
        return v

class EmailVariant(BaseModel):
    """Variante específica para email - EXTIENDE VariantContent"""
    # Reutilizar VariantContent base
    base_content: VariantContent
    
    # Email-specific properties
    affects_deliverability: bool = False
    spam_risk_score: int = Field(0, ge=0, le=10)
    character_count: Optional[int] = None
    personalization_tokens: List[str] = Field(default_factory=list)
    
    # Validation for email content
    preview_text: Optional[str] = None  # Para preheader
    fallback_text: Optional[str] = None  # Para clientes que no soportan HTML
    
    @validator('spam_risk_score')
    def validate_spam_risk(cls, v):
        return min(max(v, 0), 10)

class EmailElementConfig(BaseModel):
    """Configuración de elemento de email - EXTIENDE ElementConfig base"""
    # Usar ElementConfig como base pero adaptado para email
    element_id: str = Field(..., min_length=1)
    email_element_type: EmailElementType
    selector: EmailSelector
    original_content: Dict[str, Any]
    variants: List[EmailVariant] = Field(..., min_items=1)
    
    # Email-specific properties
    priority: int = Field(5, ge=1, le=10)  # Prioridad para testing
    testing_impact: str = Field("medium", regex=r'^(low|medium|high|critical)$')
    client_compatibility: List[EmailClient] = Field(default_factory=list)
    
    # Content analysis
    readability_score: Optional[float] = Field(None, ge=0, le=100)
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1)
    
    @validator('variants')
    def validate_email_variants(cls, v):
        if len(v) == 0:
            raise ValueError('At least one variant required')
        return v

# ===== EMAIL EXPERIMENT CONFIG =====

class EmailSendSchedule(BaseModel):
    """Programación de envío de email"""
    send_immediately: bool = False
    scheduled_time: Optional[datetime] = None
    timezone: str = "UTC"
    
    # Advanced scheduling
    optimal_send_time: bool = False  # AI-optimized send time
    test_duration_hours: int = Field(24, ge=1, le=168)  # Duración del test
    winner_send_delay_hours: int = Field(2, ge=1, le=48)  # Delay antes de enviar ganador
    
    @validator('scheduled_time')
    def validate_schedule_time(cls, v, values):
        if v and not values.get('send_immediately', True):
            if v <= datetime.utcnow():
                raise ValueError('Scheduled time must be in the future')
        return v

class EmailExperimentConfig(BaseModel):
    """Configuración completa de experimento de email"""
    # Información base del experimento
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Template y elementos
    email_template: str = Field(..., min_length=10)  # HTML del email
    elements: List[EmailElementConfig] = Field(..., min_items=1, max_items=10)
    
    # Targeting y segmentación  
    targeting: EmailTargeting = Field(default_factory=EmailTargeting)
    
    # Configuración de envío
    send_schedule: EmailSendSchedule = Field(default_factory=EmailSendSchedule)
    test_percentage: float = Field(0.1, ge=0.01, le=0.5)  # % para A/B test
    minimum_test_size: int = Field(100, ge=50)
    
    # Criterios de éxito
    winner_criteria: WinnerCriteria = WinnerCriteria.OPEN_RATE
    confidence_threshold: float = Field(0.95, ge=0.8, le=0.99)
    auto_send_winner: bool = False
    
    # Platform settings
    email_platform: EmailPlatform = EmailPlatform.MAILGUN
    sender_email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    sender_name: str = Field(..., min_length=1, max_length=100)
    reply_to: Optional[str] = Field(None, regex=r'^[^@]+@[^@]+\.[^@]+$')
    
    # Advanced settings
    tracking_domain: Optional[str] = None
    custom_headers: Dict[str, str] = Field(default_factory=dict)
    suppress_lists: List[str] = Field(default_factory=list)
    unsubscribe_url: Optional[str] = None
    
    @validator('email_template')
    def validate_html_template(cls, v):
        # Validación básica de HTML
        if '<html>' not in v.lower() or '<body>' not in v.lower():
            raise ValueError('Template must contain valid HTML structure')
        return v
    
    @validator('sender_email')
    def validate_sender_format(cls, v):
        if '@' not in v or '.' not in v.split('@')[1]:
            raise ValueError('Invalid email format')
        return v

# ===== SEND TRACKING MODELS =====

class EmailRecipient(BaseModel):
    """Destinatario de email"""
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    recipient_id: Optional[str] = None  # ID interno del usuario
    segment_id: Optional[str] = None
    personalization_data: Dict[str, str] = Field(default_factory=dict)
    
    # Targeting match data
    targeting_score: Optional[float] = Field(None, ge=0, le=1)
    segment_match: Dict[str, bool] = Field(default_factory=dict)

class EmailSendResult(BaseModel):
    """Resultado de envío de email"""
    recipient: EmailRecipient
    variant_id: str
    sent_at: datetime
    
    # Delivery tracking
    delivered: bool = False
    delivered_at: Optional[datetime] = None
    bounce_type: Optional[str] = None  # hard, soft, complaint
    bounce_reason: Optional[str] = None
    
    # Engagement tracking  
    opened: bool = False
    opened_at: Optional[datetime] = None
    clicked: bool = False
    clicked_at: Optional[datetime] = None
    unsubscribed: bool = False
    unsubscribed_at: Optional[datetime] = None
    
    # Technical data
    email_client: Optional[str] = None
    device_type: Optional[str] = None
    location_country: Optional[str] = None
    ip_address: Optional[str] = None

# ===== ANALYTICS MODELS =====

class EmailMetrics(BaseModel):
    """Métricas de email experiment"""
    # Basic metrics
    total_sent: int = 0
    delivered_count: int = 0
    bounced_count: int = 0
    opened_count: int = 0
    clicked_count: int = 0
    unsubscribed_count: int = 0
    
    # Calculated rates
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    click_to_open_rate: float = 0.0
    unsubscribe_rate: float = 0.0
    
    # Advanced metrics
    unique_opens: int = 0
    unique_clicks: int = 0
    forwards: int = 0
    replies: int = 0
    spam_complaints: int = 0
    
    # Time-based metrics
    average_time_to_open: Optional[float] = None  # Minutes
    average_time_to_click: Optional[float] = None  # Minutes
    peak_engagement_hour: Optional[int] = None
    
    def calculate_rates(self):
        """Calcular rates basados en counts"""
        if self.total_sent > 0:
            self.delivery_rate = self.delivered_count / self.total_sent
            self.open_rate = self.opened_count / self.total_sent
            self.click_rate = self.clicked_count / self.total_sent
            self.unsubscribe_rate = self.unsubscribed_count / self.total_sent
            
        if self.opened_count > 0:
            self.click_to_open_rate = self.clicked_count / self.opened_count

class EmailVariantPerformance(BaseModel):
    """Performance de una variante específica"""
    variant_id: str
    variant_name: str
    element_changes: Dict[str, str]  # element -> new_value
    
    metrics: EmailMetrics
    
    # Statistical significance
    confidence_level: float = 0.0
    p_value: Optional[float] = None
    is_statistically_significant: bool = False
    
    # Comparison vs control
    lift_over_control: Dict[str, float] = Field(default_factory=dict)  # metric -> lift %

class EmailExperimentAnalytics(BaseModel):
    """Analytics completas del experimento de email"""
    experiment_id: str
    experiment_name: str
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    
    # Variant performance
    variants: List[EmailVariantPerformance]
    control_variant_id: str
    
    # Overall experiment metrics
    total_recipients: int
    test_group_size: int
    winner_variant_id: Optional[str] = None
    winner_selected_at: Optional[datetime] = None
    
    # Segment breakdown
    segment_performance: Dict[str, EmailMetrics] = Field(default_factory=dict)
    
    # Email client breakdown
    client_performance: Dict[str, EmailMetrics] = Field(default_factory=dict)
    
    # Deliverability insights
    deliverability_score: float = Field(0.0, ge=0, le=100)
    spam_score: float = Field(0.0, ge=0, le=10)
    reputation_impact: str = Field("neutral", regex=r'^(positive|neutral|negative))
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    next_test_suggestions: List[str] = Field(default_factory=list)

# ===== TEMPLATE ANALYSIS =====

class EmailTemplateElement(BaseModel):
    """Elemento encontrado en template analysis"""
    element_type: EmailElementType
    selector: EmailSelector
    current_content: str
    priority: int = Field(5, ge=1, le=10)
    testing_impact: str = Field("medium", regex=r'^(low|medium|high|critical))
    
    # Analysis results
    optimization_potential: float = Field(0.0, ge=0, le=1)
    spam_risk: int = Field(0, ge=0, le=10)
    character_count: int = 0
    
    # Suggestions
    variant_suggestions: List[str] = Field(default_factory=list)
    best_practices: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class EmailTemplateAnalysis(BaseModel):
    """Resultado del análisis de template"""
    template_html: str
    template_text: Optional[str] = None
    
    # Identified elements
    testable_elements: List[EmailTemplateElement]
    total_elements_found: int = 0
    high_impact_elements: int = 0
    
    # Overall template analysis
    template_score: float = Field(0.0, ge=0, le=100)
    deliverability_score: float = Field(0.0, ge=0, le=100)
    mobile_friendly_score: float = Field(0.0, ge=0, le=100)
    
    # Email client compatibility
    client_compatibility: Dict[EmailClient, float] = Field(default_factory=dict)
    
    # Content analysis
    word_count: int = 0
    image_count: int = 0
    link_count: int = 0
    personalization_tokens: List[str] = Field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    priority_tests: List[str] = Field(default_factory=list)
    
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)

# ===== REQUEST/RESPONSE MODELS =====

class EmailAnalysisRequest(BaseModel):
    """Request para analizar template de email"""
    template_html: str = Field(..., min_length=50)
    template_name: Optional[str] = None
    email_platform: EmailPlatform = EmailPlatform.MAILGUN
    analyze_deliverability: bool = True
    analyze_mobile_compatibility: bool = True
    suggest_variants: bool = True
    max_suggestions_per_element: int = Field(3, ge=1, le=10)

class EmailAnalysisResponse(BaseModel):
    """Response del análisis de template"""
    analysis: EmailTemplateAnalysis
    estimated_analysis_time: float  # seconds
    success: bool = True
    warnings: List[str] = Field(default_factory=list)

class CreateEmailExperimentRequest(BaseModel):
    """Request para crear experimento de email"""
    config: EmailExperimentConfig
    recipients: List[EmailRecipient] = Field(default_factory=list)
    send_test_emails: bool = False  # Enviar emails de prueba antes del test real
    test_email_addresses: List[str] = Field(default_factory=list)
    
    @validator('test_email_addresses')
    def validate_test_emails(cls, v):
        for email in v:
            if '@' not in email or '.' not in email.split('@')[1]:
                raise ValueError(f'Invalid test email format: {email}')
        return v

class CreateEmailExperimentResponse(BaseModel):
    """Response de crear experimento de email"""
    experiment_id: str
    email_experiment_id: str
    estimated_recipients: int
    test_group_size: int
    estimated_send_time: Optional[datetime] = None
    
    # Validation results
    deliverability_check: Dict[str, Any] = Field(default_factory=dict)
    spam_check_results: Dict[str, Any] = Field(default_factory=dict)
    
    # Preview URLs
    variant_preview_urls: Dict[str, str] = Field(default_factory=dict)
    
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

class EmailSendRequest(BaseModel):
    """Request para enviar experimento de email"""
    experiment_id: str
    confirm_send: bool = False  # Safety flag
    send_test_first: bool = True
    override_schedule: Optional[datetime] = None
    
    # Final validations
    validate_deliverability: bool = True
    validate_links: bool = True
    validate_unsubscribe: bool = True

class EmailSendResponse(BaseModel):
    """Response de envío de email"""
    send_id: str
    experiment_id: str
    total_queued: int
    estimated_delivery_time: int  # minutes
    
    # Send breakdown
    variants_queued: Dict[str, int] = Field(default_factory=dict)
    segments_targeted: List[str] = Field(default_factory=list)
    
    # Tracking info
    tracking_urls: Dict[str, str] = Field(default_factory=dict)
    webhook_configured: bool = False
    
    status: str = "queued"
    queued_at: datetime = Field(default_factory=datetime.utcnow)

class EmailPreviewRequest(BaseModel):
    """Request para preview de email"""
    experiment_id: str
    variant_selections: Dict[str, int] = Field(default_factory=dict)
    email_client: EmailClient = EmailClient.GMAIL_WEB
    preview_data: Dict[str, str] = Field(default_factory=dict)  # Datos de personalización
    
class EmailPreviewResponse(BaseModel):
    """Response con preview de email"""
    html_content: str
    text_content: Optional[str] = None
    subject_line: str
    preheader: Optional[str] = None
    
    # Preview metadata
    email_client: EmailClient
    viewport_width: int
    estimated_render: str  # base64 screenshot o URL
    
    # Analysis
    content_warnings: List[str] = Field(default_factory=list)
    client_compatibility_issues: List[str] = Field(default_factory=list)
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)

# ===== INTEGRATION MODELS =====

class EmailPlatformConfig(BaseModel):
    """Configuración de plataforma de email"""
    platform: EmailPlatform
    api_key: str = Field(..., min_length=10)
    domain: Optional[str] = None
    webhook_url: Optional[str] = None
    
    # Platform-specific settings
    mailgun_region: Optional[str] = Field(None, regex=r'^(us|eu))  # Para Mailgun
    sendgrid_subuser: Optional[str] = None  # Para SendGrid
    ses_region: Optional[str] = None  # Para Amazon SES
    
    # Validation settings
    verify_domain: bool = True
    test_connection: bool = True

class WebhookEvent(BaseModel):
    """Evento recibido por webhook"""
    platform: EmailPlatform
    event_type: str  # delivered, opened, clicked, bounced, etc.
    timestamp: datetime
    
    # Email identification
    message_id: str
    experiment_id: Optional[str] = None
    variant_id: Optional[str] = None
    recipient_email: str
    
    # Event-specific data
    event_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Technical data
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[Dict[str, str]] = None

# ===== HELPER FUNCTIONS =====

def generate_email_selector_token(element_type: EmailElementType, index: int = 0) -> str:
    """Generar token de selector para elemento de email"""
    base_token = element_type.value
    if index > 0:
        base_token = f"{base_token}_{index}"
    return f"{{{{{base_token}}}}}"

def extract_personalization_tokens(template: str) -> List[str]:
    """Extraer tokens de personalización del template"""
    import re
    pattern = r'\{\{([^}]+)\}\}'
    matches = re.findall(pattern, template)
    return list(set(matches))

def validate_email_template_html(html: str) -> Dict[str, Any]:
    """Validar HTML del template de email"""
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, 'html.parser')
    
    validation_results = {
        'valid_html': True,
        'has_html_tag': bool(soup.find('html')),
        'has_body_tag': bool(soup.find('body')),
        'has_head_tag': bool(soup.find('head')),
        'image_count': len(soup.find_all('img')),
        'link_count': len(soup.find_all('a')),
        'table_based_layout': len(soup.find_all('table')) > 0,
        'responsive_meta': bool(soup.find('meta', attrs={'name': 'viewport'})),
        'issues': []
    }
    
    # Check for common issues
    if not validation_results['has_body_tag']:
        validation_results['issues'].append('Missing <body> tag')
    
    if validation_results['image_count'] > 10:
        validation_results['issues'].append('Too many images (affects load time)')
    
    # Check for unsubscribe link
    unsubscribe_found = any(
        'unsubscribe' in link.get('href', '').lower() 
        for link in soup.find_all('a', href=True)
    )
    if not unsubscribe_found:
        validation_results['issues'].append('Missing unsubscribe link')
    
    return validation_results

def calculate_email_spam_score(content: str, subject: str = "") -> Dict[str, Any]:
    """Calcular score de spam básico para email"""
    spam_indicators = {
        'excessive_caps': len([c for c in content if c.isupper()]) / len(content) > 0.3,
        'excessive_exclamation': content.count('!') > 5,
        'spam_words': any(word in content.lower() for word in [
            'free', 'urgent', 'limited time', 'act now', 'guarantee', 
            'no risk', 'money back', 'winner', 'congratulations'
        ]),
        'subject_spam': any(word in subject.lower() for word in [
            'free', 'urgent', '!!!', 'winner', 'guarantee'
        ]) if subject else False,
        'excessive_links': content.count('http') > 10
    }
    
    spam_score = sum(spam_indicators.values()) * 2  # 0-10 scale
    
    return {
        'spam_score': min(spam_score, 10),
        'indicators': spam_indicators,
        'risk_level': 'low' if spam_score < 3 else 'medium' if spam_score < 6 else 'high'
    }

# ===== EXAMPLE USAGE =====

"""
Ejemplo de uso de los modelos:

# 1. Crear configuración de experimento de email
email_config = EmailExperimentConfig(
    name="Newsletter Headline Test",
    email_template=html_template,
    elements=[
        EmailElementConfig(
            element_id="headline_1",
            email_element_type=EmailElementType.HEADLINE,
            selector=EmailSelector(
                token="{{main_headline}}",
                html_selector="h1.headline"
            ),
            original_content={"text": "Weekly Newsletter"},
            variants=[
                EmailVariant(
                    base_content=VariantContent(type="text", value="Your Weekly Insights"),
                    spam_risk_score=2
                ),
                EmailVariant(
                    base_content=VariantContent(type="text", value="This Week's Top Stories"),
                    spam_risk_score=1
                )
            ]
        )
    ],
    targeting=EmailTargeting(
        engagement_level="high",
        last_open_days=30
    ),
    sender_email="newsletter@company.com",
    sender_name="Company Newsletter"
)

# 2. Analizar template
analysis_request = EmailAnalysisRequest(
    template_html=html_template,
    analyze_deliverability=True
)

# 3. Crear experimento
create_request = CreateEmailExperimentRequest(
    config=email_config,
    send_test_emails=True,
    test_email_addresses=["test@company.com"]
)
"""
