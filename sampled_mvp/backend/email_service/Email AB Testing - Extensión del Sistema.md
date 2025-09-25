# 📧 Email A/B Testing - Extensión del Sistema

## 🎯 Conceptos Clave

**Diferencia principal**: 
- **Web**: Elementos en vivo, cambios dinámicos, tracking en tiempo real
- **Email**: Templates estáticos, variantes pre-generadas, tracking por clicks/opens

## 🏗️ Arquitectura - Sin Cambios Estructurales

Tu sistema actual es **perfectamente extensible**:

### Modelos Existentes Reutilizables
```python
# ✅ Ya tienes estos - NO cambiar
ElementConfig          # Funciona para email elements
TargetingConfig       # Perfecto para email segmentation  
VariantContent        # Ideal para email content variants
SessionAnalytics      # Para email engagement tracking
```

### Nuevos Modelos Específicos de Email
```python
# 📧 Nuevos - AGREGAR sin tocar existentes

class EmailElementType(str, Enum):
    SUBJECT_LINE = "subject_line"      # Línea de asunto
    HEADLINE = "headline"              # H1, H2 en email
    CTA_BUTTON = "cta_button"         # Botones de acción
    BODY_TEXT = "body_text"           # Texto del cuerpo
    IMAGE = "image"                   # Imágenes
    SENDER_NAME = "sender_name"       # Nombre del remitente
    PREHEADER = "preheader"           # Texto de vista previa

class EmailExperimentType(str, Enum):
    TEMPLATE = "template"              # Template completo
    ELEMENT = "element"               # Elementos específicos
    SEND_TIME = "send_time"           # Hora de envío
    FREQUENCY = "frequency"           # Frecuencia de envío

class EmailTargeting(BaseModel):
    """Targeting específico para emails"""
    # Reutiliza TargetingConfig base + específicos
    list_segments: List[str] = []              # Segmentos de lista
    engagement_level: Optional[str] = None     # high, medium, low
    last_open_days: Optional[int] = None       # Días desde último open
    purchase_history: Optional[str] = None     # buyer, prospect, customer
    email_client: Optional[str] = None         # gmail, outlook, apple
    device_type: Optional[str] = None          # mobile, desktop

class EmailElementConfig(BaseModel):
    """Configuración de elemento específico para email"""
    # Extiende ElementConfig base
    element_id: str
    element_type: EmailElementType
    email_selector: str                        # ej: "{{subject_line}}", "{{cta_button_1}}"
    original_content: Dict[str, Any]
    variants: List[VariantContent]
    
    # Email-specific
    affects_deliverability: bool = False       # Cambios que afectan deliverability
    spam_risk: int = Field(0, ge=0, le=10)    # Risk score 0-10
    personalization_tokens: List[str] = []     # {{first_name}}, {{company}}

class EmailExperimentConfig(BaseModel):
    """Configuración completa de experimento de email"""
    # Reutiliza ExperimentConfigExtended + específicos
    experiment_type: EmailExperimentType
    email_elements: List[EmailElementConfig]
    targeting: EmailTargeting
    
    # Email campaign settings
    send_schedule: Dict[str, Any] = {}         # Programación de envío
    test_percentage: float = Field(0.1, ge=0.01, le=0.5)  # % para test (resto control)
    winner_selection_criteria: str = "open_rate"  # open_rate, click_rate, conversion
    auto_send_winner: bool = False             # Enviar ganador automáticamente
    
    # Technical settings
    email_platform: str = "mailgun"           # mailgun, sendgrid, ses
    tracking_domain: Optional[str] = None     # Para tracking de clicks
    suppress_lists: List[str] = []            # Listas de supresión
```

## 🔧 Base de Datos - Extensión Sin Impacto

### Nuevas Tablas (no tocar existentes)
```sql
-- Email experiments (extiende experiments)
CREATE TABLE IF NOT EXISTS email_experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    base_experiment_id UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    
    -- Email-specific data
    email_platform VARCHAR(50) NOT NULL DEFAULT 'mailgun',
    template_id VARCHAR(255),
    subject_line_variants JSONB DEFAULT '[]',
    send_schedule JSONB DEFAULT '{}',
    test_percentage DECIMAL(4,2) DEFAULT 0.10,
    winner_criteria VARCHAR(50) DEFAULT 'open_rate',
    auto_send_winner BOOLEAN DEFAULT false,
    
    -- Campaign data
    total_recipients INTEGER DEFAULT 0,
    test_group_size INTEGER DEFAULT 0,
    sent_at TIMESTAMP WITH TIME ZONE,
    winner_selected_at TIMESTAMP WITH TIME ZONE,
    winner_variant_id UUID,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Email recipients and sends
CREATE TABLE IF NOT EXISTS email_sends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_experiment_id UUID NOT NULL REFERENCES email_experiments(id) ON DELETE CASCADE,
    variant_id UUID NOT NULL REFERENCES experiment_elements(id),
    
    recipient_email VARCHAR(255) NOT NULL,
    recipient_id VARCHAR(255),
    segment_data JSONB DEFAULT '{}',
    
    -- Send tracking
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    unsubscribed_at TIMESTAMP WITH TIME ZONE,
    bounced_at TIMESTAMP WITH TIME ZONE,
    
    -- Email client data
    email_client VARCHAR(100),
    device_type VARCHAR(50),
    location_country VARCHAR(10),
    
    INDEX idx_email_sends_experiment (email_experiment_id),
    INDEX idx_email_sends_recipient (recipient_email),
    INDEX idx_email_sends_variant (variant_id)
);

-- Email interactions (clicks específicos)
CREATE TABLE IF NOT EXISTS email_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email_send_id UUID NOT NULL REFERENCES email_sends(id) ON DELETE CASCADE,
    
    interaction_type VARCHAR(50) NOT NULL, -- click, open, forward, etc
    element_clicked VARCHAR(255),          -- cta_button, link, image
    click_url VARCHAR(500),
    click_position VARCHAR(50),            -- top, middle, bottom
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_email_interactions_send (email_send_id),
    INDEX idx_email_interactions_type (interaction_type)
);
```

## 📊 API Endpoints - Extensión Limpia

### Nuevos Endpoints (sin tocar existentes)
```python
# ===== EMAIL SPECIFIC ENDPOINTS =====

@app.post("/api/emails/analyze-template", response_model=EmailAnalysisResponse)
async def analyze_email_template(
    request: EmailAnalysisRequest,
    user_id: str = Depends(get_current_user)
):
    """Analizar template de email para encontrar elementos testeable"""
    # Parsear HTML del email
    # Identificar elementos como {{subject_line}}, botones, etc.
    # Retornar análisis de testability

@app.post("/api/experiments/email", response_model=CreateExperimentResponse) 
async def create_email_experiment(
    request: EmailExperimentConfig,
    user_id: str = Depends(get_current_user)
):
    """Crear experimento de email"""
    # Crear experimento base (reutiliza función existente)
    # Crear email_experiment específico
    # Configurar elementos de email

@app.get("/api/experiments/{experiment_id}/email-preview")
async def preview_email_variants(
    experiment_id: str,
    variant_selections: Dict[str, int] = {},
    user_id: str = Depends(get_current_user)
):
    """Preview de variantes de email"""
    # Generar HTML de email con variantes aplicadas
    # Retornar preview para diferentes email clients

@app.post("/api/experiments/{experiment_id}/email-send")
async def send_email_test(
    experiment_id: str,
    send_config: EmailSendConfig,
    user_id: str = Depends(get_current_user)
):
    """Enviar test de email"""
    # Validar experimento
    # Segmentar audiencia según targeting
    # Enviar variantes vía email platform
    # Configurar tracking

@app.get("/api/experiments/{experiment_id}/email-analytics")
async def get_email_analytics(
    experiment_id: str,
    user_id: str = Depends(get_current_user)
):
    """Analytics específicas de email"""
    # Métricas de deliverability
    # Open rates, click rates por variante
    # Engagement por email client, device
    # Heat map de clicks en email

# ===== EMAIL PLATFORM INTEGRATIONS =====

@app.post("/api/email-platforms/mailgun/webhook")
async def mailgun_webhook(request: Request):
    """Webhook para tracking de Mailgun"""
    # Procesar eventos: delivered, opened, clicked, unsubscribed
    # Actualizar email_sends y email_interactions

@app.post("/api/email-platforms/sendgrid/webhook") 
async def sendgrid_webhook(request: Request):
    """Webhook para tracking de SendGrid"""

@app.post("/api/email-platforms/ses/webhook")
async def ses_webhook(request: Request):
    """Webhook para tracking de Amazon SES"""
```

## 🎨 Frontend - Dashboard Email

### Nuevo Tab en Dashboard Existente
```javascript
// En tu index.html existente, agregar:
<div class="experiment-type-tabs">
    <button class="tab active" onclick="showWebExperiments()">🌐 Web Testing</button>
    <button class="tab" onclick="showEmailExperiments()">📧 Email Testing</button>
</div>

// Email experiment creation flow
function createEmailExperiment() {
    // 1. Upload/paste email template
    // 2. Identify testable elements
    // 3. Create variants
    // 4. Setup targeting
    // 5. Schedule send
}
```

### Email Template Analyzer
```javascript
class EmailTemplateAnalyzer {
    analyzeTemplate(htmlContent) {
        const testableElements = [];
        
        // Subject line (always testable)
        if (htmlContent.includes('{{subject_line}}')) {
            testableElements.push({
                type: 'subject_line',
                current: this.extractSubjectLine(htmlContent),
                priority: 'high',
                impact: 'Open rate'
            });
        }
        
        // CTA buttons
        const buttons = this.findCTAButtons(htmlContent);
        buttons.forEach(button => {
            testableElements.push({
                type: 'cta_button',
                element: button,
                current: button.text,
                priority: 'high',
                impact: 'Click rate'
            });
        });
        
        // Headlines
        const headlines = this.findHeadlines(htmlContent);
        // ... etc
        
        return {
            template: htmlContent,
            testableElements,
            recommendations: this.generateRecommendations(testableElements)
        };
    }
}
```

## 🎯 Flujo de Usuario - Email Testing

### 1. **Crear Experimento de Email**
```
Usuario en Dashboard → 
Click "📧 Email Testing" → 
Upload/Paste Template → 
Sistema identifica elementos testeable → 
Usuario selecciona qué testear → 
Crear variantes → 
Configurar targeting → 
Programar envío
```

### 2. **Análisis de Template**
```html
<!-- Template original -->
<html>
<body>
    <h1>{{headline}}</h1>
    <p>{{body_text}}</p>
    <a href="{{cta_url}}" class="cta">{{cta_text}}</a>
</body>
</html>

<!-- Sistema identifica: -->
- {{headline}} → Testeable (Impacto: Alto)
- {{body_text}} → Testeable (Impacto: Medio)  
- {{cta_text}} → Testeable (Impacto: Alto)
```

### 3. **Preview Multi-Client**
```javascript
// Preview en diferentes email clients
const emailPreviews = [
    { client: 'Gmail Web', width: 600 },
    { client: 'Outlook Desktop', width: 580 },
    { client: 'iPhone Mail', width: 320 },
    { client: 'Gmail Mobile', width: 360 }
];
```

## 📈 Métricas Email vs Web

### Web Metrics
- Page views, clicks, conversions
- Time on page, scroll depth
- Heatmaps, user flows

### Email Metrics
- **Deliverability**: Delivered rate, bounce rate
- **Engagement**: Open rate, click rate, forward rate
- **Conversion**: Click-to-conversion, revenue per email
- **Lifecycle**: Unsubscribe rate, list growth

## 🔌 Integraciones Email Platform

### Mailgun Integration
```python
class MailgunIntegration:
    def send_experiment_emails(self, experiment_id, recipients):
        # Enviar cada variante a su segmento
        for variant in experiment.variants:
            segment_recipients = self.get_segment_recipients(variant.targeting)
            
            # Generar email con variante aplicada
            email_html = self.apply_variant_to_template(
                experiment.template, variant.content
            )
            
            # Enviar vía Mailgun con tracking
            self.mailgun_client.send({
                'to': segment_recipients,
                'subject': variant.subject_line,
                'html': email_html,
                'tracking': True,
                'tracking-clicks': True,
                'tracking-opens': True,
                'custom_variables': {
                    'experiment_id': experiment_id,
                    'variant_id': variant.id
                }
            })
```

## 🚀 Implementación Sin Breaking Changes

### Fase 1: Base Email Support (1-2 semanas)
1. ✅ Agregar modelos de email (sin tocar existentes)
2. ✅ Crear tablas de email (sin tocar existentes)  
3. ✅ Endpoints básicos de análisis de template
4. ✅ UI básica para email experiments

### Fase 2: Email Platform Integration (2-3 semanas)
1. ✅ Integración con Mailgun/SendGrid
2. ✅ Sistema de webhooks para tracking
3. ✅ Analytics de email
4. ✅ Preview multi-client

### Fase 3: Advanced Email Features (2-3 semanas)
1. ✅ Send time optimization
2. ✅ Advanced segmentation
3. ✅ Automated winner selection
4. ✅ Deliverability optimization

## 💡 Ventajas del Approach

1. **Zero Breaking Changes**: Web testing sigue funcionando igual
2. **Shared Infrastructure**: Reutiliza auth, analytics, Thompson Sampling
3. **Unified Dashboard**: Un solo lugar para web y email testing
4. **Cross-Channel Insights**: Ver performance web + email juntos
5. **Scalable**: Fácil agregar SMS, push notifications después

¿Te gusta este approach? ¿Quieres que empecemos con los modelos de email o prefieres ver el configurador de templates primero?
