"""Repository for managing notifications."""
import logging

from sqlalchemy import Select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.wrlc_alma_item_checks.models.notification import Notification as SQLAlchemyNotification
from src.wrlc_alma_item_checks.api.models.notification import NotificationCreate as PydanticNotificationCreate
from src.wrlc_alma_item_checks.api.models.notification import NotificationUpdate as PydanticNotificationUpdate


# noinspection PyMethodMayBeStatic
class NotificationRepository:
    """Repository for managing notifications."""

    def __init__(self, session: Session):
        self.session = session

    def create_notification(self, notification_data: PydanticNotificationCreate) -> SQLAlchemyNotification:
        """
        Create a new notification.

        Args:
            notification_data (PydanticNotificationCreate): The notification data to create.

        Returns:
            SQLAlchemyNotification: The created notification.

        """
        notification = SQLAlchemyNotification(**notification_data.model_dump())
        try:
            self.session.add(notification)
            self.session.commit()
            self.session.refresh(notification)
            return notification
        except SQLAlchemyError as e:
            logging.error(f"Error creating notification: {e}")
            self.session.rollback()
            raise
        except Exception as e:
            logging.error(f"Error creating notification: {e}")
            self.session.rollback()
            raise

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

    def update_notification(
            self, notification_id: int, notification_data: PydanticNotificationUpdate
    ) -> SQLAlchemyNotification:
        """
        Update a notification.

        Args:
            notification_id (int): The ID of the notification to update.
            notification_data (PydanticNotificationUpdate): The notification data to update

        Returns:
            SQLAlchemyNotification: The updated notification.

        """
        notification = self.get_notification_by_id(notification_id)
        for key, value in notification_data.model_dump().items():
            setattr(notification, key, value)
        try:
            self.session.commit()
            self.session.refresh(notification)
            return notification
        except SQLAlchemyError as e:
            logging.error(f"Error updating notification: {e}")
            self.session.rollback()
            raise
        except Exception as e:
            logging.error(f"Error updating notification: {e}")
            self.session.rollback()
            raise

    def delete_notification(self, notification_id: int) -> bool:
        """
        Delete a notification.

        Args:
            notification_id (int): The ID of the notification to delete.

        Returns:
            bool: True if the notification was deleted, False otherwise.

        """
        notification = self.get_notification_by_id(notification_id)
        try:
            self.session.delete(notification)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            logging.error(f"Error deleting notification: {e}")
            self.session.rollback()
            return False
        except Exception as e:
            logging.error(f"Error deleting notification: {e}")
            self.session.rollback()
            return False
