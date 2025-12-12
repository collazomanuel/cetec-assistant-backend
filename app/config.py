from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str
    mongodb_database: str
    google_client_id: str
    cors_origins: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    s3_bucket_name: str
    max_file_size: int = 100 * 1024 * 1024

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "course_documents"

    embedding_provider: str = "local"
    openai_api_key: str | None = None
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    chunk_size: int = 1000
    chunk_overlap: int = 150

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("max_file_size")
    @classmethod
    def validate_max_file_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_file_size must be positive")
        if v > 1024 * 1024 * 1024:  # 1GB limit
            raise ValueError("max_file_size cannot exceed 1GB")
        return v

    @field_validator("chunk_size")
    @classmethod
    def validate_chunk_size(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("chunk_size must be positive")
        if v > 100000:  # Reasonable upper limit
            raise ValueError("chunk_size cannot exceed 100,000 characters")
        return v

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v: int) -> int:
        if v < 0:
            raise ValueError("chunk_overlap cannot be negative")
        return v

    def model_post_init(self, __context) -> None:
        """Validate relationships between fields after all fields are set"""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than chunk_size ({self.chunk_size})"
            )


def load_settings() -> Settings:
    return Settings()


settings = load_settings()
