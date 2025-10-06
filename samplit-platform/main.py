# main.py

"""
Samplit Platform - Main Application

⚠️  CONFIDENTIAL - Proprietary A/B Testing Platform

This is the main entry point for Samplit's optimization platform.
Algorithm implementations are proprietary trade secrets.

Copyright (c) 2024 Samplit Technologies. All rights reserved.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import time
from typing import Callable

from config.settings import settings
from data_access.database import DatabaseManager
from public_api.routers import (
    auth,
    experiments,
    analytics,
    funnels,
    emails,
    notifications
)

# ============================================
# LOGGING SETUP
# ============================================

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("samplit.main")

# ============================================
# LIFESPAN MANAGEMENT
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    
    Handles startup and shutdown events
    """
    # STARTUP
    logger.info("🚀 Starting Samplit Platform...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Version: {settings.APP_VERSION}")
    
    # Initialize database
    db = DatabaseManager()
    await db.initialize()
    app.state.db = db
    
    logger.info("✅ Database initialized")
    
    # Health check
    if await db.health_check():
        logger.info("✅ Database health check passed")
    else:
        logger.error("❌ Database health check failed")
        raise Exception("Database not healthy")
    
    logger.info("✨ Samplit Platform ready!")
    
    yield
    
    # SHUTDOWN
    logger.info("🛑 Shutting down Samplit Platform...")
    await db.close()
    logger.info("👋 Samplit Platform stopped")

# ============================================
# CREATE APP
# ============================================

app = FastAPI(
    title=settings.APP_NAME,
    description="Intelligent A/B Testing & Optimization Platform",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,  # Hide in production
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None
)

# ============================================
# MIDDLEWARE
# ============================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host (security)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.samplit.com", "samplit.com"]
    )

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable):
    """Add X-Process-Time header to responses"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable):
    """Add security headers"""
    response = await call_next(request)
    
    # NO revelar stack technology
    response.headers["X-Powered-By"] = "Samplit"
    response.headers["Server"] = "Samplit"
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# ============================================
# EXCEPTION HANDLERS
# ============================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    # Don't expose internal errors in production
    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": str(exc)
            }
        )

# ============================================
# INCLUDE ROUTERS
# ============================================

# Auth (Supabase OAuth)
app.include_router(
    auth.router,
    prefix=f"{settings.API_PREFIX}/auth",
    tags=["Authentication"]
)

# Experiments
app.include_router(
    experiments.router,
    prefix=f"{settings.API_PREFIX}/experiments",
    tags=["Experiments"]
)

# Analytics
app.include_router(
    analytics.router,
    prefix=f"{settings.API_PREFIX}/analytics",
    tags=["Analytics"]
)

# Funnels (si está habilitado)
if settings.ENABLE_FUNNEL_OPTIMIZATION:
    app.include_router(
        funnels.router,
        prefix=f"{settings.API_PREFIX}/funnels",
        tags=["Funnels"]
    )

# Emails (si está habilitado)
if settings.ENABLE_EMAIL_OPTIMIZATION:
    app.include_router(
        emails.router,
        prefix=f"{settings.API_PREFIX}/emails",
        tags=["Email Campaigns"]
    )

# Push Notifications (si está habilitado)
if settings.ENABLE_PUSH_OPTIMIZATION:
    app.include_router(
        notifications.router,
        prefix=f"{settings.API_PREFIX}/notifications",
        tags=["Push Notifications"]
    )

# ============================================
# ROOT ENDPOINTS
# ============================================

@app.get("/")
async def root():
    """Root endpoint - public info"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "features": {
            "ab_testing": True,
            "funnel_optimization": settings.ENABLE_FUNNEL_OPTIMIZATION,
            "email_optimization": settings.ENABLE_EMAIL_OPTIMIZATION,
            "push_optimization": settings.ENABLE_PUSH_OPTIMIZATION
        },
        "docs": "/docs" if settings.DEBUG else None
    }

@app.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint
    
    Verifies database connectivity and system status
    """
    db: DatabaseManager = request.app.state.db
    
    try:
        db_healthy = await db.health_check()
        
        return {
            "status": "healthy" if db_healthy else "degraded",
            "database": "connected" if db_healthy else "disconnected",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": "Service unavailable"
            }
        )

@app.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"pong": True}

# ============================================
# ADMIN ENDPOINTS (Protected)
# ============================================

@app.get(f"{settings.API_PREFIX}/system/stats")
async def system_stats(request: Request):
    """
    System statistics
    
    ⚠️  Should be protected in production
    """
    if settings.ENVIRONMENT == "production":
        return {"error": "Endpoint disabled in production"}
    
    db: DatabaseManager = request.app.state.db
    stats = await db.get_database_stats()
    
    return {
        "system": "samplit",
        "version": settings.APP_VERSION,
        "database": stats,
        "features": {
            "funnels": settings.ENABLE_FUNNEL_OPTIMIZATION,
            "emails": settings.ENABLE_EMAIL_OPTIMIZATION,
            "push": settings.ENABLE_PUSH_OPTIMIZATION
        }
    }

# ============================================
# STARTUP MESSAGE
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔═══════════════════════════════════════╗
    ║                                       ║
    ║          SAMPLIT PLATFORM             ║
    ║   Intelligent A/B Testing Engine      ║
    ║                                       ║
    ╚═══════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
