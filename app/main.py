"""
ScenarioWizard API
FastAPI backend for BDD scenario generation
"""

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import structlog
import logging

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

app = FastAPI(
    title="ScenarioWizard API",
    description="BDD Scenario Generation Tool",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {"status": "healthy", "version": "1.0.0"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to ScenarioWizard API",
        "version": "1.0.0",
        "docs": "/docs",
        "docs_json": "/openapi.json"
    }

async def create_tables_on_startup():
    """Create database tables on application startup"""
    from app.core.database_init import create_tables
    try:
        await create_tables()
        logger.info("Database tables created/verified on startup")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")

def create_api_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    from app.api.routes.documents import router as documents_router
    from app.api.routes.scenarios import router as scenarios_router

    # Include routers
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(scenarios_router, prefix="/api/v1")

    # Add startup event to create tables
    @app.on_event("startup")
    async def startup_event():
        await create_tables_on_startup()

    logger.info("FastAPI application created with CORS and document routes")
    return app

# Create the application instance
app = create_api_app()

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting ScenarioWizard API server on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
