from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks
from app.services.redis_queue import get_arq_redis # Helper to get ARQ pool

router = APIRouter()

@router.post("/upload")
async def upload_campaign(
    campaign_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
):
    content = await file.read()
    
    # Get Redis Connection
    redis = await get_arq_redis()
    
    # Enqueue the Loader Job
    await redis.enqueue_job(
        'load_campaign_job',
        file_content=content,
        campaign_id=campaign_id,
        tenant_id=str(current_user.tenant_id),
        agent_id="<AGENT_ID_FROM_DB>" # You'd pass this in params
    )
    
    return {"status": "processing", "message": "Campaign started."}