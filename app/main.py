"""FastAPI main application entry point."""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.api.routes import router
from app.config.settings import get_settings
from app.core.logger import setup_logging, get_logger
from app.monitoring.metrics import AUTO_RATE_GAUGE, ESCALATION_RATE_GAUGE, FAQ_COUNT_GAUGE
from app.monitoring.collector import calculate_auto_rate, calculate_escalation_rate, get_faq_count

settings = get_settings()
logger = get_logger(__name__)

# Setup logging
setup_logging(settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    settings.validate_api_keys()
    logger.info("Application starting up", environment=settings.environment)
    yield
    # Shutdown
    logger.info("Application shutting down")


# Create FastAPI app
app = FastAPI(
    title="CS Cost Optimizer Agent",
    description="Customer Service Cost Optimization Agent API",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


@app.get("/health")
async def health_check():
    """Health check endpoint (root level)."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint (real prometheus-client output)."""
    AUTO_RATE_GAUGE.set(calculate_auto_rate())
    ESCALATION_RATE_GAUGE.set(calculate_escalation_rate())
    FAQ_COUNT_GAUGE.set(get_faq_count())
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=(settings.environment == "development"),
    )
