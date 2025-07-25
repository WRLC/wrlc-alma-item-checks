"""Pydantic models for application data structures."""
from pydantic import BaseModel


class EmailMessage(BaseModel):
    """Represents the structure of an email message to be placed on the queue."""
    to: list[str]
    cc: list[str] | None = None
    subject: str
    html: str | None = None
    plaintext: str | None = None
