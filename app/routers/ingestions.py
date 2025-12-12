from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from pymongo.database import Database
from qdrant_client import QdrantClient

from app.database import get_database
from app.dependencies import require_professor, require_student, get_embedder, get_qdrant_client
from app.models.user import UserResponse
from app.models.ingestion import IngestionJobCreate, IngestionJobResponse, IngestionJobCancel, IngestionJobRetry
from app.services.embedder import BaseEmbedder
from app.services.ingestion import (
    create_ingestion_job,
    get_ingestion_job,
    list_ingestion_jobs,
    cancel_ingestion_job,
    retry_ingestion_job,
    process_ingestion_job
)
from app.services.log import log_event

router = APIRouter(prefix="/ingestions")


@router.post(
    "/start",
    response_model=IngestionJobResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def start_ingestion(
    job_request: IngestionJobCreate,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database),
    embedder: BaseEmbedder = Depends(get_embedder),
    qdrant_client: QdrantClient = Depends(get_qdrant_client)
) -> IngestionJobResponse:
    job = create_ingestion_job(
        course_code=job_request.course_code,
        job_request=job_request,
        created_by=current_user.email,
        db=db
    )

    background_tasks.add_task(process_ingestion_job, job.job_id, embedder, qdrant_client)

    return job


@router.get("/list", response_model=list[IngestionJobResponse])
async def list_course_ingestions(
    course_code: str = Query(...),
    current_user: UserResponse = Depends(require_student),
    db: Database = Depends(get_database)
) -> list[IngestionJobResponse]:
    jobs = list_ingestion_jobs(course_code, db)

    log_event(
        "ingestion_list_viewed",
        level="info",
        user_email=current_user.email,
        details={"course_code": course_code}
    )

    return jobs


@router.get("/status", response_model=IngestionJobResponse)
async def get_ingestion_status(
    job_id: str = Query(...),
    current_user: UserResponse = Depends(require_student),
    db: Database = Depends(get_database)
) -> IngestionJobResponse:
    job = get_ingestion_job(job_id, db)

    log_event(
        "ingestion_status_viewed",
        level="info",
        user_email=current_user.email,
        details={"job_id": job_id}
    )

    return job


@router.post("/cancel", response_model=IngestionJobResponse)
async def cancel_ingestion(
    cancel_request: IngestionJobCancel,
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database)
) -> IngestionJobResponse:
    job = cancel_ingestion_job(cancel_request.job_id, current_user.email, db)

    return job


@router.post("/retry", response_model=IngestionJobResponse)
async def retry_ingestion(
    retry_request: IngestionJobRetry,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(require_professor),
    db: Database = Depends(get_database),
    embedder: BaseEmbedder = Depends(get_embedder),
    qdrant_client: QdrantClient = Depends(get_qdrant_client)
) -> IngestionJobResponse:
    job = retry_ingestion_job(retry_request.job_id, db)

    background_tasks.add_task(process_ingestion_job, job.job_id, embedder, qdrant_client)

    return job
