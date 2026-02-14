import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models.database import init_db
from app.api import router as api_router

settings = get_settings()

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Nexus AI Autonomous Trader v2.0")
    await init_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down Nexus AI Autonomous Trader")


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="Agentic Trading Ecosystem powered by LLMs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "shadow_mode": settings.shadow_mode,
    }
