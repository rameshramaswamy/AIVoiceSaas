from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: str # Used to create the Tenant

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    tenant_id: UUID
    role: str

    class Config:
        from_attributes = True