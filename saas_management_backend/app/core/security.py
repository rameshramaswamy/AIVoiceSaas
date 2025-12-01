from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings
import re
from fastapi import HTTPException, status

# Enterprise: Role-to-Scope Mapping
ROLE_PERMISSIONS = {
    "owner": ["tenant:manage", "billing:manage", "agent:write", "agent:read", "user:manage"],
    "admin": ["agent:write", "agent:read", "user:read"],
    "viewer": ["agent:read"]
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def validate_password_strength(password: str):
    """
    Enforce enterprise password policy:
    - At least 12 chars
    - Mixed case, numbers, special chars
    """
    if len(password) < 12:
        raise HTTPException(status_code=400, detail="Password must be at least 12 characters.")
    if not re.search(r"[A-Z]", password):
        raise HTTPException(status_code=400, detail="Password must contain uppercase letters.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(status_code=400, detail="Password must contain special characters.")
    return True

def get_scopes_for_role(role: str) -> list:
    return ROLE_PERMISSIONS.get(role, [])