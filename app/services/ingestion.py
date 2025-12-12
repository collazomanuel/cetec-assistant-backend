import asyncio
import io
import uuid
from datetime import datetime, timezone

from pymongo.database import Database
from pymongo.errors import PyMongoError
from qdrant_client import QdrantClient

from app.config import settings
from app.database import get_database
from app.exceptions import (
    IngestionJobNotFoundError,
    IngestionJobError,
    StorageError,
    PDFExtractionError,
    EmbeddingError,
    VectorStoreError,
    CourseNotFoundError
)
from app.models.document import DocumentStatus
from app.models.ingestion import (
    IngestionMode,
    IngestionStatus,
    IngestionJobResponse,
    IngestionJobCreate
)
from app.services.s3 import download_file_from_s3
from app.services.pdf import extract_and_chunk_pdf
from app.services.embedder import BaseEmbedder
from app.services.qdrant import ensure_collection_exists, store_vectors, delete_document_vectors
from app.services.log import log_event


def create_ingestion_job(
    course_code: str,
    job_request: IngestionJobCreate,
    created_by: str,
    db: Database
) -> IngestionJobResponse:
    course = db.courses.find_one({"code": course_code})
    if course is None:
        raise CourseNotFoundError(f"Course with code {course_code} not found")
    
    job_id = str(uuid.uuid4())

    documents = _get_documents_for_ingestion(
        course_code=course_code,
        mode=job_request.mode,
        document_ids=job_request.document_ids,
        db=db
    )

    job_doc = {
        "job_id": job_id,
        "course_code": course_code,
        "status": IngestionStatus.QUEUED.value,
        "mode": job_request.mode.value,
        "document_ids": job_request.document_ids,
        "docs_total": len(documents),
        "docs_done": 0,
        "vectors_created": 0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "created_by": created_by,
        "error_message": None,
        "retry_count": 0,
        "max_retries": job_request.max_retries
    }

    db.ingestion_jobs.insert_one(job_doc)

    log_event(
        "ingestion_job_created",
        level="info",
        user_email=created_by,
        details={
            "job_id": job_id,
            "course_code": course_code,
            "mode": job_request.mode.value,
            "docs_total": len(documents)
        }
    )

    return IngestionJobResponse(
        job_id=job_id,
        course_code=course_code,
        status=IngestionStatus.QUEUED,
        mode=job_request.mode,
        docs_total=len(documents),
        docs_done=0,
        vectors_created=0,
        created_at=job_doc["created_at"],
        updated_at=job_doc["updated_at"],
        created_by=created_by,
        retry_count=0,
        max_retries=job_request.max_retries
    )


def get_ingestion_job(job_id: str, db: Database) -> IngestionJobResponse:
    job = db.ingestion_jobs.find_one({"job_id": job_id})
    if job is None:
        raise IngestionJobNotFoundError(f"Ingestion job {job_id} not found")

    return IngestionJobResponse(
        job_id=job["job_id"],
        course_code=job["course_code"],
        status=IngestionStatus(job["status"]),
        mode=IngestionMode(job["mode"]),
        docs_total=job["docs_total"],
        docs_done=job["docs_done"],
        vectors_created=job["vectors_created"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        created_by=job["created_by"],
        error_message=job.get("error_message"),
        retry_count=job.get("retry_count", 0),
        max_retries=job.get("max_retries", 3)
    )


def list_ingestion_jobs(course_code: str, db: Database) -> list[IngestionJobResponse]:
    jobs = []
    for job in db.ingestion_jobs.find({"course_code": course_code}).sort("created_at", -1):
        jobs.append(IngestionJobResponse(
            job_id=job["job_id"],
            course_code=job["course_code"],
            status=IngestionStatus(job["status"]),
            mode=IngestionMode(job["mode"]),
            docs_total=job["docs_total"],
            docs_done=job["docs_done"],
            vectors_created=job["vectors_created"],
            created_at=job["created_at"],
            updated_at=job["updated_at"],
            created_by=job["created_by"],
            error_message=job.get("error_message"),
            retry_count=job.get("retry_count", 0),
            max_retries=job.get("max_retries", 3)
        ))
    return jobs


def cancel_ingestion_job(job_id: str, user_email: str, db: Database) -> IngestionJobResponse:
    job = db.ingestion_jobs.find_one({"job_id": job_id})
    if job is None:
        raise IngestionJobNotFoundError(f"Ingestion job {job_id} not found")

    if job["status"] in [IngestionStatus.COMPLETED.value, IngestionStatus.FAILED.value, IngestionStatus.CANCELED.value]:
        raise IngestionJobError(f"Cannot cancel job with status {job['status']}")

    db.ingestion_jobs.update_one(
        {"job_id": job_id},
        {
            "$set": {
                "status": IngestionStatus.CANCELED.value,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )

    log_event(
        "ingestion_job_canceled",
        level="info",
        user_email=user_email,
        details={"job_id": job_id}
    )

    return get_ingestion_job(job_id, db)


async def process_ingestion_job(job_id: str, embedder: BaseEmbedder, qdrant_client: QdrantClient) -> None:
    db = get_database()

    try:
        # Atomic update to claim the job - prevents race conditions
        # Only update to RUNNING if status is currently QUEUED
        result = db.ingestion_jobs.update_one(
            {
                "job_id": job_id,
                "status": IngestionStatus.QUEUED.value
            },
            {
                "$set": {
                    "status": IngestionStatus.RUNNING.value,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

        if result.matched_count == 0:
            job = db.ingestion_jobs.find_one({"job_id": job_id})
            if job is None:
                log_event(
                    "ingestion_job_not_found",
                    level="warning",
                    details={"job_id": job_id}
                )
                return

            if job["status"] == IngestionStatus.RUNNING.value:
                log_event(
                    "ingestion_job_already_running",
                    level="info",
                    details={"job_id": job_id, "reason": "Job is already being processed by another worker"}
                )
                return

            if job["status"] == IngestionStatus.CANCELED.value:
                log_event(
                    "ingestion_job_skipped",
                    level="info",
                    details={"job_id": job_id, "reason": "Job was canceled before processing"}
                )
                return

            log_event(
                "ingestion_job_wrong_status",
                level="warning",
                details={"job_id": job_id, "status": job["status"], "reason": "Job is not in QUEUED status"}
            )
            return

        # Fetch the updated job with RUNNING status
        job = db.ingestion_jobs.find_one({"job_id": job_id})
        if job is None:
            log_event(
                "ingestion_job_disappeared",
                level="error",
                details={"job_id": job_id}
            )
            return

        ensure_collection_exists(qdrant_client, embedder.get_dimension())

        documents = _get_documents_for_ingestion(
            course_code=job["course_code"],
            mode=IngestionMode(job["mode"]),
            document_ids=job.get("document_ids"),
            db=db
        )

        for doc in documents:
            if _is_job_canceled(job_id, db):
                return

            try:
                num_vectors = await asyncio.to_thread(
                    _process_document,
                    document=doc,
                    embedder=embedder,
                    qdrant_client=qdrant_client,
                    job_id=job_id,
                    db=db
                )

                db.documents.update_one(
                    {"document_id": doc["document_id"]},
                    {"$set": {"status": DocumentStatus.INGESTED.value}}
                )

                db.ingestion_jobs.update_one(
                    {"job_id": job_id},
                    {
                        "$inc": {"docs_done": 1, "vectors_created": num_vectors},
                        "$set": {"updated_at": datetime.now(timezone.utc)}
                    }
                )

            except (StorageError, PDFExtractionError, EmbeddingError, VectorStoreError, PyMongoError) as e:
                db.documents.update_one(
                    {"document_id": doc["document_id"]},
                    {"$set": {"status": DocumentStatus.FAILED.value}}
                )

                log_event(
                    "ingestion_document_failed",
                    level="warning",
                    details={
                        "job_id": job_id,
                        "document_id": doc["document_id"],
                        "error": str(e),
                        "error_type": type(e).__name__
                    }
                )

        db.ingestion_jobs.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": IngestionStatus.COMPLETED.value,
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

        final_job = db.ingestion_jobs.find_one({"job_id": job_id})
        log_event(
            "ingestion_job_completed",
            level="info",
            details={
                "job_id": job_id,
                "docs_done": final_job.get("docs_done", 0) if final_job else 0,
                "vectors_created": final_job.get("vectors_created", 0) if final_job else 0
            }
        )

    except (StorageError, PDFExtractionError, EmbeddingError, VectorStoreError, PyMongoError, IngestionJobError) as e:
        current_job = db.ingestion_jobs.find_one({"job_id": job_id})
        retry_count = current_job.get("retry_count", 0) if current_job else 0
        max_retries = current_job.get("max_retries", 3) if current_job else 3

        db.ingestion_jobs.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": IngestionStatus.FAILED.value,
                    "error_message": str(e),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )

        log_event(
            "ingestion_job_failed",
            level="warning",
            details={
                "job_id": job_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "retry_count": retry_count,
                "max_retries": max_retries,
                "can_retry": retry_count < max_retries
            }
        )


def _process_document(
    document: dict,
    embedder: BaseEmbedder,
    qdrant_client: QdrantClient,
    job_id: str,
    db: Database
) -> int:
    """
    Process a document by extracting text, generating embeddings, and storing vectors.

    This function ensures proper cleanup on failure:
    - Checks for job cancellation at multiple points
    - Deletes existing vectors before storing new ones
    - If vector storage fails, attempts to clean up any partial state
    - Raises appropriate exceptions on failure
    """
    document_id = document["document_id"]
    s3_key = document["s3_key"]

    try:
        pdf_content = download_file_from_s3(s3_key)
        pdf_file = io.BytesIO(pdf_content)

        if _is_job_canceled(job_id, db):
            raise IngestionJobError("Job was canceled during document processing")

        chunks = extract_and_chunk_pdf(pdf_file, settings.chunk_size, settings.chunk_overlap)

        if not chunks:
            return 0

        if _is_job_canceled(job_id, db):
            raise IngestionJobError("Job was canceled during document processing")

        vectors = embedder.embed_batch(chunks)

        if _is_job_canceled(job_id, db):
            raise IngestionJobError("Job was canceled during document processing")

        delete_document_vectors(qdrant_client, document_id)

        num_vectors = store_vectors(
            client=qdrant_client,
            course_code=document["course_code"],
            document_id=document_id,
            vectors=vectors,
            chunks=chunks,
            metadata={
                "filename": document["filename"],
                "uploaded_by": document["uploaded_by"]
            }
        )

        return num_vectors

    except (StorageError, PDFExtractionError, EmbeddingError, VectorStoreError) as e:
        try:
            delete_document_vectors(qdrant_client, document_id)
        except VectorStoreError as cleanup_error:
            log_event(
                "vector_cleanup_failed",
                level="warning",
                details={
                    "document_id": document_id,
                    "cleanup_error": str(cleanup_error),
                    "original_error": str(e)
                }
            )
        raise


def _get_documents_for_ingestion(
    course_code: str,
    mode: IngestionMode,
    document_ids: list[str] | None,
    db: Database
) -> list[dict]:
    if mode == IngestionMode.NEW:
        query = {
            "course_code": course_code,
            "status": DocumentStatus.UPLOADED.value
        }
    elif mode == IngestionMode.SELECTED:
        if not document_ids:
            raise IngestionJobError("Document IDs required for SELECTED mode")
        query = {
            "course_code": course_code,
            "document_id": {"$in": document_ids}
        }
    elif mode == IngestionMode.ALL:
        query = {"course_code": course_code}
    elif mode == IngestionMode.REINGEST:
        query = {
            "course_code": course_code,
            "status": DocumentStatus.INGESTED.value
        }
    else:
        raise IngestionJobError(f"Unknown ingestion mode: {mode}")

    return list(db.documents.find(query))


def _is_job_canceled(job_id: str, db: Database) -> bool:
    job = db.ingestion_jobs.find_one({"job_id": job_id})
    return job is not None and job["status"] == IngestionStatus.CANCELED.value


def retry_ingestion_job(job_id: str, db: Database) -> IngestionJobResponse:
    job = db.ingestion_jobs.find_one({"job_id": job_id})
    if job is None:
        raise IngestionJobNotFoundError(f"Ingestion job {job_id} not found")

    if job["status"] != IngestionStatus.FAILED.value:
        raise IngestionJobError(f"Can only retry failed jobs. Current status: {job['status']}")

    retry_count = job.get("retry_count", 0)
    max_retries = job.get("max_retries", 3)

    if retry_count >= max_retries:
        raise IngestionJobError(
            f"Job has already been retried {retry_count} times (max: {max_retries})"
        )

    db.ingestion_jobs.update_one(
        {"job_id": job_id},
        {
            "$set": {
                "status": IngestionStatus.QUEUED.value,
                "error_message": None,
                "updated_at": datetime.now(timezone.utc)
            },
            "$inc": {"retry_count": 1}
        }
    )

    log_event(
        "ingestion_job_retried",
        level="info",
        details={
            "job_id": job_id,
            "retry_count": retry_count + 1,
            "max_retries": max_retries
        }
    )

    return get_ingestion_job(job_id, db)
