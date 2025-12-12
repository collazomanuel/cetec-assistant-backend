import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from app.config import settings
from app.exceptions import VectorStoreError


def create_qdrant_client() -> QdrantClient:
    """
    Factory function to create a Qdrant client instance.

    This function should be called once during application startup
    and the instance should be managed via dependency injection.
    """
    try:
        return QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key
        )
    except Exception as e:
        raise VectorStoreError(f"Failed to connect to Qdrant: {str(e)}")


def ensure_collection_exists(client: QdrantClient, dimension: int) -> None:

    try:
        collections = client.get_collections()
        collection_names = [col.name for col in collections.collections]

        if settings.qdrant_collection_name not in collection_names:
            client.create_collection(
                collection_name=settings.qdrant_collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
            )

            client.create_payload_index(
                collection_name=settings.qdrant_collection_name,
                field_name="course_code",
                field_schema="keyword"
            )

            client.create_payload_index(
                collection_name=settings.qdrant_collection_name,
                field_name="document_id",
                field_schema="keyword"
            )

    except Exception as e:
        raise VectorStoreError(f"Failed to ensure collection exists: {str(e)}")


def store_vectors(
    client: QdrantClient,
    course_code: str,
    document_id: str,
    vectors: list[list[float]],
    chunks: list[str],
    metadata: dict[str, Any] | None = None
) -> int:

    if len(vectors) != len(chunks):
        raise VectorStoreError("Number of vectors must match number of chunks")

    try:
        points = []
        for i, (vector, chunk) in enumerate(zip(vectors, chunks)):
            point_id = str(uuid.uuid4())
            payload = {
                "course_code": course_code,
                "document_id": document_id,
                "chunk_index": i,
                "chunk_text": chunk,
                **(metadata or {})
            }

            points.append(PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            ))

        client.upsert(
            collection_name=settings.qdrant_collection_name,
            points=points
        )

        return len(points)

    except Exception as e:
        raise VectorStoreError(f"Failed to store vectors: {str(e)}")


def delete_document_vectors(client: QdrantClient, document_id: str) -> None:

    try:
        client.delete(
            collection_name=settings.qdrant_collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
        )
    except Exception as e:
        raise VectorStoreError(f"Failed to delete document vectors: {str(e)}")


def search_vectors(
    client: QdrantClient,
    query_vector: list[float],
    course_code: str | None = None,
    limit: int = 10
) -> list[dict[str, Any]]:

    try:
        search_filter = None
        if course_code:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="course_code",
                        match=MatchValue(value=course_code)
                    )
                ]
            )

        results = client.search(
            collection_name=settings.qdrant_collection_name,
            query_vector=query_vector,
            query_filter=search_filter,
            limit=limit
        )

        return [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            }
            for result in results
        ]

    except Exception as e:
        raise VectorStoreError(f"Failed to search vectors: {str(e)}")
