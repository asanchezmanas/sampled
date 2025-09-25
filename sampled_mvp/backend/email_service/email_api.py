# backend/email_api.py
"""
Email A/B Testing API Endpoints
Se integra con main_extended.py sin breaking changes
"""

from fastapi import HTTPException, Depends, status, BackgroundTasks
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup

# Importar modelos de email
from email_models import *
from models_extended import *

# Importar dependencias existentes (sin cambios)
from main_extended import get_current_user, db, logger

# ===== EMAIL TEMPLATE ANALYSIS =====

@app.post("/api/emails/analyze-template", response_model=EmailAnalysisResponse)
async def analyze_email_template(
    request: EmailAnalysisRequest,
    user_id: str = Depends(get_current_user)
):
    """Analizar template de email para identificar elementos testeable"""
    try:
        # Validar HTML básico
        validation = validate_email_template_html(request.template_html)
        if not validation['valid_html']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid HTML template"
            )
        
        # Extraer elementos testeable
        testable_elements = []
        
        # 1. Subject line (siempre testeable si tiene token)
        if '{{subject_line}}' in request.template_html or '{{subject}}' in request.template_html:
            subject_element = EmailTemplateElement(
                element_type=EmailElementType.SUBJECT_LINE,
                selector=EmailSelector(
                    token="{{subject_line}}",
                    placeholder_pattern=r'\{\{subject[_line]*\}\}'
                ),
                current_content="Subject line placeholder",
                priority=10,
                testing_impact="critical",
                optimization_potential=0.9,
                spam_risk=2,
                character_count=0,
                variant_suggestions=[
                    "Add urgency: 'Last chance'",
                    "Add personalization: Include recipient name",
                    "Use numbers: '5 tips for...'",
                    "Ask a question: 'Ready to...?'"
                ],
                best_practices=[
                    "Keep under 50 characters for mobile",
                    "Avoid spam words like 'free', 'urgent'",
                    "Include brand name for recognition"
                ]
            )
            testable_elements.append(subject_element)
        
        # 2. Parse HTML para otros elementos
        soup = BeautifulSoup(request.template_html, 'html.parser')
        
        # CTA buttons
        cta_buttons = soup.find_all(['a', 'button'], class_=re.compile(r'(cta|button|btn)'))
        for i, button in enumerate(cta_buttons[:3]):  # Max 3 CTAs
            button_text = button.get_text(strip=True) or "Button text"
            testable_elements.append(EmailTemplateElement(
                element_type=EmailElementType.CTA_BUTTON,
                selector=EmailSelector(
                    token=f"{{{{cta_button_{i+1}}}}}",
                    html_selector=f".{button.get('class', ['cta'])[0]}",
                    placeholder_pattern=f"\\{{{{cta_button_{i+1}\\}}}}"
                ),
                current_content=button_text,
                priority=9,
                testing_impact="high",
                optimization_potential=0.8,
                character_count=len(button_text),
                variant_suggestions=[
                    "Use action words: 'Get Started', 'Download Now'",
                    "Add urgency: 'Limited Time'",
                    "Be specific: 'Get Your Free Report'"
                ]
            ))
        
        # Headlines
        headlines = soup.find_all(['h1', 'h2', 'h3'])
        for i, headline in enumerate(headlines[:2]):  # Max 2 headlines
            headline_text = headline.get_text(strip=True) or "Headline text"
            testable_elements.append(EmailTemplateElement(
                element_type=EmailElementType.HEADLINE,
                selector=EmailSelector(
                    token=f"{{{{headline_{i+1}}}}}",
                    html_selector=headline.name,
                    placeholder_pattern=f"\\{{{{headline_{i+1}\\}}}}"
                ),
                current_content=headline_text,
                priority=8,
                testing_impact="high",
                optimization_potential=0.7,
                character_count=len(headline_text),
                variant_suggestions=[
                    "Make it benefit-focused",
                    "Add social proof elements",
                    "Use power words"
                ]
            ))
        
        # Preheader
        preheader = soup.find('span', style=re.compile(r'display:\s*none'))
        if preheader:
            preheader_text = preheader.get_text(strip=True)
            testable_elements.append(EmailTemplateElement(
                element_type=EmailElementType.PREHEADER,
                selector=EmailSelector(
                    token="{{preheader}}",
                    html_selector="span[style*='display:none']",
                    placeholder_pattern=r'\{\{preheader\}\}'
                ),
                current_content=preheader_text,
                priority=7,
                testing_impact="medium",
                optimization_potential=0.6,
                character_count=len(preheader_text),
                variant_suggestions=[
                    "Complement subject line",
                    "Add call to action",
                    "Include key benefit"
                ]
            ))
        
        # Análisis general del template
        word_count = len(request.template_html.split())
        image_count = len(soup.find_all('img'))
        link_count = len(soup.find_all('a'))
        personalization_tokens = extract_personalization_tokens(request.template_html)
        
        # Calcular scores
        template_score = min(100, 60 + len(testable_elements) * 8)
        deliverability_score = 85 - (spam_risk_total := sum(el.spam_risk for el in testable_elements))
        mobile_friendly_score = 90 if validation['responsive_meta'] else 70
        
        # Client compatibility (simulado)
        client_compatibility = {
            EmailClient.GMAIL_WEB: 0.95,
            EmailClient.GMAIL_MOBILE: 0.90,
            EmailClient.OUTLOOK_DESKTOP: 0.85,
            EmailClient.OUTLOOK_WEB: 0.88,
            EmailClient.APPLE_MAIL: 0.92,
        }
        
        # Recommendations
        recommendations = [
            "Focus on testing subject line first - highest impact",
            f"Found {len(testable_elements)} testable elements",
            "Consider testing CTA button text variations"
        ]
        
        if image_count > 5:
            recommendations.append("Consider reducing images for better deliverability")
        
        if not any(el.element_type == EmailElementType.PREHEADER for el in testable_elements):
            recommendations.append("Add preheader text for better preview")
        
        priority_tests = [
            el.selector.token for el in testable_elements 
            if el.testing_impact in ['critical', 'high']
        ]
        
        # Crear análisis completo
        analysis = EmailTemplateAnalysis(
            template_html=request.template_html,
            testable_elements=testable_elements,
            total_elements_found=len(testable_elements),
            high_impact_elements=len([el for el in testable_elements if el.testing_impact in ['critical', 'high']]),
            template_score=template_score,
            deliverability_score=deliverability_score,
            mobile_friendly_score=mobile_friendly_score,
            client_compatibility=client_compatibility,
            word_count=word_count,
            image_count=image_count,
            link_count=link_count,
            personalization_tokens=personalization_tokens,
            recommendations=recommendations,
            priority_tests=priority_tests
        )
        
        logger.info(f"Email template analyzed for user {user_id}: {len(testable_elements)} elements found")
        
        return EmailAnalysisResponse(
            analysis=analysis,
            estimated_analysis_time=2.5,
            success=True,
            warnings=validation.get('issues', [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email template analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template analysis failed"
        )

# ===== EMAIL EXPERIMENT CREATION =====

@app.post("/api/experiments/email", response_model=CreateEmailExperimentResponse)
async def create_email_experiment(
    request: CreateEmailExperimentRequest,
    user_id: str = Depends(get_current_user)
):
    """Crear experimento de A/B testing para email"""
    try:
        config = request.config
        
        # 1. Crear experimento base (reutilizar función existente)
        base_experiment_id = await db.create_experiment(
            user_id=user_id,
            name=config.name,
            description=config.description,
            config={
                'type': 'email',
                'platform': config.email_platform.value,
                'sender_email': config.sender_email,
                'sender_name': config.sender_name,
                'test_percentage': config.test_percentage,
                'confidence_threshold': config.confidence_threshold
            }
        )
        
        # 2. Crear elementos de email (usando tabla experiment_elements existente)
        element_ids = []
        for element_config in config.elements:
            # Convertir EmailElementConfig a ElementConfig base
            base_element = ElementConfig(
                id=element_config.element_id,
                selector=ElementSelector(
                    primary=SelectorConfig(
                        type=SelectorType.CSS,  # Para emails usamos CSS como tipo base
                        selector=element_config.selector.token,
                        specificity=element_config.priority * 10,
                        reliable=True
                    ),
                    fallbacks=[],
                    xpath=None
                ),
                element_type=ElementType.GENERIC,  # Email elements son generic en base
                original_content=element_config.original_content,
                variants=[
                    VariantContent(
                        type=variant.base_content.type,
                        value=variant.base_content.value,
                        attributes=variant.base_content.attributes,
                        styles=variant.base_content.styles
                    ) for variant in element_config.variants
                ],
                stability=ElementStability(
                    score=100 - element_config.spam_risk_score * 5,
                    factors=[f"Email element: {element_config.email_element_type.value}"],
                    warnings=[],
                    recommendations=[]
                )
            )
            
            element_id = await db.create_experiment_element(
                experiment_id=base_experiment_id,
                element_config=base_element
            )
            element_ids.append(element_id)
        
        # 3. Crear registro específico de email
        email_experiment_id = await create_email_experiment_record(
            base_experiment_id=base_experiment_id,
            config=config,
            element_ids=element_ids
        )
        
        # 4. Calcular estimaciones
        estimated_recipients = len(request.recipients) if request.recipients else 1000
        test_group_size = int(estimated_recipients * config.test_percentage)
        
        # 5. Validaciones de deliverability (simuladas)
        deliverability_check = {
            'sender_reputation': 'good',
            'domain_reputation': 'good',
            'spf_record': True,
            'dkim_signature': True,
            'estimated_inbox_rate': 0.92
        }
        
        spam_check = calculate_email_spam_score(
            config.email_template,
            config.elements[0].original_content.get('text', '') if config.elements else ''
        )
        
        # 6. Generar URLs de preview
        variant_preview_urls = {}
        for i, element in enumerate(config.elements):
            for j, variant in enumerate(element.variants):
                variant_key = f"{element.element_id}_variant_{j}"
                variant_preview_urls[variant_key] = f"/api/emails/preview/{email_experiment_id}?variant={variant_key}"
        
        # 7. Enviar emails de test si se solicita
        if request.send_test_emails and request.test_email_addresses:
            await send_test_emails(email_experiment_id, request.test_email_addresses)
        
        logger.info(f"Email experiment created: {email_experiment_id} for user {user_id}")
        
        return CreateEmailExperimentResponse(
            experiment_id=base_experiment_id,
            email_experiment_id=email_experiment_id,
            estimated_recipients=estimated_recipients,
            test_group_size=test_group_size,
            estimated_send_time=config.send_schedule.scheduled_time,
            deliverability_check=deliverability_check,
            spam_check_results=spam_check,
            variant_preview_urls=variant_preview_urls,
            warnings=[
                f"Spam risk score: {spam_check['spam_score']}/10"
            ] if spam_check['spam_score'] > 3 else [],
            recommendations=[
                "Test subject line variations first",
                "Monitor deliverability rates closely",
                "Start with small test group"
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email experiment creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email experiment creation failed"
        )

# ===== EMAIL PREVIEW SYSTEM =====

@app.get("/api/emails/preview/{email_experiment_id}")
async def preview_email_variants(
    email_experiment_id: str,
    variant: str = "control",
    email_client: EmailClient = EmailClient.GMAIL_WEB,
    user_id: str = Depends(get_current_user)
):
    """Generar preview de variante de email"""
    try:
        # Obtener experimento de email
        email_experiment = await get_email_experiment(email_experiment_id, user_id)
        if not email_experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email experiment not found"
            )
        
        # Obtener template y aplicar variante
        template_html = email_experiment['template_html']
        
        # Aplicar cambios de variante
        if variant != "control":
            variant_data = parse_variant_selection(variant)
            template_html = apply_email_variant(template_html, variant_data)
        
        # Adaptar para email client específico
        adapted_html = adapt_for_email_client(template_html, email_client)
        
        # Generar subject line y preheader
        subject_line = extract_subject_from_template(adapted_html) or "Email Subject"
        preheader = extract_preheader_from_template(adapted_html)
        
        # Validaciones para el cliente específico
        content_warnings = []
        compatibility_issues = []
        
        if email_client == EmailClient.OUTLOOK_DESKTOP:
            if 'background-image' in adapted_html:
                compatibility_issues.append("Background images not supported in Outlook Desktop")
            if adapted_html.count('<table') == 0:
                compatibility_issues.append("Use table-based layout for Outlook compatibility")
        
        if len(subject_line) > 50:
            content_warnings.append("Subject line may be truncated on mobile")
        
        return EmailPreviewResponse(
            html_content=adapted_html,
            text_content=convert_html_to_text(adapted_html),
            subject_line=subject_line,
            preheader=preheader,
            email_client=email_client,
            viewport_width=get_client_viewport_width(email_client),
            estimated_render=f"data:image/png;base64,{generate_email_screenshot_placeholder()}",
            content_warnings=content_warnings,
            client_compatibility_issues=compatibility_issues
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email preview generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email preview generation failed"
        )

# ===== EMAIL SENDING =====

@app.post("/api/emails/send/{email_experiment_id}", response_model=EmailSendResponse)
async def send_email_experiment(
    email_experiment_id: str,
    request: EmailSendRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """Enviar experimento de email"""
    try:
@app.post("/api/emails/send/{email_experiment_id}", response_model=EmailSendResponse)
async def send_email_experiment(
    email_experiment_id: str,
    request: EmailSendRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user)
):
    """Enviar experimento de email"""
    try:
        if not request.confirm_send:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must confirm send with confirm_send=true"
            )
        
        # Verificar ownership del experimento
        email_experiment = await get_email_experiment(email_experiment_id, user_id)
        if not email_experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email experiment not found"
            )
        
        # Validaciones pre-envío
        if request.validate_deliverability:
            deliverability_issues = await validate_email_deliverability(email_experiment)
            if deliverability_issues:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Deliverability issues: {', '.join(deliverability_issues)}"
                )
        
        if request.validate_unsubscribe:
            if not has_unsubscribe_link(email_experiment['template_html']):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Template missing unsubscribe link"
                )
        
        # Obtener lista de destinatarios
        recipients = await get_experiment_recipients(email_experiment_id)
        if not recipients:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No recipients found for experiment"
            )
        
        # Crear send record
        send_id = await create_email_send_record(
            email_experiment_id=email_experiment_id,
            total_recipients=len(recipients),
            scheduled_time=request.override_schedule or datetime.utcnow()
        )
        
        # Segmentar destinatarios por variante
        variants_queued = await segment_recipients_by_variant(
            recipients, email_experiment['test_percentage']
        )
        
        # Programar envío en background
        if request.send_test_first:
            # Enviar emails de test primero
            background_tasks.add_task(
                send_test_emails_task,
                email_experiment_id,
                email_experiment['test_emails']
            )
            # Programar envío real después
            background_tasks.add_task(
                send_experiment_emails_task,
                send_id,
                email_experiment_id,
                recipients,
                variants_queued,
                delay_minutes=15
            )
        else:
            # Enviar directamente
            background_tasks.add_task(
                send_experiment_emails_task,
                send_id,
                email_experiment_id, 
                recipients,
                variants_queued
            )
        
        # Configurar webhooks para tracking
        webhook_configured = await setup_email_tracking_webhooks(
            email_experiment['platform'],
            email_experiment_id
        )
        
        # Generar URLs de tracking
        tracking_urls = {
            'opens': f"/api/emails/track/{email_experiment_id}/opens",
            'clicks': f"/api/emails/track/{email_experiment_id}/clicks", 
            'unsubscribes': f"/api/emails/track/{email_experiment_id}/unsubscribes"
        }
        
        logger.info(f"Email experiment {email_experiment_id} queued for sending to {len(recipients)} recipients")
        
        return EmailSendResponse(
            send_id=send_id,
            experiment_id=request.experiment_id,
            total_queued=len(recipients),
            estimated_delivery_time=30,  # 30 minutos estimado
            variants_queued=variants_queued,
            segments_targeted=[seg['name'] for seg in email_experiment.get('segments', [])],
            tracking_urls=tracking_urls,
            webhook_configured=webhook_configured,
            status="queued"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email experiment send failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email send failed"
        )

# ===== EMAIL ANALYTICS =====

@app.get("/api/emails/{email_experiment_id}/analytics", response_model=EmailExperimentAnalytics)
async def get_email_analytics(
    email_experiment_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    include_segments: bool = True,
    include_clients: bool = True,
    user_id: str = Depends(get_current_user)
):
    """Obtener analytics completas del experimento de email"""
    try:
        # Verificar ownership
        email_experiment = await get_email_experiment(email_experiment_id, user_id)
        if not email_experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email experiment not found"
            )
        
        # Obtener métricas por variante
        variant_performances = []
        
        # Para cada variante del experimento
        for variant in email_experiment['variants']:
            # Obtener métricas básicas
            metrics = await get_email_variant_metrics(
                email_experiment_id, variant['id'], start_date, end_date
            )
            
            # Calcular lift vs control
            lift_over_control = {}
            if variant['id'] != email_experiment['control_variant_id']:
                control_metrics = await get_email_variant_metrics(
                    email_experiment_id, email_experiment['control_variant_id'], start_date, end_date
                )
                lift_over_control = calculate_lift_metrics(metrics, control_metrics)
            
            # Análisis estadístico
            significance_test = await calculate_statistical_significance(
                variant['id'], email_experiment['control_variant_id'], email_experiment_id
            )
            
            variant_performance = EmailVariantPerformance(
                variant_id=variant['id'],
                variant_name=variant['name'],
                element_changes=variant.get('changes', {}),
                metrics=metrics,
                confidence_level=significance_test['confidence_level'],
                p_value=significance_test['p_value'],
                is_statistically_significant=significance_test['is_significant'],
                lift_over_control=lift_over_control
            )
            variant_performances.append(variant_performance)
        
        # Métricas por segmento
        segment_performance = {}
        if include_segments:
            for segment in email_experiment.get('segments', []):
                segment_metrics = await get_email_segment_metrics(
                    email_experiment_id, segment['id'], start_date, end_date
                )
                segment_performance[segment['name']] = segment_metrics
        
        # Métricas por email client
        client_performance = {}
        if include_clients:
            client_metrics = await get_email_client_breakdown(
                email_experiment_id, start_date, end_date
            )
            client_performance = client_metrics
        
        # Selección de ganador
        winner_variant_id = None
        winner_selected_at = None
        
        if email_experiment.get('status') == 'completed':
            winner_analysis = determine_email_winner(
                variant_performances, email_experiment['winner_criteria']
            )
            winner_variant_id = winner_analysis['winner_id']
            winner_selected_at = winner_analysis['selected_at']
        
        # Deliverability y reputación
        deliverability_analysis = await analyze_email_deliverability(email_experiment_id)
        
        # Generar recomendaciones
        recommendations = generate_email_recommendations(
            variant_performances, deliverability_analysis
        )
        
        # Sugerencias para próximos tests
        next_test_suggestions = generate_next_test_suggestions(
            variant_performances, email_experiment
        )
        
        return EmailExperimentAnalytics(
            experiment_id=email_experiment_id,
            experiment_name=email_experiment['name'],
            status=email_experiment['status'],
            started_at=email_experiment['started_at'],
            ended_at=email_experiment.get('ended_at'),
            variants=variant_performances,
            control_variant_id=email_experiment['control_variant_id'],
            total_recipients=email_experiment['total_recipients'],
            test_group_size=email_experiment['test_group_size'],
            winner_variant_id=winner_variant_id,
            winner_selected_at=winner_selected_at,
            segment_performance=segment_performance,
            client_performance=client_performance,
            deliverability_score=deliverability_analysis['score'],
            spam_score=deliverability_analysis['spam_score'],
            reputation_impact=deliverability_analysis['reputation_impact'],
            recommendations=recommendations,
            next_test_suggestions=next_test_suggestions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email analytics failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email analytics failed"
        )

# ===== EMAIL PLATFORM WEBHOOKS =====

@app.post("/api/emails/webhooks/mailgun")
async def mailgun_webhook_handler(request: Request):
    """Webhook handler para eventos de Mailgun"""
    try:
        # Verificar signature de Mailgun
        body = await request.body()
        signature = request.headers.get('X-Mailgun-Signature')
        
        if not verify_mailgun_signature(body, signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Parsear evento
        form_data = await request.form()
        event_data = dict(form_data)
        
        # Crear webhook event record
        webhook_event = WebhookEvent(
            platform=EmailPlatform.MAILGUN,
            event_type=event_data.get('event', 'unknown'),
            timestamp=datetime.fromtimestamp(int(event_data.get('timestamp', 0))),
            message_id=event_data.get('Message-Id', ''),
            recipient_email=event_data.get('recipient', ''),
            event_data=event_data
        )
        
        # Procesar evento
        await process_email_webhook_event(webhook_event)
        
        return {"status": "processed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mailgun webhook processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )

@app.post("/api/emails/webhooks/sendgrid")
async def sendgrid_webhook_handler(request: Request):
    """Webhook handler para eventos de SendGrid"""
    try:
        # SendGrid envía JSON array de eventos
        events = await request.json()
        
        for event_data in events:
            webhook_event = WebhookEvent(
                platform=EmailPlatform.SENDGRID,
                event_type=event_data.get('event', 'unknown'),
                timestamp=datetime.fromtimestamp(event_data.get('timestamp', 0)),
                message_id=event_data.get('sg_message_id', ''),
                recipient_email=event_data.get('email', ''),
                event_data=event_data
            )
            
            await process_email_webhook_event(webhook_event)
        
        return {"status": "processed"}
        
    except Exception as e:
        logger.error(f"SendGrid webhook processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )

# ===== HELPER FUNCTIONS =====

async def create_email_experiment_record(
    base_experiment_id: str,
    config: EmailExperimentConfig,
    element_ids: List[str]
) -> str:
    """Crear registro específico de experimento de email"""
    # En producción, esto guardaria en tabla email_experiments
    # Por ahora simulamos con un ID
    import uuid
    email_exp_id = str(uuid.uuid4())
    
    # Aquí iría la lógica para guardar en database:
    # await db.create_email_experiment_record(...)
    
    logger.info(f"Email experiment record created: {email_exp_id}")
    return email_exp_id

async def get_email_experiment(email_experiment_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Obtener experimento de email"""
    # Simulado - en producción consultaría la database
    return {
        'id': email_experiment_id,
        'name': 'Test Email Campaign',
        'template_html': '<html><body><h1>{{headline}}</h1><a href="#" class="cta">{{cta_text}}</a></body></html>',
        'platform': 'mailgun',
        'test_percentage': 0.1,
        'control_variant_id': 'variant_control',
        'variants': [
            {'id': 'variant_control', 'name': 'Control', 'changes': {}},
            {'id': 'variant_a', 'name': 'Variant A', 'changes': {'headline': 'New Headline'}}
        ],
        'status': 'active',
        'started_at': datetime.utcnow(),
        'total_recipients': 1000,
        'test_group_size': 100,
        'test_emails': ['test@company.com'],
        'segments': []
    }

def apply_email_variant(template_html: str, variant_data: Dict[str, Any]) -> str:
    """Aplicar cambios de variante al template"""
    modified_html = template_html
    
    for token, new_value in variant_data.items():
        pattern = f"{{{{{token}}}}}"
        modified_html = modified_html.replace(pattern, str(new_value))
    
    return modified_html

def adapt_for_email_client(html: str, client: EmailClient) -> str:
    """Adaptar HTML para cliente de email específico"""
    if client == EmailClient.OUTLOOK_DESKTOP:
        # Outlook requiere tables para layout
        html = html.replace('<div class="container">', '<table><tr><td>')
        html = html.replace('</div>', '</td></tr></table>')
    
    elif client == EmailClient.GMAIL_MOBILE:
        # Gmail mobile tiene viewport específico
        html = html.replace('<head>', '<head><meta name="viewport" content="width=device-width, initial-scale=1.0">')
    
    return html

def get_client_viewport_width(client: EmailClient) -> int:
    """Obtener ancho de viewport para cliente"""
    widths = {
        EmailClient.GMAIL_WEB: 600,
        EmailClient.GMAIL_MOBILE: 320,
        EmailClient.OUTLOOK_DESKTOP: 580,
        EmailClient.OUTLOOK_WEB: 600,
        EmailClient.APPLE_MAIL: 600
    }
    return widths.get(client, 600)

def generate_email_screenshot_placeholder() -> str:
    """Generar placeholder de screenshot (base64)"""
    # En producción usaría servicio como Puppeteer o PhantomJS
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

def extract_subject_from_template(html: str) -> Optional[str]:
    """Extraer subject line del template"""
    import re
    
    # Buscar tokens de subject
    subject_patterns = [r'\{\{subject_line\}\}', r'\{\{subject\}\}']
    for pattern in subject_patterns:
        if re.search(pattern, html):
            return "Subject Line Placeholder"
    
    # Buscar en meta tags
    soup = BeautifulSoup(html, 'html.parser')
    subject_meta = soup.find('meta', attrs={'name': 'subject'})
    if subject_meta:
        return subject_meta.get('content')
    
    return None

def extract_preheader_from_template(html: str) -> Optional[str]:
    """Extraer preheader del template"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Buscar span oculto (preheader común)
    preheader = soup.find('span', style=re.compile(r'display:\s*none'))
    if preheader:
        return preheader.get_text(strip=True)
    
    return None

def convert_html_to_text(html: str) -> str:
    """Convertir HTML a texto plano"""
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text(separator='\n', strip=True)

async def get_email_variant_metrics(
    experiment_id: str, 
    variant_id: str, 
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> EmailMetrics:
    """Obtener métricas de una variante específica"""
    # Simulado - en producción consultaría email_sends table
    return EmailMetrics(
        total_sent=500,
        delivered_count=485,
        bounced_count=15,
        opened_count=194,  # ~40% open rate
        clicked_count=48,   # ~10% click rate
        unsubscribed_count=2,
        delivery_rate=0.97,
        open_rate=0.40,
        click_rate=0.096,
        click_to_open_rate=0.247,
        unsubscribe_rate=0.004,
        unique_opens=180,
        unique_clicks=45,
        forwards=5,
        replies=2,
        spam_complaints=1,
        average_time_to_open=45.5,  # 45.5 minutos
        average_time_to_click=125.3,  # 125.3 minutos
        peak_engagement_hour=14  # 2 PM
    )

def calculate_lift_metrics(variant_metrics: EmailMetrics, control_metrics: EmailMetrics) -> Dict[str, float]:
    """Calcular lift de métricas vs control"""
    lifts = {}
    
    if control_metrics.open_rate > 0:
        lifts['open_rate'] = ((variant_metrics.open_rate - control_metrics.open_rate) / control_metrics.open_rate) * 100
    
    if control_metrics.click_rate > 0:
        lifts['click_rate'] = ((variant_metrics.click_rate - control_metrics.click_rate) / control_metrics.click_rate) * 100
    
    if control_metrics.delivery_rate > 0:
        lifts['delivery_rate'] = ((variant_metrics.delivery_rate - control_metrics.delivery_rate) / control_metrics.delivery_rate) * 100
    
    return lifts

async def calculate_statistical_significance(
    variant_id: str, 
    control_id: str, 
    experiment_id: str
) -> Dict[str, Any]:
    """Calcular significancia estadística"""
    # Simulado - en producción usaría test estadístico real
    return {
        'confidence_level': 0.85,
        'p_value': 0.12,
        'is_significant': False,
        'sample_size': 500,
        'min_sample_needed': 1000
    }

def generate_email_recommendations(
    variants: List[EmailVariantPerformance],
    deliverability: Dict[str, Any]
) -> List[str]:
    """Generar recomendaciones basadas en performance"""
    recommendations = []
    
    # Analizar performance
    best_variant = max(variants, key=lambda v: v.metrics.open_rate)
    worst_variant = min(variants, key=lambda v: v.metrics.open_rate)
    
    if best_variant.metrics.open_rate > worst_variant.metrics.open_rate * 1.1:
        recommendations.append(f"'{best_variant.variant_name}' shows {((best_variant.metrics.open_rate / worst_variant.metrics.open_rate - 1) * 100):.1f}% better open rate")
    
    # Deliverability recommendations
    if deliverability.get('score', 100) < 85:
        recommendations.append("Improve sender reputation - consider warming up domain")
    
    # Click rate analysis
    avg_click_rate = sum(v.metrics.click_rate for v in variants) / len(variants)
    if avg_click_rate < 0.05:  # < 5% click rate
        recommendations.append("Consider testing different CTA button text and placement")
    
    return recommendations

def generate_next_test_suggestions(
    variants: List[EmailVariantPerformance],
    experiment: Dict[str, Any]
) -> List[str]:
    """Generar sugerencias para próximos tests"""
    suggestions = []
    
    # Basado en elementos testados
    tested_elements = set()
    for variant in variants:
        tested_elements.update(variant.element_changes.keys())
    
    if 'subject_line' not in tested_elements:
        suggestions.append("Test subject line variations - highest impact element")
    
    if 'send_time' not in tested_elements:
        suggestions.append("Test different send times - may improve open rates")
    
    if 'sender_name' not in tested_elements:
        suggestions.append("Test different sender names for trust building")
    
    # Basado en performance
    best_performer = max(variants, key=lambda v: v.metrics.click_rate)
    if best_performer.metrics.click_rate > 0.08:  # Good click rate
        suggestions.append("Scale winning variant to larger audience")
    
    return suggestions

# Background tasks para envío de emails

async def send_test_emails_task(experiment_id: str, test_emails: List[str]):
    """Enviar emails de test"""
    logger.info(f"Sending test emails for experiment {experiment_id}")
    # Aquí iría la integración real con Mailgun/SendGrid
    await asyncio.sleep(2)  # Simular envío
    logger.info(f"Test emails sent for experiment {experiment_id}")

async def send_experiment_emails_task(
    send_id: str,
    experiment_id: str, 
    recipients: List[Dict],
    variants_queued: Dict[str, int],
    delay_minutes: int = 0
):
    """Enviar emails del experimento"""
    if delay_minutes > 0:
        await asyncio.sleep(delay_minutes * 60)
    
    logger.info(f"Starting email send {send_id} for experiment {experiment_id}")
    # Aquí iría la lógica real de envío masivo
    await asyncio.sleep(10)  # Simular envío masivo
    logger.info(f"Email send {send_id} completed")

async def process_email_webhook_event(event: WebhookEvent):
    """Procesar evento de webhook"""
    logger.info(f"Processing webhook event: {event.event_type} for {event.recipient_email}")
    
    # Aquí se actualizarían las tablas email_sends y email_interactions
    # Ejemplo:
    # await db.update_email_send_status(event.message_id, event.event_type, event.timestamp)
    
    # Trigger real-time analytics update si es necesario
    pass
