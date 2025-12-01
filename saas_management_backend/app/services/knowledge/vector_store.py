import uuid
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.core.config import settings

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self._ensure_collection()

    def _ensure_collection(self):
        """Create the collection if it doesn't exist."""
        collections = self.client.get_collections()
        exists = any(c.name == settings.QDRANT_COLLECTION_NAME for c in collections.collections)
        
        if not exists:
            # Create with standard OpenAI embedding size (1536 for text-embedding-3-small)
            self.client.create_collection(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
            )
            # Create Index on tenant_id for fast filtering
            self.client.create_payload_index(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                field_name="tenant_id",
                field_schema=models.PayloadSchemaType.KEYWORD
            )

    def upsert_vectors(self, tenant_id: str, vectors: List[List[float]], payloads: List[Dict]):
        """
        Store vectors with metadata.
        """
        points = [
            models.PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "tenant_id": str(tenant_id),
                    **payload
                }
            )
            for vector, payload in zip(vectors, payloads)
        ]
        
        self.client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=points
        )