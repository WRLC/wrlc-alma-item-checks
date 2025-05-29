"""Model for Check."""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.wrlc.alma.item_checks.models.base import Base


class Check(Base):
    """
    Base class for item checks.
    """

    __tablename__ = 'checks'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    api_key: Mapped[str] = mapped_column(String(255), nullable=True)
    report_path: Mapped[str] = mapped_column(String(255), nullable=True)
    email_subject: Mapped[str] = mapped_column(String(255), nullable=True)
    email_body: Mapped[str] = mapped_column(String(255), nullable=True)
