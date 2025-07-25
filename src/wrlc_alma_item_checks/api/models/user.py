"""Pydantic models for User API."""
from pydantic import BaseModel


class User(BaseModel):
    id: int
    email: str
    is_active: bool


class UserCreate(BaseModel):
    email: str


class UserUpdate(BaseModel):
    email: str | None = None
    is_active: bool | None = None
