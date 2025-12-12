from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pymongo.database import Database
from qdrant_client import QdrantClient

from app.config import settings
from app.database import get_database
from app.dependencies import get_qdrant_client


router = APIRouter()


@router.get("/health")
async def health_check(
    db: Database = Depends(get_database),
    qdrant_client: QdrantClient = Depends(get_qdrant_client)
) -> JSONResponse:
    """
    Comprehensive health check for all critical services.
    Returns detailed status without exposing sensitive error details in production.
    """
    health_status = {
        "status": "healthy",
        "services": {}
    }
    is_healthy = True

    try:
        db.command("ping")
        health_status["services"]["database"] = "connected"
    except Exception as e:
        health_status["services"]["database"] = "disconnected"
        is_healthy = False

    try:
        qdrant_client.get_collections()
        health_status["services"]["vector_store"] = "connected"
    except Exception as e:
        health_status["services"]["vector_store"] = "disconnected"
        is_healthy = False

    try:
        if settings.embedding_provider == "openai":
            if settings.openai_api_key:
                health_status["services"]["embeddings"] = "configured"
            else:
                health_status["services"]["embeddings"] = "misconfigured"
                is_healthy = False
        else:
            health_status["services"]["embeddings"] = "configured"
    except Exception as e:
        health_status["services"]["embeddings"] = "error"
        is_healthy = False

    if settings.aws_access_key_id and settings.aws_secret_access_key and settings.s3_bucket_name:
        health_status["services"]["storage"] = "configured"
    else:
        health_status["services"]["storage"] = "misconfigured"
        is_healthy = False

    if is_healthy:
        health_status["status"] = "healthy"
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=health_status
        )
    else:
        health_status["status"] = "degraded"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )
