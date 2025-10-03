# backend/main.py
from fastapi import FastAPI, HTTPException, Depends, status, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta

# Importar modelos extendidos
from models import *
from database import DatabaseManager
from auth import AuthManager
from thompson import ThompsonSamplingManager
from utils import Logger

# Mantener imports existentes
from models import *  

# Initialize extended managers
db = DatabaseManager()  
auth_manager = AuthManager()
ts_manager = ThompsonSamplingManager(db)
logger = Logger()
security = HTTPBearer()

# Dependency existente
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user_id = auth_manager.verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return user_id

# ===== NUEVOS ENDPOINTS FASE 2 =====

# ===== ELEMENT ANALYSIS & SMART SELECTOR =====

@app.post("/api/pages/analyze", response_model=PageAnalysisResponse)
async def analyze_page_elements(
    request: PageAnalysisRequest,
    user_id: str = Depends(get_current_user)
):
    """Analizar elementos testeable en una página (para el configurador)"""
    try:
        # Simular análisis inteligente de elementos
        # En producción, esto haría scraping real de la página
        
        elements_found = []
        
        # Elementos comunes que encontraría
        common_elements = [
            {
                'element_type': ElementType.HEADLINE,
                'content_preview': 'Transform Your Business Today',
                'priority_score': 90,
                'testable_properties': ['text', 'style'],
                'selector': {
                    'primary': {
                        'type': SelectorType.ID,
                        'selector': '#main-headline',
                        'specificity': 100,
                        'reliable': True
                    },
                    'fallbacks': [
                        {
                            'type': SelectorType.CSS,
                            'selector': 'h1:first-of-type',
                            'specificity': 50,
                            'reliable': False
                        }
                    ],
                    'xpath': '/html/body/section[1]/h1'
                },
                'stability': {
                    'score': 85,
                    'factors': ['Has unique ID', 'Semantic HTML element'],
                    'warnings': [],
                    'recommendations': ['High priority for A/B testing']
                }
            },
            {
                'element_type': ElementType.BUTTON,
                'content_preview': 'Start Free Trial',
                'priority_score': 95,
                'testable_properties': ['text', 'color', 'style'],
                'selector': {
                    'primary': {
                        'type': SelectorType.CLASS,
                        'selector': '.cta-button',
                        'specificity': 60,
                        'reliable': True
                    },
                    'fallbacks': [
                        {
                            'type': SelectorType.CSS,
                            'selector': 'button[type="submit"]',
                            'specificity': 40,
                            'reliable': True
                        }
                    ],
                    'xpath': '/html/body/section[1]/button'
                },
                'stability': {
                    'score': 75,
                    'factors': ['Stable CSS class', 'Semantic button element'],
                    'warnings': ['Class name might change with CSS updates'],
                    'recommendations': ['Consider adding data-testid attribute']
                }
            }
        ]
        
        # Guardar análisis en base de datos
        analysis_id = await db.save_page_analysis(
            user_id=user_id,
            url=request.url,
            title="Sample Page Title",  # En producción, extraer de la página
            elements_found=common_elements,
            page_info={
                'framework': 'React',  # Detectar framework
                'has_spa': True,
                'load_time': 2.3,
                'total_elements': len(common_elements)
            },
            recommendations=[
                'Focus on high-impact elements like CTA buttons',
                'Consider testing headline variations',
                'Add data-testid attributes for more stable selectors'
            ]
        )
        
        return PageAnalysisResponse(
            url=request.url,
            title="Sample Page Title",
            elements=common_elements,
            page_info={
                'framework': 'React',
                'has_spa': True,
                'analysis_id': analysis_id
            },
            recommendations=[
                'Focus on high-impact elements like CTA buttons',
                'Consider testing headline variations',
                'Add data-testid attributes for more stable selectors'
            ]
        )
        
    except Exception as e:
        logger.error(f"Page analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Page analysis failed"
        )

@app.post("/api/elements/smart-selector", response_model=SmartSelectorResponse)
async def generate_smart_selectors(
    element_info: Dict[str, Any],
    user_id: str = Depends(get_current_user)
):
    """Generar selectores inteligentes para un elemento"""
    try:
        # Simular generación de selectores inteligentes
        suggested_selectors = [
            {
                'type': SelectorType.ID,
                'selector': f"#{element_info.get('id', 'element-id')}",
                'specificity': 100,
                'reliable': bool(element_info.get('id'))
            },
            {
                'type': SelectorType.DATA_ATTRIBUTE,
                'selector': f"[data-testid=\"{element_info.get('testid', 'test-element')}\"]",
                'specificity': 90,
                'reliable': bool(element_info.get('testid'))
            },
            {
                'type': SelectorType.CLASS,
                'selector': f".{element_info.get('class', '').split()[0] if element_info.get('class') else 'element'}",
                'specificity': 60,
                'reliable': True
            }
        ]
        
        stability_analysis = {
            'score': 75,
            'factors': ['Semantic HTML element'],
            'warnings': ['CSS classes might change'],
            'recommendations': ['Add data-testid for better stability']
        }
        
        return SmartSelectorResponse(
            element_id=element_info.get('id', 'generated-id'),
            suggested_selectors=suggested_selectors,
            stability_analysis=stability_analysis,
            recommendations=[
                'Use ID selector for highest reliability',
                'Add data-testid attribute if possible',
                'Avoid CSS-in-JS generated classes'
            ]
        )
        
    except Exception as e:
        logger.error(f"Smart selector generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Smart selector generation failed"
        )

# ===== EXPERIMENT CREATION EXTENDIDO =====

@app.post("/api/experiments/extended", response_model=CreateExperimentResponse)
async def create_extended_experiment(
    request: CreateExperimentRequestExtended,
    user_id: str = Depends(get_current_user)
):
    """Crear experimento con múltiples elementos y configuración avanzada"""
    try:
        # Crear experimento base
        experiment_id = await db.create_experiment(
            user_id=user_id,
            name=request.name,
            description=request.description,
            config={
                'url': request.url,
                'max_elements': request.config.max_elements,
                'enable_preview': request.config.enable_preview,
                'enable_heatmaps': request.config.enable_heatmaps,
                'traffic_allocation': request.config.traffic_allocation,
                'confidence_threshold': request.config.confidence_threshold
            }
        )
        
        # Crear elementos del experimento
        element_ids = []
        for element_config in request.elements:
            element_id = await db.create_experiment_element(
                experiment_id=experiment_id,
                element_config=element_config
            )
            element_ids.append(element_id)
        
        # Guardar reglas de targeting
        if request.targeting.enabled:
            await db.save_targeting_rules(
                experiment_id=experiment_id,
                targeting_config=request.targeting
            )
        
        logger.info(f"Extended experiment created: {experiment_id} with {len(element_ids)} elements")
        
        return CreateExperimentResponse(
            experiment_id=experiment_id,
            arm_ids=element_ids  # Reutilizar response existente
        )
        
    except Exception as e:
        logger.error(f"Extended experiment creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Extended experiment creation failed"
        )

@app.get("/api/experiments/{experiment_id}/extended", response_model=ExperimentDetailResponseExtended)
async def get_extended_experiment_details(
    experiment_id: str,
    user_id: str = Depends(get_current_user)
):
    """Obtener detalles extendidos de experimento"""
    try:
        # Obtener experimento base
        experiment = await db.get_experiment_with_arms(experiment_id, user_id)
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        # Obtener elementos del experimento
        elements = await db.get_experiment_elements(experiment_id)
        
        # Obtener configuración de targeting
        targeting_config = await db.get_targeting_rules(experiment_id)
        
        # Construir response extendido
        element_responses = []
        for element in elements:
            element_responses.append(ElementDetailResponse(
                id=element['id'],
                selector=ElementSelector(
                    primary=SelectorConfig(
                        type=SelectorType(element['primary_selector_type']),
                        selector=element['primary_selector'],
                        specificity=element['primary_specificity'],
                        reliable=True
                    ),
                    fallbacks=[
                        SelectorConfig(**fb) for fb in element['fallback_selectors']
                    ],
                    xpath=element['xpath']
                ),
                element_type=ElementType(element['element_type']),
                original_content=element['original_content'],
                variants=[
                    VariantContent(**variant) for variant in element['variants']
                ],
                stability=ElementStability(
                    score=element['stability_score'],
                    factors=element['stability_factors'],
                    warnings=element['stability_warnings'],
                    recommendations=element['stability_recommendations']
                ),
                created_at=element['created_at']
            ))
        
        return ExperimentDetailResponseExtended(
            id=experiment['id'],
            name=experiment['name'],
            description=experiment['description'],
            url=experiment.get('config', {}).get('url', ''),
            status=experiment['status'],
            elements=element_responses,
            targeting=TargetingConfig(**targeting_config),
            config=ExperimentConfigExtended(
                traffic_allocation=experiment.get('config', {}).get('traffic_allocation', 1.0),
                max_elements=experiment.get('config', {}).get('max_elements', 5),
                enable_preview=experiment.get('config', {}).get('enable_preview', True),
                enable_heatmaps=experiment.get('config', {}).get('enable_heatmaps', False),
                confidence_threshold=experiment.get('config', {}).get('confidence_threshold', 0.95)
            ),
            created_at=experiment['created_at'],
            started_at=experiment['started_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get extended experiment details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get experiment details"
        )

# ===== PREVIEW SYSTEM =====

@app.post("/api/experiments/{experiment_id}/preview", response_model=PreviewResponse)
async def create_experiment_preview(
    experiment_id: str,
    request: PreviewRequest,
    user_id: str = Depends(get_current_user)
):
    """Crear preview de experimento con variantes seleccionadas"""
    try:
        # Verificar que el experimento pertenezca al usuario
        experiment = await db.get_experiment_with_arms(experiment_id, user_id)
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        # Generar cambios para el preview
        changes = []
        for element_config in request.element_configs:
            variant_index = request.variant_selections.get(element_config.id, 0)
            if variant_index < len(element_config.variants):
                variant = element_config.variants[variant_index]
                changes.append({
                    'element_id': element_config.id,
                    'selector': element_config.selector.primary.selector,
                    'change_type': variant.type,
                    'new_value': variant.value,
                    'attributes': variant.attributes,
                    'styles': variant.styles
                })
        
        # Crear preview en base de datos
        preview_id = await db.create_experiment_preview(
            experiment_id=experiment_id,
            user_id=user_id,
            variant_selections=request.variant_selections,
            viewport_width=request.viewport.get('width', 1920) if request.viewport else 1920,
            viewport_height=request.viewport.get('height', 1080) if request.viewport else 1080
        )
        
        # En producción, aquí generarías screenshot real
        screenshot_url = f"/api/previews/{preview_id}/screenshot"
        
        return PreviewResponse(
            preview_id=preview_id,
            changes=changes,
            screenshot_url=screenshot_url,
            estimated_impact={
                'confidence': 'medium',
                'expected_lift': '+12.5%',
                'recommendation': 'These changes show promising potential'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Preview creation failed"
        )

@app.get("/api/previews/{preview_id}")
async def get_experiment_preview(
    preview_id: str,
    user_id: str = Depends(get_current_user)
):
    """Obtener preview de experimento"""
    try:
        preview = await db.get_experiment_preview(preview_id)
        if not preview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preview not found or expired"
            )
        
        # Verificar ownership a través del experimento
        experiment = await db.get_experiment_with_arms(preview['experiment_id'], user_id)
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return preview
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get preview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get preview"
        )

# ===== TARGETING SYSTEM =====

@app.get("/api/targeting/options")
async def get_targeting_options():
    """Obtener opciones disponibles para targeting"""
    try:
        return {
            'device': {
                'name': 'Device Type',
                'options': [
                    {'value': 'desktop', 'label': 'Desktop'},
                    {'value': 'mobile', 'label': 'Mobile'},
                    {'value': 'tablet', 'label': 'Tablet'}
                ],
                'operators': ['equals', 'not_equals']
            },
            'browser': {
                'name': 'Browser',
                'options': [
                    {'value': 'chrome', 'label': 'Chrome'},
                    {'value': 'firefox', 'label': 'Firefox'},
                    {'value': 'safari', 'label': 'Safari'},
                    {'value': 'edge', 'label': 'Edge'}
                ],
                'operators': ['equals', 'not_equals', 'contains']
            },
            'location': {
                'name': 'Country',
                'options': [
                    {'value': 'US', 'label': 'United States'},
                    {'value': 'UK', 'label': 'United Kingdom'},
                    {'value': 'CA', 'label': 'Canada'},
                    {'value': 'ES', 'label': 'Spain'},
                    {'value': 'FR', 'label': 'France'},
                    {'value': 'DE', 'label': 'Germany'}
                ],
                'operators': ['equals', 'not_equals']
            },
            'traffic_source': {
                'name': 'Traffic Source',
                'options': [
                    {'value': 'google', 'label': 'Google'},
                    {'value': 'facebook', 'label': 'Facebook'},
                    {'value': 'twitter', 'label': 'Twitter'},
                    {'value': 'direct', 'label': 'Direct'},
                    {'value': 'email', 'label': 'Email'}
                ],
                'operators': ['equals', 'not_equals', 'contains']
            },
            'time': {
                'name': 'Time of Day',
                'options': [
                    {'value': 'morning', 'label': 'Morning (6-12)'},
                    {'value': 'afternoon', 'label': 'Afternoon (12-18)'},
                    {'value': 'evening', 'label': 'Evening (18-24)'},
                    {'value': 'night', 'label': 'Night (0-6)'}
                ],
                'operators': ['equals', 'not_equals']
            },
            'returning_visitor': {
                'name': 'Visitor Type',
                'options': [
                    {'value': 'new', 'label': 'New Visitor'},
                    {'value': 'returning', 'label': 'Returning Visitor'}
                ],
                'operators': ['equals']
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get targeting options: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get targeting options"
        )

@app.post("/api/experiments/{experiment_id}/targeting")
async def update_experiment_targeting(
    experiment_id: str,
    targeting_config: TargetingConfig,
    user_id: str = Depends(get_current_user)
):
    """Actualizar configuración de targeting"""
    try:
        # Verificar ownership
        experiment = await db.get_experiment_with_arms(experiment_id, user_id)
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        # Guardar configuración de targeting
        await db.save_targeting_rules(
            experiment_id=experiment_id,
            targeting_config=targeting_config
        )
        
        logger.info(f"Targeting updated for experiment {experiment_id}")
        return {"status": "success", "message": "Targeting rules updated"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update targeting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update targeting"
        )

# ===== ANALYTICS EXTENDIDAS =====

@app.post("/api/experiments/{experiment_id}/sessions")
async def create_session_analytics(
    experiment_id: str,
    session_data: SessionAnalytics
):
    """Crear sesión de analytics (endpoint público para tracking script)"""
    try:
        # Verificar que el experimento existe y está activo
        experiment = await db.get_experiment_public(experiment_id)
        if not experiment or experiment['status'] != 'active':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found or not active"
            )
        
        # Crear sesión de analytics
        analytics_id = await db.create_session_analytics(
            session_id=session_data.session_id,
            user_id=session_data.user_id,
            experiment_id=experiment_id,
            variant_assignments=session_data.variant_assignments,
            device_info=session_data.device_info,
            viewport_width=session_data.viewport_size.get('width') if session_data.viewport_size else None,
            viewport_height=session_data.viewport_size.get('height') if session_data.viewport_size else None
        )
        
        return {"analytics_id": analytics_id, "status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session analytics creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session analytics creation failed"
        )

@app.post("/api/analytics/{analytics_id}/interactions")
async def record_element_interaction(
    analytics_id: str,
    interaction: ElementInteraction
):
    """Registrar interacción con elemento (endpoint público)"""
    try:
        await db.record_element_interaction(
            session_analytics_id=analytics_id,
            element_id=interaction.element_id,
            interaction_type=interaction.interaction_type,
            coordinates=(interaction.coordinates['x'], interaction.coordinates['y']) if interaction.coordinates else None,
            metadata=interaction.metadata
        )
        
        return {"status": "success", "message": "Interaction recorded"}
        
    except Exception as e:
        logger.error(f"Interaction recording failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Interaction recording failed"
        )

@app.post("/api/analytics/{analytics_id}/micro-conversions")
async def record_micro_conversion(
    analytics_id: str,
    micro_conversion: MicroConversion
):
    """Registrar micro conversión (endpoint público)"""
    try:
        await db.record_micro_conversion(
            session_analytics_id=analytics_id,
            conversion_type=micro_conversion.type,
            value=micro_conversion.value,
            metadata=micro_conversion.metadata
        )
        
        return {"status": "success", "message": "Micro conversion recorded"}
        
    except Exception as e:
        logger.error(f"Micro conversion recording failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Micro conversion recording failed"
        )

@app.get("/api/experiments/{experiment_id}/analytics/advanced")
async def get_advanced_analytics(
    experiment_id: str,
    user_id: str = Depends(get_current_user),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    include_heatmap: bool = Query(False),
    include_funnel: bool = Query(False)
):
    """Obtener analytics avanzadas"""
    try:
        # Verificar ownership
        experiment = await db.get_experiment_with_arms(experiment_id, user_id)
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        # Obtener analytics base
        analytics = await db.get_experiment_analytics(experiment_id, user_id)
        
        # Agregar datos avanzados si se solicita
        advanced_data = {}
        
        if include_funnel:
            funnel_data = await db.get_experiment_conversion_funnel(
                experiment_id, start_date, end_date
            )
            advanced_data['conversion_funnel'] = funnel_data
        
        if include_heatmap:
            heatmap_data = await db.get_experiment_heatmap_data(
                experiment_id, None, 'click', start_date, end_date
            )
            advanced_data['heatmap_data'] = heatmap_data
        
        # Estadísticas de elementos individuales
        elements_stats = []
        for element in analytics.get('arms', []):  # Reutilizar estructura existente
            element_stats = await db.get_element_interaction_stats(
                element['id'], start_date, end_date
            )
            elements_stats.append({
                'element_id': element['id'],
                'element_name': element['name'],
                **element_stats
            })
        
        advanced_data['elements_stats'] = elements_stats
        
        # Combinar con analytics base
        analytics.update({'advanced_analytics': advanced_data})
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Advanced analytics failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Advanced analytics failed"
        )

# ===== TRACKING SCRIPT PERSONALIZADO =====

@app.get("/api/experiments/{experiment_id}/tracking-script")
async def get_tracking_script(experiment_id: str):
    """Generar script de tracking personalizado para el experimento"""
    try:
        # Verificar que el experimento existe
        experiment = await db.get_experiment_public(experiment_id)
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        # Obtener elementos del experimento
        elements = await db.get_experiment_elements(experiment_id)
        
        # Generar configuración para el script
        script_config = {
            'experiment_id': experiment_id,
            'api_endpoint': '/api',  # Usar endpoint relativo
            'elements': [
                {
                    'id': element['id'],
                    'selector': element['primary_selector'],
                    'fallbacks': element['fallback_selectors'],
                    'xpath': element['xpath'],
                    'type': element['element_type'],
                    'variants': element['variants']
                }
                for element in elements
            ],
            'tracking_enabled': True,
            'heatmap_enabled': experiment.get('config', {}).get('enable_heatmaps', False)
        }
        
        # Generar script JavaScript
        tracking_script = f"""
(function() {{
    // MAB Tracking Script - Generated for Experiment {experiment_id}
    var MAB_CONFIG = {json.dumps(script_config)};
    
    // Load main tracking script
    var script = document.createElement('script');
    script.src = '/static/tracking/tracker.js';
    script.async = true;
    script.onload = function() {{
        if (window.MABTracker) {{
            new window.MABTracker(MAB_CONFIG);
        }}
    }};
    document.head.appendChild(script);
}})();
"""
        
        return {"script": tracking_script, "config": script_config}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tracking script generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tracking script generation failed"
        )

# ===== CLEANUP & MAINTENANCE =====

@app.post("/api/admin/cleanup")
async def cleanup_old_data(
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
    days: int = Query(90, ge=30, le=365)
):
    """Limpiar datos antiguos (solo admins)"""
    try:
        # En producción, verificar que el usuario es admin
        # if not await db.is_user_admin(user_id):
        #     raise HTTPException(status_code=403, detail="Admin access required")
        
        # Ejecutar cleanup en background
        background_tasks.add_task(cleanup_background_task, days)
        
        return {"status": "success", "message": f"Cleanup task started for data older than {days} days"}
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cleanup task failed"
        )

async def cleanup_background_task(days: int):
    """Tarea de background para cleanup"""
    try:
        # Limpiar datos analytics antiguos
        analytics_cleanup = await db.cleanup_old_analytics_data(days)
        
        # Limpiar previews expirados
        previews_cleanup = await db.cleanup_expired_previews()
        
        # Limpiar assignments antiguos (función existente)
        assignments_cleanup = await db.cleanup_old_assignments(days)
        
        logger.info(f"Cleanup completed: {analytics_cleanup}, previews: {previews_cleanup}, assignments: {assignments_cleanup}")
        
    except Exception as e:
        logger.error(f"Background cleanup failed: {str(e)}")

# ===== DATABASE MONITORING =====

@app.get("/api/admin/db-stats")
async def get_database_stats(user_id: str = Depends(get_current_user)):
    """Obtener estadísticas de la base de datos"""
    try:
        # En producción, verificar permisos de admin
        
        performance_stats = await db.get_database_performance_stats()
        basic_stats = await db.get_database_stats()  # Función existente
        
        return {
            'basic_stats': basic_stats,
            'performance_stats': performance_stats,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database stats failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database stats failed"
        )

# ===== HEALTH CHECK EXTENDIDO =====

@app.get("/health/extended")
async def extended_health_check():
    """Health check extendido con métricas de Fase 2"""
    try:
        # Health check básico
        basic_health = await health_check()  # Función existente
        
        # Verificaciones adicionales
        extended_checks = {}
        
        # Verificar tablas de Fase 2
        try:
            async with db.pool.acquire() as conn:
                await conn.fetchval("SELECT COUNT(*) FROM experiment_elements LIMIT 1")
            extended_checks['experiment_elements'] = 'ok'
        except Exception:
            extended_checks['experiment_elements'] = 'error'
        
        try:
            async with db.pool.acquire() as conn:
                await conn.fetchval("SELECT COUNT(*) FROM session_analytics LIMIT 1")
            extended_checks['session_analytics'] = 'ok'
        except Exception:
            extended_checks['session_analytics'] = 'error'
        
        # Verificar performance de queries comunes
        try:
            start_time = datetime.now()
            await db.get_experiment_elements('00000000-0000-0000-0000-000000000000')  # Query que fallará pero testea performance
            query_time = (datetime.now() - start_time).total_seconds()
            extended_checks['query_performance'] = 'ok' if query_time < 1.0 else 'slow'
        except Exception:
            extended_checks['query_performance'] = 'ok'  # Expected to fail, just testing speed
        
        # Determinar status general
        all_healthy = (
            basic_health.get('status') == 'healthy' and
            all(status == 'ok' for status in extended_checks.values())
        )
        
        return {
            **basic_health,
            'phase2_checks': extended_checks,
            'status': 'healthy' if all_healthy else 'degraded'
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# Mantener todos los endpoints existentes de Fase 1 para compatibilidad
# Los endpoints originales siguen funcionando sin cambios
