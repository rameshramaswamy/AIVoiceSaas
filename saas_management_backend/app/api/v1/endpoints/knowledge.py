from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.models.user import User
from app.services.knowledge.ingestion_service import IngestionService

router = APIRouter()

@router.post("/upload")
async def upload_knowledge_base(
    background_tasks: BackgroundTasks, # Inject
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
):
    # Validate type early
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Only PDF supported currently.")
    
    # Read content into memory immediately (Files close after request ends)
    # Warning: For massive files (>50MB), stream to disk first.
    file_content = await file.read()
    
    # Define Background Job
    async def process_job(content: bytes, filename: str, tenant_id: str):
        # Re-wrap bytes for the parser
        from io import BytesIO
        class MemoryUploadFile:
            def __init__(self, data): self.data = BytesIO(data)
            async def read(self, n=-1): return self.data.read(n)
            async def seek(self, n): return self.data.seek(n)
        
        mem_file = MemoryUploadFile(content)
        service = IngestionService()
        await service.process_file(tenant_id, mem_file, filename)

    # Dispatch
    background_tasks.add_task(process_job, file_content, file.filename, str(current_user.tenant_id))