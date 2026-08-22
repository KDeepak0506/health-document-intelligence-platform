from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    DOCTOR = "doctor"
    NURSE = "nurse"
    RECORDS_STAFF = "records_staff"
    ADMIN = "admin"


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole


class UserResponse(BaseModel):
    user_id: UUID
    name: str
    email: str
    role: str
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"