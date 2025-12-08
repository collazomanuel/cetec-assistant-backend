from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pymongo.database import Database

from app.database import get_database


router = APIRouter()



@router.get("/health")
def health_check(db: Database = Depends(get_database)) -> JSONResponse:
    try:
        db.command("ping")
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "database": "connected"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )
