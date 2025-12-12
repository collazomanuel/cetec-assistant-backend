import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import ensure_indexes, get_database
from app.handlers import register_exception_handlers
from app.routers import health, users, courses, documents, ingestions
from app.services.embedder import create_embedder
from app.services.qdrant import create_qdrant_client, ensure_collection_exists

logger = logging.getLogger(__name__)


def validate_startup_config() -> None:
    """
    Validate critical configuration and service availability at startup.
    Exits with error if validation fails.
    """
    errors = []

    try:
        db = get_database()
        db.command("ping")
    except Exception as e:
        errors.append(f"MongoDB connection failed: {str(e)}")

    if not settings.aws_access_key_id or not settings.aws_secret_access_key:
        errors.append("AWS credentials are not configured")
    if not settings.s3_bucket_name:
        errors.append("S3 bucket name is not configured")

    if not settings.qdrant_url:
        errors.append("Qdrant URL is not configured")

    if settings.embedding_provider == "openai" and not settings.openai_api_key:
        errors.append("OpenAI API key required when embedding_provider is 'openai'")

    if not settings.google_client_id:
        errors.append("Google OAuth credentials are not configured")

    if errors:
        logger.error("Startup validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)

    logger.info("Startup validation passed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to initialize and cleanup resources.
    """
    logger.info("Initializing application services...")

    validate_startup_config()
    ensure_indexes()

    logger.info("Loading embedding model...")
    embedder = create_embedder()
    app.state.embedder = embedder
    logger.info(f"Embedder initialized (dimension: {embedder.get_dimension()})")

    logger.info("Connecting to Qdrant...")
    qdrant_client = create_qdrant_client()
    app.state.qdrant_client = qdrant_client
    logger.info("Qdrant client initialized")

    ensure_collection_exists(qdrant_client, embedder.get_dimension())
    logger.info("Qdrant collection ready")

    logger.info("Application startup complete")

    yield

    logger.info("Shutting down application...")
    logger.info("Application shutdown complete")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health.router)
app.include_router(users.router)
app.include_router(courses.router)
app.include_router(documents.router)
app.include_router(ingestions.router)

