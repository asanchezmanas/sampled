# backend/main.py
from fastapi import FastAPI, HTTPException, Depends, status, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime

from models import *
from database import DatabaseManager
from auth import AuthManager
from thompson import ThompsonSamplingManager
from utils import Logger

# Initialize
app = FastAPI(title="MAB A/B Testing Platform", version="2.0")
db = DatabaseManager()  
auth_manager = AuthManager()
ts_manager = ThompsonSamplingManager(db)
logger = Logger()
security = HTTPBearer()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup/Shutdown
@app.on_event("startup")
async def startup():
    await db.initialize()
    logger.info("Application started")

@app.on_event("shutdown")
async def shutdown():
    await db.close()
    logger.info("Application shutdown")

# Auth dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user_id = auth_manager.verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return user_id

# ===== AUTH ENDPOINTS =====

@app.post("/api/auth/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register new user"""
    try:
        # Check if user exists
        existing = await db.get_user_by_email(request.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        password_hash = auth_manager.hash_password(request.password)
        user_id = await db.create_user(request.email, password_hash, request.name)
        
        # Generate token
        token = auth_manager.create_token(user_id)
        
        return AuthResponse(token=token, user_id=user_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@app.post("/api/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login user"""
    try:
        user = await db.get_user_by_email(request.email)
        if not user or not auth_manager.verify_password(request.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        token = auth_manager.create_token(str(user['id']))
        return AuthResponse(token=token, user_id=str(user['id']))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

# ===== EXPERIMENT ENDPOINTS (CONSOLIDADOS) =====

@app.post("/api/experiments", response_model=CreateExperimentResponse)
async def create_experiment(
    request: CreateExperimentRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Crear experimento - UNIFICADO
    Soporta tanto experimentos tradicionales (arms) como multi-elemento (elements)
    
    Ejemplos:
    - Tradicional: {"name": "Test", "arms": [{"name": "A", "content": {...}}, ...]}
    - Multi-elemento: {"name": "Test", "url": "...", "elements": [...], "targeting": {...}}
    """
    try:
        # Validar que se proporcione un tipo
        if not request.arms and not request.elements:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either 'arms' (traditional) or 'elements' (multi-element)"
            )
        
        # Crear experimento
        result = await db.create_experiment(
            user_id=user_id,
            name=request.name,
            description=request.description,
            config=request.config,
            url=request.url,
            arms=[{
                'name': arm.name,
                'description': arm.description,
                'content': arm.content
            } for arm in request.arms] if request.arms else None,
            elements=request.elements,
            targeting=request.targeting
        )
        
        experiment_type = 'multi_element' if request.elements else 'traditional'
        
        logger.info(f"Experiment created: {result['experiment_id']} ({experiment_type})")
        
        return CreateExperimentResponse(
            experiment_id=result['experiment_id'],
            arm_ids=result['arm_ids'],
            element_ids=result['element_ids'],
            experiment_type=experiment_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Experiment creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Experiment creation failed: {str(e)}"
        )

@app.get("/api/experiments", response_model=List[ExperimentResponse])
async def get_user_experiments(user_id: str = Depends(get_current_user)):
    """Get all experiments for user"""
    try:
        experiments = await db.get_user_experiments(user_id)
        return [ExperimentResponse(**exp) for exp in experiments]
    except Exception as e:
        logger.error(f"Failed to get experiments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get experiments"
        )

@app.get("/api/experiments/{experiment_id}", response_model=ExperimentDetailResponse)
async def get_experiment_details(
    experiment_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get experiment details - UNIFICADO
    Devuelve arms O elements dependiendo del tipo de experimento
    """
    try:
        experiment = await db.get_experiment(experiment_id, user_id)
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        return ExperimentDetailResponse(
            id=experiment['id'],
            name=experiment['name'],
            description=experiment['description'],
            status=ExperimentStatus(experiment['status']),
            experiment_type=experiment['experiment_type'],
            url=experiment.get('url'),
            config=experiment.get('config', {}),
            created_at=experiment['created_at'],
            started_at=experiment.get('started_at'),
            arms=[ArmData(**arm) for arm in experiment['arms']],
            elements=[ElementData(**el) for el in experiment['elements']],
            targeting=experiment.get('targeting')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get experiment details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get experiment details"
        )

@app.post("/api/experiments/{experiment_id}/start")
async def start_experiment(
    experiment_id: str,
    user_id: str = Depends(get_current_user)
):
    """Start experiment"""
    try:
        await db.update_experiment_status(experiment_id, user_id, 'active')
        logger.info(f"Experiment started: {experiment_id}")
        return {"status": "success", "message": "Experiment started"}
    except Exception as e:
        logger.error(f"Failed to start experiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start experiment"
        )

@app.post("/api/experiments/{experiment_id}/pause")
async def pause_experiment(
    experiment_id: str,
    user_id: str = Depends(get_current_user)
):
    """Pause experiment"""
    try:
        await db.update_experiment_status(experiment_id, user_id, 'paused')
        logger.info(f"Experiment paused: {experiment_id}")
        return {"status": "success", "message": "Experiment paused"}
    except Exception as e:
        logger.error(f"Failed to pause experiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause experiment"
        )

@app.post("/api/experiments/{experiment_id}/complete")
async def complete_experiment(
    experiment_id: str,
    user_id: str = Depends(get_current_user)
):
    """Mark experiment as completed"""
    try:
        await db.update_experiment_status(experiment_id, user_id, 'completed')
        logger.info(f"Experiment completed: {experiment_id}")
        return {"status": "success", "message": "Experiment completed"}
    except Exception as e:
        logger.error(f"Failed to complete experiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete experiment"
        )

# ===== ASSIGNMENT ENDPOINTS =====

@app.get("/api/experiments/{experiment_id}/assign", response_model=AssignmentResponse)
async def assign_user_to_variant(
    experiment_id: str,
    user_id: str = Query(...),
    session_id: Optional[str] = Query(None)
):
    """
    Assign user to variant - UNIFICADO
    Funciona para experimentos tradicionales y multi-elemento
    """
    try:
        # Check existing assignment
        existing = await db.get_user_assignment(experiment_id, user_id)
        if existing:
            arm_content = await db.get_arm_content(existing['arm_id'])
            return AssignmentResponse(
                arm_id=str(existing['arm_id']),
                content=arm_content,
                assignment_id=str(existing['id']),
                new_assignment=False
            )
        
        # Get experiment arms
        arms = await db.get_experiment_arms(experiment_id)
        if not arms:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active arms found for experiment"
            )
        
        # Thompson Sampling selection
        selected_arm_id = ts_manager.select_arm(arms)
        
        # Create assignment
        assignment_id = await db.create_assignment(
            experiment_id=experiment_id,
            arm_id=selected_arm_id,
            user_id=user_id,
            session_id=session_id
        )
        
        # Update arm assignments count
        await db.increment_arm_assignments(selected_arm_id)
        
        # Get arm content
        arm_content = await db.get_arm_content(selected_arm_id)
        
        logger.info(f"User {user_id} assigned to arm {selected_arm_id}")
        
        return AssignmentResponse(
            arm_id=selected_arm_id,
            content=arm_content,
            assignment_id=assignment_id,
            new_assignment=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Assignment failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Assignment failed"
        )

@app.post("/api/experiments/{experiment_id}/convert")
async def record_conversion(
    experiment_id: str,
    request: ConversionRequest
):
    """Record conversion"""
    try:
        # Get assignment
        assignment = await db.get_user_assignment(experiment_id, request.user_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No assignment found for user"
            )
        
        if assignment['converted_at']:
            return {"status": "success", "message": "Conversion already recorded"}
        
        # Record conversion
        await db.record_conversion(
            assignment_id=str(assignment['id']),
            conversion_value=request.value
        )
        
        # Update arm stats
        await db.increment_arm_conversions(assignment['arm_id'])
        
        # Update Thompson Sampling (success)
        await ts_manager.update_arm_success(assignment['arm_id'])
        
        # Update failure for other arms (implicit)
        arms = await db.get_experiment_arms(experiment_id)
        for arm in arms:
            if arm['id'] != assignment['arm_id']:
                await ts_manager.update_arm_failure(arm['id'])
        
        logger.info(f"Conversion recorded for user {request.user_id}")
        
        return {"status": "success", "message": "Conversion recorded"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversion recording failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Conversion recording failed"
        )

# ===== ANALYTICS ENDPOINTS =====

@app.get("/api/experiments/{experiment_id}/analytics", response_model=AnalyticsResponse)
async def get_experiment_analytics(
    experiment_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get experiment analytics - UNIFICADO
    Devuelve analytics apropiados según el tipo de experimento
    """
    try:
        analytics = await db.get_experiment_analytics(experiment_id, user_id)
        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        # Preparar response según tipo
        response_data = {
            'experiment_id': analytics['id'],
            'experiment_name': analytics['name'],
            'experiment_type': analytics['experiment_type'],
            'status': ExperimentStatus(analytics['status']),
            'created_at': analytics['created_at']
        }
        
        # Analytics para experimentos tradicionales (Fase 1)
        if analytics['experiment_type'] == 'traditional' and analytics.get('arms_stats'):
            arms_data = [ArmData(**arm) for arm in analytics['arms_stats']]
            
            # Bayesian analysis
            bayesian = ts_manager.get_bayesian_analysis(analytics['arms_stats'])
            
            # Summary
            total_users = sum(arm['assignments'] for arm in analytics['arms_stats'])
            total_conversions = sum(arm['conversions'] for arm in analytics['arms_stats'])
            
            response_data.update({
                'arms': arms_data,
                'summary': AnalyticsSummary(
                    total_users=total_users,
                    total_conversions=total_conversions,
                    overall_conversion_rate=total_conversions / total_users if total_users > 0 else 0,
                    best_performing_arm=bayesian.get('best_arm'),
                    confidence_level=bayesian.get('best_arm_probability', 0)
                ),
                'bayesian_analysis': BayesianAnalysis(
                    arms=[BayesianArm(
                        arm_id=arm_id,
                        name=next(a['name'] for a in analytics['arms_stats'] if a['id'] == arm_id),
                        probability_best=bayesian['prob_best'].get(arm_id, 0),
                        expected_conversion_rate=bayesian['arm_statistics'][arm_id]['expected_conversion_rate'],
                        credible_interval_lower=bayesian['arm_statistics'][arm_id]['credible_interval_lower'],
                        credible_interval_upper=bayesian['arm_statistics'][arm_id]['credible_interval_upper']
                    ) for arm_id in bayesian.get('prob_best', {}).keys()],
                    recommended_winner=bayesian.get('recommended_winner'),
                    confidence_threshold_met=bayesian.get('confidence_threshold_met', False),
                    continue_experiment=bayesian.get('continue_experiment', True),
                    statistical_power=bayesian.get('statistical_power', 0),
                    message=bayesian.get('recommendations', ['Continue testing'])[0] if bayesian.get('recommendations') else None
                ) if bayesian else None
            })
        
        # Analytics para experimentos multi-elemento (Fase 2)
        elif analytics['experiment_type'] == 'multi_element':
            response_data.update({
                'elements_stats': analytics.get('elements_stats', []),
                'session_stats': {
                    'total_sessions': len(analytics.get('elements_stats', [])),
                    'total_interactions': sum(s.get('total_interactions', 0) for s in analytics.get('elements_stats', []))
                }
            })
        
        return AnalyticsResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analytics failed"
        )

# ===== FASE 2: ADVANCED ENDPOINTS =====

@app.post("/api/pages/analyze", response_model=PageAnalysisResponse)
async def analyze_page_elements(
    request: PageAnalysisRequest,
    user_id: str = Depends(get_current_user)
):
    """Analizar elementos de una página"""
    try:
        # Mock data para MVP - en producción haría scraping real
        mock_elements = [
            AnalyzableElement(
                selector=ElementSelector(
                    primary=SelectorConfig(
                        type=SelectorType.ID,
                        selector="#main-cta",
                        specificity=100,
                        reliable=True
                    ),
                    fallbacks=[
                        SelectorConfig(
                            type=SelectorType.CLASS,
                            selector=".cta-button",
                            specificity=60,
                            reliable=True
                        )
                    ]
                ),
                element_type=ElementType.BUTTON,
                content_preview="Get Started Free",
                stability=ElementStability(
                    score=85,
                    factors=["Has unique ID", "Stable CSS class"],
                    warnings=[],
                    recommendations=["High priority for testing"]
                ),
                testable_properties=["text", "color", "style"],
                priority_score=95
            )
        ]
        
        # Guardar análisis
        await db.save_page_analysis(
            user_id=user_id,
            url=request.url,
            analysis_data={
                'title': 'Sample Page',
                'elements': [{'selector': '#main-cta', 'type': 'button'}],
                'recommendations': ['Test CTA variations']
            }
        )
        
        return PageAnalysisResponse(
            url=request.url,
            title="Sample Page",
            elements=mock_elements,
            page_info={'framework': 'react'},
            recommendations=['Focus on high-impact elements']
        )
        
    except Exception as e:
        logger.error(f"Page analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Page analysis failed"
        )

@app.post("/api/experiments/{experiment_id}/sessions")
async def create_session_analytics(
    experiment_id: str,
    request: SessionAnalyticsRequest
):
    """Crear sesión de analytics (endpoint público para tracking)"""
    try:
        analytics_id = await db.create_session_analytics(
            session_id=request.session_id,
            user_id=request.user_id,
            experiment_id=experiment_id,
            variant_assignments=request.variant_assignments,
            device_info=request.device_info,
            metrics=request.viewport_size
        )
        
        return {"analytics_id": analytics_id, "status": "success"}
        
    except Exception as e:
        logger.error(f"Session creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session creation failed"
        )

@app.post("/api/analytics/{analytics_id}/interactions")
async def record_element_interaction(
    analytics_id: str,
    interaction: ElementInteraction
):
    """Registrar interacción con elemento"""
    try:
        await db.record_element_interaction(
            session_analytics_id=analytics_id,
            element_id=interaction.element_id,
            interaction_type=interaction.interaction_type,
            interaction_data={
                'coordinates': interaction.coordinates,
                'metadata': interaction.metadata
            }
        )
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Interaction recording failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Interaction recording failed"
        )

@app.post("/api/analytics/{analytics_id}/micro-conversions")
async def record_micro_conversion(
    analytics_id: str,
    conversion: MicroConversion
):
    """Registrar micro conversión"""
    try:
        await db.record_micro_conversion(
            session_analytics_id=analytics_id,
            conversion_type=conversion.type,
            value=conversion.value,
            metadata=conversion.metadata
        )
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Micro conversion recording failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Micro conversion recording failed"
        )

@app.post("/api/experiments/{experiment_id}/preview", response_model=PreviewResponse)
async def create_experiment_preview(
    experiment_id: str,
    request: PreviewRequest,
    user_id: str = Depends(get_current_user)
):
    """Crear preview de experimento"""
    try:
        preview_id = await db.create_preview(
            experiment_id=experiment_id,
            user_id=user_id,
            preview_config={
                'variant_selections': request.variant_selections,
                'viewport': request.viewport
            }
        )
        
        return PreviewResponse(
            preview_id=preview_id,
            changes=[],
            screenshot_url=f"/api/previews/{preview_id}/screenshot"
        )
        
    except Exception as e:
        logger.error(f"Preview creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Preview creation failed"
        )

@app.get("/api/targeting/options")
async def get_targeting_options():
    """Obtener opciones de targeting disponibles"""
    return {
        'device': {
            'name': 'Device Type',
            'options': [
                {'value': 'desktop', 'label': 'Desktop'},
                {'value': 'mobile', 'label': 'Mobile'},
                {'value': 'tablet', 'label': 'Tablet'}
            ]
        },
        'browser': {
            'name': 'Browser',
            'options': [
                {'value': 'chrome', 'label': 'Chrome'},
                {'value': 'firefox', 'label': 'Firefox'},
                {'value': 'safari', 'label': 'Safari'}
            ]
        },
        'location': {
            'name': 'Country',
            'options': [
                {'value': 'US', 'label': 'United States'},
                {'value': 'UK', 'label': 'United Kingdom'},
                {'value': 'ES', 'label': 'Spain'}
            ]
        }
    }

# ===== GTM INTEGRATION =====

@app.get("/api/gtm/experiments/{experiment_id}", response_model=GTMExperimentResponse)
async def get_experiment_for_gtm(experiment_id: str):
    """Get experiment data for GTM integration"""
    try:
        async with db.pool.acquire() as conn:
            # Get experiment
            exp = await conn.fetchrow(
                "SELECT id, name, status FROM experiments WHERE id = $1 AND status = 'active'",
                experiment_id
            )
            
            if not exp:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Active experiment not found"
                )
            
            # Get arms
            arms = await conn.fetch(
                "SELECT id, name, content FROM arms WHERE experiment_id = $1 AND is_active = true",
                experiment_id
            )
            
            # Get elements
            elements = await conn.fetch(
                "SELECT id, selector_config, element_type, variants FROM experiment_elements WHERE experiment_id = $1",
                experiment_id
            )
            
            exp_type = 'multi_element' if elements else 'traditional'
            
            return GTMExperimentResponse(
                experiment_id=str(exp['id']),
                name=exp['name'],
                experiment_type=exp_type,
                arms=[{'id': str(a['id']), 'name': a['name'], 'content': a['content']} for a in arms] if arms else None,
                elements=[dict(e) for e in elements] if elements else None
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GTM integration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GTM integration failed"
        )

# ===== ADMIN / MAINTENANCE =====

@app.post("/api/admin/cleanup")
async def cleanup_old_data(
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
    days: int = Query(90, ge=30, le=365)
):
    """Cleanup old data"""
    try:
        async def cleanup_task():
            result = await db.cleanup_old_data(days)
            logger.info(f"Cleanup completed: {result}")
        
        background_tasks.add_task(cleanup_task)
        
        return {"status": "success", "message": f"Cleanup task started for data older than {days} days"}
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cleanup task failed"
        )

@app.get("/api/admin/stats")
async def get_database_stats(user_id: str = Depends(get_current_user)):
    """Get database statistics"""
    try:
        stats = await db.get_database_stats()
        return stats
    except Exception as e:
        logger.error(f"Stats retrieval failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stats retrieval failed"
        )

# ===== HEALTH CHECK =====

@app.get("/health")
async def health_check():
    """Basic health check"""
    try:
        db_healthy = await db.health_check()
        stats = await db.get_database_stats()
        
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "MAB A/B Testing Platform",
        "version": "2.0",
        "status": "running",
        "features": {
            "traditional_ab": True,
            "multi_element": True,
            "thompson_sampling": True,
            "targeting": True,
            "analytics": True
        },
        "docs": "/docs"
    }
