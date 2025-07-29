"""Model for Notification."""
from sqlalchemy.orm import Mapped, mapped_column

from src.wrlc_alma_item_checks.models.base import Base


class Notification(Base):
    """
    SQLAlchemy model for a notification in the Alma item checks system.
    """
    __tablename__ = 'notifications'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(nullable=False)
    check_id: Mapped[int] = mapped_column(nullable=False)

    def __repr__(self):
        return f"<Notification(user_id={self.user_id}, check_id={self.check_id}')>"
