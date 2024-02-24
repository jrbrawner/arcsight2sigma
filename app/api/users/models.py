from sqlmodel import Field

from app.database import BaseModel

class UserBase(BaseModel):
    """Base model for Users"""
    user_id: str = Field(nullable=False, unique=True)
    email: str = Field(nullable=False, unique=True)
    id: int = Field(primary_key=True)

class User(UserBase):
    """Model for regular users."""

    __tablename__ = "user"

