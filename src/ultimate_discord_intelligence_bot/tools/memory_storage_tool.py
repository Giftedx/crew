"""Store transcripts and analysis in a Qdrant vector database."""

from __future__ import annotations

import os
import uuid
from typing import Callable, Dict, Optional

from crewai_tools import BaseTool

try:  # pragma: no cover - optional dependency
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams
except Exception:  # pragma: no cover - used for testing without qdrant
    QdrantClient = None

    class PointStruct:  # type: ignore
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class VectorParams:  # type: ignore
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class Distance:  # type: ignore
        COSINE = "cosine"


class MemoryStorageTool(BaseTool):
    """Persist text and metadata to a Qdrant collection."""

    name: str = "Qdrant Memory Storage Tool"
    description: str = "Stores documents in a Qdrant vector database for later retrieval."

    def __init__(
        self,
        client: Optional[object] = None,
        collection: str | None = None,
        embedding_fn: Optional[Callable[[str], list[float]]] = None,
    ) -> None:
        super().__init__()
        self.collection = collection or os.getenv("QDRANT_COLLECTION", "content")
        self.embedding_fn = embedding_fn or (lambda text: [float(len(text))])
        if client is not None:
            self.client = client
        else:
            if QdrantClient is None:  # pragma: no cover - real client missing
                raise RuntimeError("qdrant-client package is not installed")
            url = os.getenv("QDRANT_URL", "http://localhost:6333")
            api_key = os.getenv("QDRANT_API_KEY")
            self.client = QdrantClient(url=url, api_key=api_key)
        self._ensure_collection()

    def _ensure_collection(self) -> None:  # pragma: no cover - setup
        try:
            self.client.get_collection(self.collection)
        except Exception:
            self.client.recreate_collection(
                self.collection,
                vectors_config=VectorParams(size=1, distance=Distance.COSINE),
            )

    def _run(self, text: str, metadata: Dict) -> Dict:
        try:
            vector = self.embedding_fn(text)
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={**metadata, "text": text},
            )
            self.client.upsert(collection_name=self.collection, points=[point])
            return {"status": "success"}
        except Exception as exc:  # pragma: no cover - network errors
            return {"status": "error", "error": str(exc)}

    # Explicit run wrapper for pipeline compatibility
    def run(self, *args, **kwargs):  # pragma: no cover - thin wrapper
        return self._run(*args, **kwargs)
