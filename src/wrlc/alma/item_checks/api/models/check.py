"""Pydantic Models for Check API"""
from pydantic import BaseModel


class Check(BaseModel):
    id: int
    name: str
    api_key: str
    report_path: str
    email_subject: str
    email_body: str


class CheckCreate(BaseModel):
    name: str
    api_key: str
    report_path: str
    email_subject: str
    email_body: str


class CheckUpdate(BaseModel):
    name: str = None
    api_key: str = None
    report_path: str = None
    email_subject: str = None
    email_body: str = None
