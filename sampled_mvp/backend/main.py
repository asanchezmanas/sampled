# backend/main.py
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from pathlib import Path

from models import *
from database import DatabaseManager
from auth import AuthManager
from thompson import ThompsonSamplingManager
from utils import Logger

# Initialize
app = FastAPI(
    title="MAB System MVP",
    description="Multi-Armed Bandit System for A/B Testing",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core managers (singletons)
db = DatabaseManager()
auth_manager = AuthManager()
ts_manager = ThompsonSamplingManager(db)
logger = Logger()
security = HTTPBearer()

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency: Get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    user_id = auth_manager.verify_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    return user_id

# ===== FRONTEND ROUTES =====

@app.get("/")
async def dashboard():
    return FileResponse("static/frontend/index.html")

@app.get("/login")
async def login_page():
    return FileResponse("static/frontend/login.html")

@app.get("/experiment")
async def experiment_page():
    return FileResponse("static/frontend/experiment.html")

@app.get("/analytics")
async def analytics_page():
    return FileResponse("static/frontend/analytics.html")

# ===== AUTH API =====

@app.post("/api/auth/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    try:
        user_id = await db.create_user(
            email=request.email,
            password_hash=auth_manager.hash_password(request.password),
            name=request.name
        )
        
        token = auth_manager.create_token(user_id)
        
        logger.info(f"User registered: {request.email}")
        return AuthResponse(token=token, user_id=user_id)
        
    except Exception as e:
        if "duplicate key" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@app.post("/api/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    try:
        user = await db.get_user_by_email(request.email)
        
        if not user or not auth_manager.verify_password(request.password, user['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        token = auth_manager.create_token(user['id'])
        
        logger.info(f"User logged in: {request.email}")
        return AuthResponse(token=token, user_id=user['id'])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

# ===== EXPERIMENTS API =====

@app.get("/api/experiments", response_model=List[ExperimentResponse])
async def get_experiments(user_id: str = Depends(get_current_user)):
    try:
        experiments = await db.get_user_experiments(user_id)
        return [ExperimentResponse(**exp) for exp in experiments]
    except Exception as e:
        logger.error(f"Failed to fetch experiments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch experiments"
        )

@app.post("/api/experiments", response_model=CreateExperimentResponse)
async def create_experiment(
    request: CreateExperimentRequest, 
    user_id: str = Depends(get_current_user)
):
    try:
        experiment_id = await db.create_experiment(
            user_id=user_id,
            name=request.name,
            description=request.description,
            config=request.config
        )
        
        # Create arms
        arm_ids = []
        for arm_data in request.arms:
            arm_id = await db.create_arm(
                experiment_id=experiment_id,
                name=arm_data.name,
                description=arm_data.description,
                content=arm_data.content
            )
            arm_ids.append(arm_id)
        
        logger.info(f"Experiment created: {experiment_id} with {len(arm_ids)} arms")
        
        return CreateExperimentResponse(
            experiment_id=experiment_id,
            arm_ids=arm_ids
        )
        
    except Exception as e:
        logger.error(f"Failed to create experiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create experiment"
        )

@app.get("/api/experiments/{experiment_id}", response_model=ExperimentDetailResponse)
async def get_experiment(
    experiment_id: str, 
    user_id: str = Depends(get_current_user)
):
    try:
        experiment = await db.get_experiment_with_arms(experiment_id, user_id)
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        return ExperimentDetailResponse(**experiment)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch experiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch experiment"
        )

@app.post("/api/experiments/{experiment_id}/start")
async def start_experiment(
    experiment_id: str, 
    user_id: str = Depends(get_current_user)
):
    try:
        await db.update_experiment_status(experiment_id, user_id, "active")
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
    try:
        await db.update_experiment_status(experiment_id, user_id, "paused")
        logger.info(f"Experiment paused: {experiment_id}")
        return {"status": "success", "message": "Experiment paused"}
        
    except Exception as e:
        logger.error(f"Failed to pause experiment: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to pause experiment"
        )

# ===== ASSIGNMENT API (FOR GTM) =====

@app.post("/api/experiments/{experiment_id}/assign", response_model=AssignmentResponse)
async def assign_user(experiment_id: str, request: AssignmentRequest):
    """Public endpoint for GTM integration (no auth required)"""
    try:
        # Get experiment
        experiment = await db.get_experiment_public(experiment_id)
        if not experiment or experiment['status'] != 'active':
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found or not active"
            )
        
        # Check if user already assigned
        existing = await db.get_user_assignment(experiment_id, request.user_id)
        if existing:
            arm_content = await db.get_arm_content(existing['arm_id'])
            return AssignmentResponse(
                arm_id=existing['arm_id'],
                content=arm_content,
                assignment_id=existing['id'],
                new_assignment=False
            )
        
        # Get arms for Thompson Sampling
        arms = await db.get_experiment_arms_with_stats(experiment_id)
        if not arms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No arms available for assignment"
            )
        
        # Select arm using Thompson Sampling
        selected_arm_id = ts_manager.select_arm(arms)
        
        # Create assignment
        assignment_id = await db.create_assignment(
            experiment_id=experiment_id,
            arm_id=selected_arm_id,
            user_id=request.user_id,
            session_id=request.session_id,
            context=request.context
        )
        
        # Update arm assignment count
        await db.increment_arm_assignments(selected_arm_id)
        
        # Get arm content
        arm_content = await db.get_arm_content(selected_arm_id)
        
        logger.info(f"User assigned: {request.user_id} to arm {selected_arm_id}")
        
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
async def record_conversion(experiment_id: str, request: ConversionRequest):
    """Public endpoint for conversion tracking (no auth required)"""
    try:
        # Find assignment
        assignment = await db.get_user_assignment(experiment_id, request.user_id)
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No assignment found for user"
            )
        
        # Record conversion
        await db.record_conversion(
            assignment_id=assignment['id'],
            conversion_value=request.value,
            metadata=request.metadata
        )
        
        # Update arm statistics (Thompson Sampling)
        await db.increment_arm_conversions(assignment['arm_id'])
        await ts_manager.update_arm_success(assignment['arm_id'])
        
        logger.info(f"Conversion recorded: {request.user_id}, value: {request.value}")
        
        return {"status": "success", "message": "Conversion recorded"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Conversion recording failed"
        )

# ===== ANALYTICS API =====

@app.get("/api/experiments/{experiment_id}/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    experiment_id: str, 
    user_id: str = Depends(get_current_user)
):
    try:
        # Get experiment with arms and stats
        experiment = await db.get_experiment_analytics(experiment_id, user_id)
        if not experiment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment not found"
            )
        
        # Get detailed statistics
        arms_data = experiment['arms']
        
        # Perform Bayesian analysis
        if len(arms_data) >= 2 and any(arm['assignments'] > 0 for arm in arms_data):
            bayesian_analysis = ts_manager.get_bayesian_analysis(arms_data)
        else:
            bayesian_analysis = {
                "message": "Insufficient data for analysis",
                "min_samples_needed": 30
            }
        
        # Calculate summary metrics
        summary = {
            "total_users": sum(arm['assignments'] for arm in arms_data),
            "total_conversions": sum(arm['conversions'] for arm in arms_data),
            "overall_conversion_rate": 0,
            "best_performing_arm": None,
            "confidence_level": 0
        }
        
        if summary["total_users"] > 0:
            summary["overall_conversion_rate"] = summary["total_conversions"] / summary["total_users"]
            
            # Find best performing arm
            best_arm = max(arms_data, key=lambda x: x['conversion_rate'] if x['assignments'] > 0 else 0)
            summary["best_performing_arm"] = {
                "arm_id": best_arm['id'],
                "name": best_arm['name'],
                "conversion_rate": best_arm['conversion_rate']
            }
            
            if 'prob_best' in bayesian_analysis:
                summary["confidence_level"] = max(bayesian_analysis['prob_best'].values())
        
        return AnalyticsResponse(
            experiment_id=experiment_id,
            experiment_name=experiment['name'],
            status=experiment['status'],
            created_at=experiment['created_at'],
            arms=arms_data,
            summary=summary,
            bayesian_analysis=bayesian_analysis
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate analytics"
        )

# ===== GTM INTEGRATION =====

@app.get("/gtm/experiments", response_model=List[GTMExperimentResponse])
async def get_gtm_experiments(domain: str = None):
    """Public endpoint for GTM script to get active experiments"""
    try:
        experiments = await db.get_active_experiments_for_domain(domain)
        
        gtm_experiments = []
        for exp in experiments:
            arms = await db.get_experiment_arms_with_stats(exp['id'])
            
            gtm_experiments.append(GTMExperimentResponse(
                experiment_id=exp['id'],
                name=exp['name'],
                arms=[
                    GTMArmData(
                        arm_id=arm['id'],
                        name=arm['name'],
                        content=arm['content']
                    ) for arm in arms
                ],
                auto_conversion_selectors=exp['config'].get('conversion_selectors', [])
            ))
        
        return gtm_experiments
        
    except Exception as e:
        logger.error(f"GTM experiments fetch failed: {str(e)}")
        return []

# ===== HEALTH CHECK =====

@app.get("/health")
async def health_check():
    try:
        # Check database
        db_healthy = await db.health_check()
        
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "ok" if db_healthy else "error",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ===== STARTUP/SHUTDOWN =====

@app.on_event("startup")
async def startup():
    await db.initialize()
    logger.info("MAB System started")

@app.on_event("shutdown")
async def shutdown():
    await db.close()
    logger.info("MAB System shutdown")

# ===== MAIN =====

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=os.environ.get("ENV") == "development"
    )