"""Pydantic Models for Notification API"""
from pydantic import BaseModel


class Notification(BaseModel):
    id: int
    user_id: int
    check_id: int


class NotificationCreate(BaseModel):
    user_id: int
    check_id: int


class NotificationUpdate(BaseModel):
    user_id: int = None
    check_id: int = None
