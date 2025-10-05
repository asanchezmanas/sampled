# backend/models.py
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum

# ===== ENUMS =====

class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

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

# ===== ELEMENT CONFIGURATION (FASE 2) =====

class SelectorConfig(BaseModel):
    """Configuración de selector"""
    type: SelectorType
    selector: str
    specificity: int = Field(..., ge=0, le=100)
    reliable: bool = True

class ElementSelector(BaseModel):
    """Selector con fallbacks"""
    primary: SelectorConfig
    fallbacks: List[SelectorConfig] = Field(default_factory=list)
    xpath: Optional[str] = None

class ElementStability(BaseModel):
    """Análisis de estabilidad"""
    score: int = Field(..., ge=0, le=100)
    factors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

class ElementPosition(BaseModel):
    """Posición del elemento"""
    x: float
    y: float
    width: float
    height: float
    viewport_width: int
    viewport_height: int

class VariantContent(BaseModel):
    """Contenido de variante"""
    type: str = "text"
    value: Union[str, Dict[str, Any]]
    attributes: Optional[Dict[str, str]] = None
    styles: Optional[Dict[str, str]] = None

class ElementConfig(BaseModel):
    """Configuración de elemento (Fase 2)"""
    selector: ElementSelector
    element_type: ElementType
    original_content: Dict[str, Any]
    variants: List[VariantContent]
    position: Optional[ElementPosition] = None
    stability: Optional[ElementStability] = None
    
    @validator('variants')
    def validate_variants(cls, v):
        if len(v) < 1:
            raise ValueError('At least one variant is required')
        return v

# ===== TARGETING (FASE 2) =====

class TargetingRule(BaseModel):
    """Regla de targeting"""
    type: str
    operator: TargetingOperator
    value: str
    enabled: bool = True

class TargetingGroup(BaseModel):
    """Grupo de reglas"""
    id: Optional[str] = None
    name: str
    rules: List[TargetingRule]
    match_all: bool = True

class TargetingConfig(BaseModel):
    """Configuración de targeting"""
    enabled: bool = False
    groups: List[TargetingGroup] = Field(default_factory=list)
    traffic_allocation: float = Field(1.0, ge=0.0, le=1.0)

# ===== ARM REQUEST (FASE 1) =====

class ArmRequest(BaseModel):
    """Arm tradicional (Fase 1)"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    content: Dict[str, Any] = Field(default_factory=dict)

# ===== EXPERIMENT REQUEST (UNIFICADO) =====

class CreateExperimentRequest(BaseModel):
    """
    Crear experimento - UNIFICADO
    Soporta tanto Fase 1 (arms) como Fase 2 (elements)
    """
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    
    # Configuración común
    config: Dict[str, Any] = Field(default_factory=dict)
    url: Optional[str] = None
    
    # Fase 1: Arms tradicionales (opcional)
    arms: Optional[List[ArmRequest]] = None
    
    # Fase 2: Elementos multi-elemento (opcional)
    elements: Optional[List[ElementConfig]] = None
    targeting: Optional[TargetingConfig] = None
    
    @validator('arms', 'elements')
    def validate_experiment_type(cls, v, values, field):
        """Validar que se proporcione arms O elements (no ambos)"""
        if field.name == 'elements' and v is not None:
            if values.get('arms') is not None:
                raise ValueError('Cannot provide both arms and elements. Choose one experiment type.')
        return v
    
    @validator('arms')
    def validate_arms(cls, v):
        if v is not None:
            if len(v) < 2:
                raise ValueError('At least 2 arms required for traditional experiments')
            names = [arm.name for arm in v]
            if len(names) != len(set(names)):
                raise ValueError('All arm names must be unique')
        return v
    
    @validator('elements')
    def validate_elements(cls, v):
        if v is not None:
            if len(v) < 1:
                raise ValueError('At least 1 element required for multi-element experiments')
        return v
    
    @validator('url')
    def validate_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class CreateExperimentResponse(BaseModel):
    """Response al crear experimento"""
    experiment_id: str
    arm_ids: List[str] = Field(default_factory=list)
    element_ids: List[str] = Field(default_factory=list)
    experiment_type: str  # 'traditional' o 'multi_element'

# ===== ARM DATA =====

class ArmData(BaseModel):
    """Datos de un arm"""
    id: str
    name: str
    description: Optional[str]
    content: Dict[str, Any]
    assignments: int = 0
    conversions: int = 0
    conversion_rate: float = 0.0
    alpha: float = 1.0
    beta: float = 1.0

# ===== ELEMENT DATA =====

class ElementData(BaseModel):
    """Datos de un elemento"""
    id: str
    element_order: int
    selector_config: Dict[str, Any]
    element_type: str
    original_content: Dict[str, Any]
    variants: List[Dict[str, Any]]
    stability_score: int
    interactions_count: Optional[int] = 0

# ===== EXPERIMENT RESPONSE (UNIFICADO) =====

class ExperimentResponse(BaseModel):
    """Response de experimento - lista simplificada"""
    id: str
    name: str
    description: Optional[str]
    status: ExperimentStatus
    experiment_type: str  # 'traditional' o 'multi_element'
    url: Optional[str]
    created_at: datetime
    started_at: Optional[datetime] = None
    arms_count: int = 0
    elements_count: int = 0
    total_users: int = 0
    conversion_rate: float = 0.0

class ExperimentDetailResponse(BaseModel):
    """Response detallado de experimento - UNIFICADO"""
    id: str
    name: str
    description: Optional[str]
    status: ExperimentStatus
    experiment_type: str
    url: Optional[str]
    config: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime] = None
    
    # Fase 1 data (si aplica)
    arms: List[ArmData] = Field(default_factory=list)
    
    # Fase 2 data (si aplica)
    elements: List[ElementData] = Field(default_factory=list)
    targeting: Optional[Dict[str, Any]] = None

# ===== ASSIGNMENT MODELS =====

class AssignmentRequest(BaseModel):
    """Request de assignment"""
    user_id: str = Field(..., min_length=1, max_length=255)
    session_id: Optional[str] = Field(None, max_length=255)
    context: Optional[Dict[str, Any]] = Field(None)
    
    @validator('context')
    def validate_context(cls, v):
        if v and len(str(v)) > 5000:
            raise ValueError('Context data too large')
        return v

class AssignmentResponse(BaseModel):
    """Response de assignment"""
    arm_id: Optional[str] = None
    content: Dict[str, Any]
    assignment_id: str
    new_assignment: bool
    
    # Para experimentos multi-elemento
    element_variants: Optional[Dict[str, int]] = None

class ConversionRequest(BaseModel):
    """Request de conversión"""
    user_id: str = Field(..., min_length=1, max_length=255)
    value: float = Field(default=1.0, ge=0)
    metadata: Optional[Dict[str, Any]] = Field(None)

# ===== ANALYTICS MODELS =====

class AnalyticsSummary(BaseModel):
    """Resumen de analytics"""
    total_users: int
    total_conversions: int
    overall_conversion_rate: float
    best_performing_arm: Optional[Dict[str, Any]] = None
    confidence_level: float = 0.0

class BayesianArm(BaseModel):
    """Análisis Bayesiano de arm"""
    arm_id: str
    name: str
    probability_best: float
    expected_conversion_rate: float
    credible_interval_lower: float
    credible_interval_upper: float

class BayesianAnalysis(BaseModel):
    """Análisis Bayesiano completo"""
    arms: List[BayesianArm] = []
    recommended_winner: Optional[str] = None
    confidence_threshold_met: bool = False
    continue_experiment: bool = True
    statistical_power: float = 0.0
    message: Optional[str] = None
    min_samples_needed: Optional[int] = None

class AnalyticsResponse(BaseModel):
    """Response de analytics - UNIFICADO"""
    experiment_id: str
    experiment_name: str
    experiment_type: str
    status: ExperimentStatus
    created_at: datetime
    
    # Fase 1 analytics
    arms: List[ArmData] = Field(default_factory=list)
    summary: Optional[AnalyticsSummary] = None
    bayesian_analysis: Optional[BayesianAnalysis] = None
    
    # Fase 2 analytics
    elements_stats: Optional[List[Dict[str, Any]]] = None
    session_stats: Optional[Dict[str, Any]] = None

# ===== SESSION ANALYTICS (FASE 2) =====

class SessionAnalyticsRequest(BaseModel):
    """Request para crear sesión de analytics"""
    session_id: str
    user_id: str
    experiment_id: str
    variant_assignments: Dict[str, str]
    device_info: Optional[Dict[str, Any]] = None
    viewport_size: Optional[Dict[str, int]] = None

class ElementInteraction(BaseModel):
    """Interacción con elemento"""
    element_id: str
    interaction_type: str
    coordinates: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = None

class MicroConversion(BaseModel):
    """Micro conversión"""
    type: str
    value: float = 1.0
    metadata: Optional[Dict[str, Any]] = None

# ===== PREVIEW & ANALYSIS =====

class PreviewRequest(BaseModel):
    """Request para crear preview"""
    experiment_id: str
    variant_selections: Dict[str, int]
    viewport: Optional[Dict[str, int]] = None

class PreviewResponse(BaseModel):
    """Response de preview"""
    preview_id: str
    changes: List[Dict[str, Any]]
    screenshot_url: Optional[str] = None

class PageAnalysisRequest(BaseModel):
    """Request para analizar página"""
    url: str
    max_elements: int = Field(50, ge=10, le=200)

class AnalyzableElement(BaseModel):
    """Elemento analizable"""
    selector: ElementSelector
    element_type: ElementType
    content_preview: str
    stability: ElementStability
    testable_properties: List[str]
    priority_score: int = Field(..., ge=0, le=100)

class PageAnalysisResponse(BaseModel):
    """Response de análisis de página"""
    url: str
    title: str
    elements: List[AnalyzableElement]
    page_info: Dict[str, Any]
    recommendations: List[str]

# ===== GTM INTEGRATION =====

class GTMExperimentResponse(BaseModel):
    """Response para GTM"""
    experiment_id: str
    name: str
    experiment_type: str
    
    # Fase 1
    arms: Optional[List[Dict[str, Any]]] = None
    
    # Fase 2
    elements: Optional[List[Dict[str, Any]]] = None
    targeting: Optional[Dict[str, Any]] = None

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
    if not all(c.isalnum() or c in '-_.' for c in user_id):
        raise ValidationError("User ID contains invalid characters")
    return user_id.strip()

def validate_conversion_value(value: float) -> float:
    """Validate conversion value"""
    if value < 0:
        raise ValidationError("Conversion value cannot be negative")
    if value > 1000000:
        raise ValidationError("Conversion value too large")
    return value
