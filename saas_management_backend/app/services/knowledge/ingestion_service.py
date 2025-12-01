from typing import List
from openai import AsyncOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.services.knowledge.parsers.pdf_parser import PDFParser
from app.services.knowledge.vector_store import VectorStore

class IngestionService:
    def __init__(self):
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.vector_store = VectorStore()
        # Chunking Strategy: 1000 chars with 200 overlap to maintain context across chunks
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    async def process_file(self, tenant_id: str, file, file_name: str):
        # 1. Parse Text
        if file.content_type == "application/pdf":
            raw_text = await PDFParser.parse(file)
        else:
            # Fallback/Todo: Add txt/docx support
            raw_text = (await file.read()).decode('utf-8')

        # 2. Chunk Text
        chunks = self.splitter.split_text(raw_text)
        if not chunks:
            return 0

        # 3. Generate Embeddings (Batch Processing)
        # text-embedding-3-small is cheap and efficient
        response = await self.openai.embeddings.create(
            input=chunks,
            model="text-embedding-3-small"
        )
        embeddings = [data.embedding for data in response.data]

        # 4. Prepare Payloads
        payloads = [{"content": chunk, "source": file_name} for chunk in chunks]

        # 5. Store in Qdrant
        self.vector_store.upsert_vectors(tenant_id, embeddings, payloads)
        
        return len(chunks)