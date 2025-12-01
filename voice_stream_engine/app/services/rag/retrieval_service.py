import json
import hashlib
import redis.asyncio as redis
import logging
from typing import List, Optional
from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from app.core.config import settings

logger = logging.getLogger("rag")

class RetrievalService:
    def __init__(self):
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.qdrant = AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        # Initialize Redis for Caching
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def retrieve(self, query: str, tenant_id: str, limit: int = 3) -> Optional[str]:
        try:
            # 1. Optimization: Check Embedding Cache
            # Hash the query + tenant to create a unique key
            query_hash = hashlib.md5(f"{tenant_id}:{query.strip().lower()}".encode()).hexdigest()
            cache_key = f"rag_embedding:{query_hash}"
            
            cached_vector = await self.redis.get(cache_key)
            
            if cached_vector:
                query_vector = json.loads(cached_vector)
            else:
                # Cache Miss: Generate Embedding
                embedding_resp = await self.openai.embeddings.create(
                    input=query,
                    model="text-embedding-3-small"
                )
                query_vector = embedding_resp.data[0].embedding
                # Cache for 24 hours
                await self.redis.setex(cache_key, 86400, json.dumps(query_vector))

            # 2. Resilience: Circuit Breaker for Vector DB
            try:
                search_result = await asyncio.wait_for(
                    self.qdrant.search(
                        collection_name=settings.QDRANT_COLLECTION_NAME,
                        query_vector=query_vector,
                        limit=limit,
                        query_filter=models.Filter(
                            must=[models.FieldCondition(key="tenant_id", match=models.MatchValue(value=str(tenant_id)))]
                        )
                    ),
                    timeout=1.0 # Fail fast if Qdrant is slow
                )
            except asyncio.TimeoutError:
                logging.error("RAG Timeout: Qdrant took too long.")
                return None
            except Exception as e:
                logging.error(f"RAG Connection Error: {e}")
                return None

            if not search_result:
                return None

            context_blocks = [hit.payload.get("content", "") for hit in search_result if hit.score > 0.45]
            return "\n---\n".join(context_blocks) if context_blocks else None

        except Exception as e:
            logging.error(f"RAG Global Failure: {e}")
            return None # Fail Open (Agent continues without context)