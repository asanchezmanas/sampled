# backend/models.py
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import json

# ===== AUTH MODELS =====

class RegisterRequest(BaseModel):
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=2, max_length=100)

class LoginRequest(BaseModel):
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=1, max_length=100)

class AuthResponse(BaseModel):
    token: str
    user_id: str

# ===== EXPERIMENT MODELS =====

class ArmRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    content: Dict[str, Any] = Field(default_factory=dict)

class CreateExperimentRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    arms: List[ArmRequest] = Field(..., min_items=2, max_items=10)
    config: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('arms')
    def validate_arms(cls, v):
        names = [arm.name for arm in v]
        if len(names) != len(set(names)):
            raise ValueError('All arm names must be unique')
        return v

class CreateExperimentResponse(BaseModel):
    experiment_id: str
    arm_ids: List[str]

class ArmData(BaseModel):
    id: str
    name: str
    description: Optional[str]
    content: Dict[str, Any]
    assignments: int = 0
    conversions: int = 0
    conversion_rate: float = 0.0
    alpha: float = 1.0
    beta: float = 1.0

class ExperimentResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: ExperimentStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    arms_count: int = 0
    total_users: int = 0
    conversion_rate: float = 0.0

class ExperimentDetailResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: ExperimentStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    config: Dict[str, Any]
    arms: List[ArmData]

# ===== ASSIGNMENT MODELS =====

class AssignmentRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=255)
    session_id: Optional[str] = Field(None, max_length=255)
    context: Optional[Dict[str, Any]] = Field(None)
    
    @validator('context')
    def validate_context(cls, v):
        if v and len(str(v)) > 5000:  # Prevent huge context objects
            raise ValueError('Context data too large')
        return v

class AssignmentResponse(BaseModel):
    arm_id: str
    content: Dict[str, Any]
    assignment_id: str
    new_assignment: bool

class ConversionRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=255)
    value: float = Field(default=1.0, ge=0)
    metadata: Optional[Dict[str, Any]] = Field(None)

# ===== ANALYTICS MODELS =====

class AnalyticsSummary(BaseModel):
    total_users: int
    total_conversions: int
    overall_conversion_rate: float
    best_performing_arm: Optional[Dict[str, Any]] = None
    confidence_level: float = 0.0

class BayesianArm(BaseModel):
    arm_id: str
    name: str
    probability_best: float
    expected_conversion_rate: float
    credible_interval_lower: float
    credible_interval_upper: float

class BayesianAnalysis(BaseModel):
    arms: List[BayesianArm] = []
    recommended_winner: Optional[str] = None
    confidence_threshold_met: bool = False
    continue_experiment: bool = True
    statistical_power: float = 0.0
    message: Optional[str] = None
    min_samples_needed: Optional[int] = None

class AnalyticsResponse(BaseModel):
    experiment_id: str
    experiment_name: str
    status: ExperimentStatus
    created_at: datetime
    arms: List[ArmData]
    summary: AnalyticsSummary
    bayesian_analysis: BayesianAnalysis

# ===== GTM INTEGRATION MODELS =====

class GTMArmData(BaseModel):
    arm_id: str
    name: str
    content: Dict[str, Any]

class GTMExperimentResponse(BaseModel):
    experiment_id: str
    name: str
    arms: List[GTMArmData]
    auto_conversion_selectors: List[str] = []

# ===== VALIDATION HELPERS =====

class ValidationError(Exception):
    """Custom validation error"""
    pass

def validate_experiment_name(name: str) -> str:
    """Validate experiment name"""
    if not name or len(name.strip()) < 3:
        raise ValidationError("Experiment name must be at least 3 characters")
    if len(name) > 255:
        raise ValidationError("Experiment name too long")
    return name.strip()

def validate_user_id(user_id: str) -> str:
    """Validate user ID format"""
    if not user_id or not user_id.strip():
        raise ValidationError("User ID cannot be empty")
    if len(user_id) > 255:
        raise ValidationError("User ID too long")
    # Allow alphanumeric, hyphens, underscores
    if not all(c.isalnum() or c in '-_.' for c in user_id):
        raise ValidationError("User ID contains invalid characters")
    return user_id.strip()

def validate_conversion_value(value: float) -> float:
    """Validate conversion value"""
    if value < 0:
        raise ValidationError("Conversion value cannot be negative")
    if value > 1000000:  # Reasonable upper limit
        raise ValidationError("Conversion value too large")
    return value



# ===== NUEVOS ENUMS =====

class ElementType(str, Enum):
    TEXT = "text"
    BUTTON = "button" 
    HEADLINE = "headline"
    LINK = "link"
    IMAGE = "image"
    FORM = "form"
    GENERIC = "generic"

class SelectorType(str, Enum):
    ID = "id"
    CLASS = "class"
    CSS = "css"
    XPATH = "xpath"
    DATA_ATTRIBUTE = "data"
    POSITION = "position"

class TargetingOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"

# ===== CONFIGURACIÓN DE ELEMENTOS =====

class SelectorConfig(BaseModel):
    """Configuración de un selector específico"""
    type: SelectorType
    selector: str
    specificity: int = Field(..., ge=0, le=100)
    reliable: bool = True
    
class ElementSelector(BaseModel):
    """Múltiples selectores para un elemento con fallbacks"""
    primary: SelectorConfig
    fallbacks: List[SelectorConfig] = Field(default_factory=list)
    xpath: Optional[str] = None
    
    @validator('fallbacks')
    def validate_fallbacks(cls, v, values):
        if 'primary' in values and len(v) == 0:
            # Al menos debería tener el selector primario
            pass
        return v

class ElementStability(BaseModel):
    """Análisis de estabilidad del elemento"""
    score: int = Field(..., ge=0, le=100)
    factors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

class ElementPosition(BaseModel):
    """Posición del elemento para preview"""
    x: float
    y: float
    width: float
    height: float
    viewport_width: int
    viewport_height: int

class VariantContent(BaseModel):
    """Contenido de una variante"""
    type: str = "text"  # text, html, style, attribute
    value: Union[str, Dict[str, Any]]
    attributes: Optional[Dict[str, str]] = None
    styles: Optional[Dict[str, str]] = None

class ElementConfig(BaseModel):
    """Configuración completa de un elemento"""
    id: Optional[str] = None
    selector: ElementSelector
    element_type: ElementType
    original_content: Dict[str, Any]
    variants: List[VariantContent]
    position: Optional[ElementPosition] = None
    stability: Optional[ElementStability] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('variants')
    def validate_variants(cls, v):
        if len(v) < 1:
            raise ValueError('At least one variant is required')
        return v

# ===== TARGETING SYSTEM =====

class TargetingRule(BaseModel):
    """Regla individual de targeting"""
    id: Optional[str] = None
    type: str  # device, browser, location, traffic_source, time, custom
    operator: TargetingOperator
    value: str
    enabled: bool = True

class TargetingGroup(BaseModel):
    """Grupo de reglas (AND logic within group)"""
    id: Optional[str] = None
    name: str
    rules: List[TargetingRule]
    match_all: bool = True  # True = AND, False = OR

class TargetingConfig(BaseModel):
    """Configuración completa de targeting"""
    enabled: bool = False
    groups: List[TargetingGroup] = Field(default_factory=list)  # OR logic between groups
    traffic_allocation: float = Field(1.0, ge=0.0, le=1.0)
    
    @validator('groups')
    def validate_groups(cls, v, values):
        if values.get('enabled', False) and len(v) == 0:
            raise ValueError('At least one targeting group required when enabled')
        return v

# ===== EXPERIMENTOS EXTENDIDOS =====

class ExperimentConfigExtended(BaseModel):
    """Configuración extendida para experimentos Fase 2"""
    # Configuración básica (existente)
    traffic_allocation: float = Field(1.0, ge=0.01, le=1.0)
    min_sample_size: int = Field(100, ge=10)
    confidence_threshold: float = Field(0.95, ge=0.8, le=0.99)
    auto_pause: bool = False
    
    # Nuevas configuraciones Fase 2
    max_elements: int = Field(5, ge=1, le=20)
    enable_preview: bool = True
    enable_heatmaps: bool = False
    enable_micro_conversions: bool = False
    
    # Configuraciones avanzadas
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None
    exclude_selectors: List[str] = Field(default_factory=list)

class CreateExperimentRequestExtended(BaseModel):
    """Request extendido para crear experimento"""
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    url: str = Field(..., min_length=1)  # URL donde se ejecuta
    elements: List[ElementConfig] = Field(..., min_items=1, max_items=10)
    targeting: TargetingConfig = Field(default_factory=TargetingConfig)
    config: ExperimentConfigExtended = Field(default_factory=ExperimentConfigExtended)
    
    @validator('elements')
    def validate_elements(cls, v):
        if len(v) == 0:
            raise ValueError('At least one element is required')
        return v
    
    @validator('url')
    def validate_url(cls, v):
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

# ===== ANALYTICS EXTENDIDAS =====

class ElementInteraction(BaseModel):
    """Interacción con un elemento"""
    element_id: str
    interaction_type: str  # click, hover, scroll_into_view, etc.
    timestamp: datetime
    coordinates: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = None

class MicroConversion(BaseModel):
    """Micro conversión"""
    type: str  # scroll_50, time_30s, click_area, etc.
    value: float = 1.0
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class SessionAnalytics(BaseModel):
    """Analytics de sesión extendidas"""
    session_id: str
    user_id: str
    experiment_id: str
    variant_assignments: Dict[str, str]  # element_id -> variant_id
    
    # Métricas básicas
    page_load_time: Optional[float] = None
    time_on_page: float = 0
    scroll_depth: float = 0
    
    # Interacciones
    interactions: List[ElementInteraction] = Field(default_factory=list)
    micro_conversions: List[MicroConversion] = Field(default_factory=list)
    
    # Contexto
    device_info: Optional[Dict[str, Any]] = None
    viewport_size: Optional[Dict[str, int]] = None

# ===== PREVIEW SYSTEM =====

class PreviewRequest(BaseModel):
    """Request para generar preview"""
    experiment_id: str
    element_configs: List[ElementConfig]
    variant_selections: Dict[str, int]  # element_id -> variant_index
    viewport: Optional[Dict[str, int]] = None

class PreviewResponse(BaseModel):
    """Response con datos de preview"""
    preview_id: str
    changes: List[Dict[str, Any]]
    screenshot_url: Optional[str] = None
    estimated_impact: Optional[Dict[str, Any]] = None

# ===== ELEMENT ANALYSIS =====

class PageAnalysisRequest(BaseModel):
    """Request para analizar elementos de una página"""
    url: str
    include_screenshots: bool = False
    max_elements: int = Field(50, ge=10, le=200)

class AnalyzableElement(BaseModel):
    """Elemento analizable encontrado en la página"""
    selector: ElementSelector
    element_type: ElementType
    content_preview: str
    stability: ElementStability
    testable_properties: List[str]
    priority_score: int = Field(..., ge=0, le=100)
    position: Optional[ElementPosition] = None

class PageAnalysisResponse(BaseModel):
    """Resultado del análisis de página"""
    url: str
    title: str
    elements: List[AnalyzableElement]
    page_info: Dict[str, Any]  # framework detection, etc.
    recommendations: List[str]
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)

# ===== VALIDATION HELPERS =====

def validate_selector_syntax(selector: str, selector_type: SelectorType) -> bool:
    """Valida sintaxis de selector"""
    try:
        if selector_type == SelectorType.CSS:
            # Validación básica de CSS selector
            import re
            css_pattern = r'^[#.]?[a-zA-Z0-9_-]+(\[[^\]]+\])?(::[a-zA-Z-]+)?$'
            return bool(re.match(css_pattern, selector))
        elif selector_type == SelectorType.XPATH:
            # Validación básica de XPath
            return selector.startswith('/') or selector.startswith('./')
        return True
    except:
        return False

def generate_element_id() -> str:
    """Genera ID único para elemento"""
    import uuid
    return f"el_{uuid.uuid4().hex[:8]}"

# ===== RESPONSE MODELS EXTENDIDOS =====

class ElementDetailResponse(BaseModel):
    """Response detallado de elemento"""
    id: str
    selector: ElementSelector
    element_type: ElementType
    original_content: Dict[str, Any]
    variants: List[VariantContent]
    stability: ElementStability
    analytics: Optional[Dict[str, Any]] = None
    created_at: datetime

class ExperimentDetailResponseExtended(BaseModel):
    """Response extendido de experimento con todos los detalles"""
    id: str
    name: str
    description: Optional[str]
    url: str
    status: str
    elements: List[ElementDetailResponse]
    targeting: TargetingConfig
    config: ExperimentConfigExtended
    analytics_summary: Optional[Dict[str, Any]] = None
    created_at: datetime
    started_at: Optional[datetime] = None

class SmartSelectorResponse(BaseModel):
    """Response para smart selector suggestions"""
    element_id: str
    suggested_selectors: List[SelectorConfig]
    stability_analysis: ElementStability
    recommendations: List[str]

# ===== ERROR MODELS =====

class ValidationErrorDetail(BaseModel):
    """Detalle de error de validación"""
    field: str
    message: str
    code: str

class ExperimentError(BaseModel):
    """Error específico de experimento"""
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    suggestions: List[str] = Field(default_factory=list)
