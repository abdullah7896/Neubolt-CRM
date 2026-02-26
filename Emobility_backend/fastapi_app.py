"""
Neubolt FastAPI Application - Main Entry Point
Electric Rickshaw Management System API v2.0
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging
import sys

from config import settings
from database import init_db, engine
from routers import users, drivers, vehicles, stations, batteries, swaps, complaints, analytics, files
import authentication

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(settings.LOG_FILE)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
# APPLICATION LIFECYCLE MANAGEMENT
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("="  * 60)
    logger.info("Starting Neubolt FastAPI Application")
    logger.info("=" * 60)
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")
        
        # Start MQTT worker
        logger.info("Starting MQTT worker...")
        from workers.mqtt_worker import start_mqtt_worker
        start_mqtt_worker()
        logger.info("MQTT worker started")
        
        # Start GPS TCP server
        logger.info("Starting GPS TCP server...")
        from workers.gps_worker import start_gps_worker
        start_gps_worker()
        logger.info("GPS TCP server started")
        
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise
    
    logger.info("=" * 60)
    logger.info(f"Neubolt API v{settings.APP_VERSION} is ready!")
    logger.info(f"Database: {settings.DB_NAME} on {settings.DB_HOST}")
    logger.info("=" * 60)
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down Neubolt API...")
    engine.dispose()
    logger.info("Shutdown complete")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Complete API for managing electric rickshaws, drivers, stations, battery swaps, and real-time monitoring",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# ============================================================
# MIDDLEWARE CONFIGURATION
# ============================================================

# CORS Middleware
origins = [
    "http://localhost:3000",
    "http://localhost:4200",
    "http://localhost:4201",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:4200",
    "http://127.0.0.1:4201",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# ============================================================
# EXCEPTION HANDLERS
# ============================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "success": False
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.DEBUG else "An error occurred",
            "success": False
        }
    )


# ============================================================
# INCLUDE ROUTERS
# ============================================================

# Authentication
app.include_router(authentication.router, prefix="/neubolt", tags=["Authentication"])

# User Management
app.include_router(users.router, prefix="/neubolt", tags=["Users"])

# Driver Management
app.include_router(drivers.router, prefix="/neubolt", tags=["Drivers"])

# Vehicle Management
app.include_router(vehicles.router, prefix="/neubolt", tags=["Vehicles"])

# Station Management
app.include_router(stations.router, prefix="/neubolt", tags=["Stations"])

# Battery Management
app.include_router(batteries.router, prefix="/neubolt", tags=["Batteries"])

# Swap Operations
app.include_router(swaps.router, prefix="/neubolt", tags=["Swaps"])

# Complaint Management
app.include_router(complaints.router, prefix="/neubolt", tags=["Complaints"])

# Analytics & Reporting
app.include_router(analytics.router, prefix="/neubolt", tags=["Analytics"])

# File Management
app.include_router(files.router, prefix="/neubolt", tags=["Files"])


# ============================================================
# HEALTH CHECK ENDPOINTS
# ============================================================

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API status"""
    return {
        "message": "Neubolt API is running",
        "version": settings.APP_VERSION,
        "status": "healthy"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        from database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "version": settings.APP_VERSION
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
