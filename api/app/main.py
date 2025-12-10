"""
FastAPI main application.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import jobs, stats, dead_letters, scheduled_jobs

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Distributed Job Queue API",
    description="Production-grade job queue system with retry logic and dead letter management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router)
app.include_router(stats.router)
app.include_router(dead_letters.router)
app.include_router(scheduled_jobs.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Distributed Job Queue",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info("Starting Distributed Job Queue API...")
    logger.info(f"CORS origins: {settings.cors_origins}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down Distributed Job Queue API...")
