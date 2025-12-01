from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.ratelimit import limiter
from app.api import deps
from app.models.agent import Agent
from app.models.user import User
from app.schemas.agent import AgentCreate, AgentResponse
from app.services.cache_service import CacheService
from fastapi.responses import ORJSONResponse 


router = APIRouter()
cache_service = CacheService()
@router.post("/", dependencies=[Security(deps.get_current_active_user, scopes=["agent:write"])])
async def create_agent(
    agent_in: AgentCreate,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Create a new AI Agent. 
    Enforces tenant isolation by using current_user.tenant_id.
    """
    agent = Agent(
        **agent_in.model_dump(),
        tenant_id=current_user.tenant_id # Force linkage to user's tenant
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent

@router.get("/", response_model=List[AgentResponse])
async def read_agents(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Retrieve agents belonging to the current user's tenant.
    """
    query = select(Agent).where(Agent.tenant_id == current_user.tenant_id).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@limiter.limit("100/minute")
@router.get("/internal/lookup", response_class=ORJSONResponse)
async def lookup_agent_by_number(
    phone_number: str,
    x_internal_key: str = Header(None), # Simple security for internal microservices
    db: AsyncSession = Depends(deps.get_db)
):
    """
    Internal endpoint for Voice Engine to fetch config by phone number.
    """
    # Verify Internal Key (In production, use better service-to-service auth)
    if x_internal_key != "changeme_shared_secret": # Match config
         raise HTTPException(status_code=403, detail="Forbidden")

    # Query
    query = select(Agent).where(Agent.phone_number == phone_number)
    result = await db.execute(query)
    agent = result.scalars().first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found for this number")
        
    return agent

@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    agent_in: AgentUpdate, # Assuming you have a Pydantic schema for Update
    current_user: User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db)
):
    # 1. Fetch Agent
    query = select(Agent).where(Agent.id == agent_id, Agent.tenant_id == current_user.tenant_id)
    result = await db.execute(query)
    agent = result.scalars().first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # 2. Update DB
    update_data = agent_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    # 3. OPTIMIZATION: Invalidate Cache Immediately
    if agent.phone_number:
        await cache_service.invalidate_agent_config(agent.phone_number)

    return agent