# backend/models.py
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

# ===== ENUMS =====

class ExperimentStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"

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