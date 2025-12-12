from abc import ABC, abstractmethod

from app.config import settings
from app.exceptions import EmbeddingError


class BaseEmbedder(ABC):
    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        pass

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        pass


class LocalEmbedder(BaseEmbedder):
    def __init__(self, model_name: str):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except Exception as e:
            raise EmbeddingError(f"Failed to load local embedding model: {str(e)}")

    def embed_text(self, text: str) -> list[float]:
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            raise EmbeddingError(f"Failed to generate embedding: {str(e)}")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            raise EmbeddingError(f"Failed to generate batch embeddings: {str(e)}")

    def get_dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()


class OpenAIEmbedder(BaseEmbedder):
    def __init__(self, api_key: str, model_name: str = "text-embedding-3-small"):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model_name = model_name
            self._dimension = 1536 if "3-small" in model_name else 3072
        except Exception as e:
            raise EmbeddingError(f"Failed to initialize OpenAI client: {str(e)}")

    def embed_text(self, text: str) -> list[float]:
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model_name
            )
            return response.data[0].embedding
        except Exception as e:
            raise EmbeddingError(f"Failed to generate OpenAI embedding: {str(e)}")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model_name
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            raise EmbeddingError(f"Failed to generate OpenAI batch embeddings: {str(e)}")

    def get_dimension(self) -> int:
        return self._dimension


def create_embedder() -> BaseEmbedder:
    """
    Factory function to create an embedder instance based on settings.

    This function should be called once during application startup
    and the instance should be managed via dependency injection.
    """
    if settings.embedding_provider == "openai":
        if not settings.openai_api_key:
            raise EmbeddingError("OpenAI API key is required for OpenAI embeddings")
        return OpenAIEmbedder(
            api_key=settings.openai_api_key,
            model_name=settings.embedding_model
        )
    else:
        return LocalEmbedder(model_name=settings.embedding_model)
