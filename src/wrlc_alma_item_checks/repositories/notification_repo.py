"""Repository for managing notifications."""
import logging

from sqlalchemy import Select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.notification import Notification as SQLAlchemyNotification


# noinspection PyMethodMayBeStatic
class NotificationRepository:
    """Repository for managing notifications."""

    def __init__(self, session: Session):
        self.session = session

    def get_all_notifications(self, skip: int = 0, limit: int = 100) -> list[SQLAlchemyNotification]:
        """
        Get all notifications.

        Args:
            skip (int): The offset for pagination.
            limit (int): The maximum number of notifications to retrieve.

        Returns:
            list[SQLAlchemyNotification]: A list of all notifications.

        """
        stmt = Select(SQLAlchemyNotification).limit(limit).offset(skip)
        try:
            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logging.error(f"Error getting notifications: {e}")
            self.session.rollback()
            return []
        except Exception as e:
            logging.error(f"Error getting notifications: {e}")
            self.session.rollback()
            return []

    def get_notification_by_id(self, notification_id: int) -> SQLAlchemyNotification:
        """
        Get a notification by its ID.

        Args:
            notification_id (int): The ID of the notification to retrieve.

        Returns:
            SQLAlchemyNotification: The retrieved notification.

        """
        stmt = Select(SQLAlchemyNotification).where(SQLAlchemyNotification.id == notification_id)
        try:
            return self.session.execute(stmt).scalars().one()
        except SQLAlchemyError as e:
            logging.error(f"Error getting notification by ID: {e}")
            raise
        except Exception as e:
            logging.error(f"Error getting notification by ID: {e}")
            self.session.rollback()
            raise
