from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.VIEWER


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    password: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserRead(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)