from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.db.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("peoplepulse")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing PeoplePulse Database...")
    init_db()
    logger.info(f"PeoplePulse v{settings.VERSION} running (Demo mode: {settings.DEMO_MODE})")
    yield
    logger.info("PeoplePulse shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    description="Evidence-Based Performance Review and Analytics Platform API",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
register_exception_handlers(app)

# Include API v1 router
app.include_router(api_router)

@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "api_v1": "/api/v1",
    }

