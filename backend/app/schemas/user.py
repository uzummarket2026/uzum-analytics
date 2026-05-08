from typing import Optional
from pydantic import BaseModel, Field


class UserBase(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool = False

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Foydalanuvchini tahrirlash — har bir maydon ixtiyoriy."""
    email: Optional[str] = Field(default=None, min_length=3, max_length=254)
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    is_active: Optional[bool] = None
