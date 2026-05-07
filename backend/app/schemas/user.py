from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Foydalanuvchini tahrirlash — har bir maydon ixtiyoriy."""
    email: EmailStr | None = None
    password: str | None = None
    is_active: bool | None = None
