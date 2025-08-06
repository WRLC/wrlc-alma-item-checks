"""Repository for managing users in the Alma item checks system."""
import logging
from typing import List

from sqlalchemy import Select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.wrlc_alma_item_checks.models.notification import Notification
from src.wrlc_alma_item_checks.models.user import User as SQLAlchemyUserModel


class UserRepository:
    """
    Repository for managing users in the Alma item checks system.
    """

    def __init__(self, session: Session):
        self.session = session

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[SQLAlchemyUserModel]:
        """
        Get all users.

        Returns:
            list[SQLAlchemyUserModel]: A list of all users.
        """
        stmt: Select = Select(SQLAlchemyUserModel).limit(limit).offset(skip)
        try:
            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logging.error(f'Unexpected error: {e}')
            self.session.rollback()
            return []
        except Exception as e:
            logging.error(f'Unexpected error: {e}')
            self.session.rollback()
            return []

    def get_users_by_check_id(self, check_id: int) -> list[SQLAlchemyUserModel]:
        """
        Get a user by their ID.

        Args:
            check_id (int): The ID of the check to retrieve.

        Returns:
            User: The user object.
        """
        stmt: Select = (
            Select(SQLAlchemyUserModel)
            .join(Notification, SQLAlchemyUserModel.id == Notification.user_id)
            .where(Notification.check_id == check_id)
        )
        try:
            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logging.error(f'Unexpected error: {e}')
            self.session.rollback()
            raise
        except Exception as e:
            logging.error(f'Unexpected error: {e}')
            self.session.rollback()
            raise

    def get_user_by_id(self, user_id: int) -> SQLAlchemyUserModel:
        """
        Get a user by their ID.

        Args:
            user_id (int): The ID of the user to retrieve.


        Returns:
            User: The user object.
        """
        stmt: Select = Select(SQLAlchemyUserModel).where(SQLAlchemyUserModel.id == user_id)
        try:
            return self.session.execute(stmt).scalars().one()
        except SQLAlchemyError as e:
            logging.error(f'Unexpected error: {e}')
            self.session.rollback()
            raise
        except Exception as e:
            logging.error(f'Unexpected error: {e}')
            self.session.rollback()
            raise
