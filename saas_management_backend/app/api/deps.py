from typing import Generator, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.schemas.token import TokenPayload
from fastapi import Security
from fastapi.security import SecurityScopes
from sqlalchemy.orm import selectinload

# Points to the login endpoint so Swagger UI works
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenPayload(sub=user_id)
    except JWTError:
        raise credentials_exception
        
    query = select(User).options(selectinload(User.tenant)).where(User.id == token_data.sub)
    
    result = await db.execute(query)
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    security_scopes: SecurityScopes,
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Middleware to check if the user has the required SCOPE for the endpoint.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    user_scopes = security.get_scopes_for_role(current_user.role)
    
    # Check if user has all required scopes for this endpoint
    for scope in security_scopes.scopes:
        if scope not in user_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: {scope}",
            )
            
    return current_user