from uuid import UUID
from typing import Optional

from pydantic import BaseModel, EmailStr


# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Properties to return via API
class UserRead(UserBase):
    id: UUID
    is_verified: bool
    is_active: bool

    class Config:
        from_attributes = True
