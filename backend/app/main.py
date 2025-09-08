"""
FastAPI main application entry point.
Restaurant SaaS API with Supabase integration.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time

from .config import get_settings
from .db import init_db, close_db, check_db_health
from .auth import AuthenticationError
from .middleware import AuthMiddleware
from .routes import (
    auth_routes,
    restaurant_routes,
    diners_api,
    campaign_routes,
    ai_routes,
    me_routes,
    ai_api,
    campaigns_api,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Restaurant SaaS API...")
    
    # Debug environment variables
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database URL: {settings.database_url}")
    logger.info(f"Database URL Port: {settings.database_url.split(':')[-1].split('/')[0] if ':' in settings.database_url else 'unknown'}")
    logger.info(f"Supabase URL: {settings.supabase_url}")
    
    # Force correct database URL for Railway deployment
    if settings.environment == "production" and "5432" in settings.database_url:
        logger.warning("Detected old port 5432, forcing update to 6543")
        settings.database_url = settings.database_url.replace(":5432/", ":6543/")
        logger.info(f"Updated Database URL: {settings.database_url}")
    
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Restaurant SaaS API...")
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    description="A comprehensive SaaS platform for restaurant management",
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan,
)

# Add CORS middleware first so it wraps all responses
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=["*"],  # Allow all headers for file uploads
    expose_headers=["*"],  # Expose all headers
)

# Add authentication middleware
app.add_middleware(
    AuthMiddleware,
    exclude_paths=[
        "/",
        "/health",
        "/health/detailed",
        "/docs",
        "/redoc", 
        "/openapi.json",
        "/api/v1/docs",
        "/api/v1/redoc",
        "/api/v1/openapi.json",
        "/api/v1/auth/status"  # Allow unauthenticated access to auth status
    ],
    require_auth_paths=[
        "/api/v1/me",
        "/api/v1/campaigns", 
        "/api/v1/diners",
        "/api/v1/ai",
        "/api/v1/auth/me",
        "/api/v1/auth/verify",
        "/api/v1/restaurants",
        "/api/v1/diners-extended",
        "/api/v1/campaigns-extended",
        "/api/v1/ai-extended"
    ]
)

# Add trusted host middleware for production
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.yourdomain.com", "yourdomain.com"]
    )


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    
    # Debug CORS requests
    if request.method == "OPTIONS":
        logger.info(f"CORS preflight request: {request.url.path}")
        logger.info(f"Origin: {request.headers.get('origin')}")
        logger.info(f"Access-Control-Request-Method: {request.headers.get('access-control-request-method')}")
        logger.info(f"Access-Control-Request-Headers: {request.headers.get('access-control-request-headers')}")
    
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Debug CORS response headers
    if request.method == "OPTIONS":
        logger.info(f"CORS response headers: {dict(response.headers)}")
    
    return response


# Global exception handlers
@app.exception_handler(AuthenticationError)
async def auth_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "type": "authentication_error"},
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "type": "server_error"
        }
    )


# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}


@app.get("/health/detailed", tags=["Health"])
async def detailed_health_check():
    """Detailed health check including database connectivity."""
    db_healthy = await check_db_health()
    
    health_status = {
        "status": "healthy" if db_healthy else "unhealthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": settings.environment,
        "checks": {
            "database": "healthy" if db_healthy else "unhealthy",
        }
    }
    
    status_code = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content=health_status
    )


# API Routes
app.include_router(
    auth_routes.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

app.include_router(
    me_routes.router,
    prefix="/api/v1/me",
    tags=["User Profile"]
)

app.include_router(
    diners_api.router,
    prefix="/api/v1/diners",
    tags=["Diners"]
)

app.include_router(
    ai_api.router,
    prefix="/api/v1/ai",
    tags=["AI Features"]
)

app.include_router(
    campaigns_api.router,
    prefix="/api/v1/campaigns",
    tags=["Campaigns"]
)

# Keep original routes for reference/additional functionality
app.include_router(
    restaurant_routes.router,
    prefix="/api/v1/restaurants",
    tags=["Restaurants (Extended)"]
)

app.include_router(
    diners_api.router,
    prefix="/api/v1/diners-extended",
    tags=["Diners (Extended)"]
)

app.include_router(
    campaign_routes.router,
    prefix="/api/v1/campaigns-extended",
    tags=["Campaigns (Extended)"]
)

app.include_router(
    ai_routes.router,
    prefix="/api/v1/ai-extended",
    tags=["AI Features (Extended)"]
)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Restaurant SaaS API",
        "version": "1.0.0",
        "docs": "/api/v1/docs",
        "health": "/health",
        "environment": settings.environment,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
