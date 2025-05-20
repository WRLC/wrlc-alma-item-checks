"""Repository for managing users in the Alma item checks system."""
import logging
from typing import List
from sqlalchemy import Select
from sqlalchemy.exc import SQLAlchemyError
from src.wrlc.alma.item_checks.models.notification import Notification
from src.wrlc.alma.item_checks.models.user import User as SQLAlchemyUserModel
from src.wrlc.alma.item_checks.api.models.user import UserCreate as PydanticUserCreate
from src.wrlc.alma.item_checks.api.models.user import UserUpdate as PydanticUserUpdate


class UserRepository:
    """
    Repository for managing users in the Alma item checks system.
    """

    def __init__(self, session):
        self.session = session

    def create_user(self, user_data: PydanticUserCreate) -> SQLAlchemyUserModel:
        """
        Create a new user.

        Args:
            user_data (PydanticUserCreate): The user to create.

        Returns:
            SQLAlchemyUserModel: The newly created user.
        """
        db_user = SQLAlchemyUserModel(**user_data.model_dump())
        try:
            self.session.add(db_user)
            self.session.commit()
            self.session.refresh(db_user)
            return db_user
        except SQLAlchemyError as e:
            logging.error(f'Unexpected error: {e}')
            self.session.rollback()
            raise
        except Exception as e:
            logging.error(f'Unexpected error: {e}')
            self.session.rollback()
            raise

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[SQLAlchemyUserModel]:
        """
        Get all users.

        Returns:
            list[SQLAlchemyUserModel]: A list of all users.
        """
        stmt = Select(SQLAlchemyUserModel).limit(limit).offset(skip)
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
        stmt = (
            Select(SQLAlchemyUserModel)
            .join(Notification, SQLAlchemyUserModel.id == Notification.user_id)
            .where(Notification.check_id == check_id)
        )

        return self.session.execute(stmt).scalars().all()

    def get_user_by_id(self, user_id: int) -> SQLAlchemyUserModel:
        """
        Get a user by their ID.

        Args:
            user_id (int): The ID of the user to retrieve.


        Returns:
            User: The user object.
        """
        stmt = Select(SQLAlchemyUserModel).where(SQLAlchemyUserModel.id == user_id)
        try:
            return self.session.execute(stmt).scalars.one()
        except SQLAlchemyError as e:
            logging.error(f'Unexpected error: {e}')
            self.session.rollback()
            raise
        except Exception as e:
            logging.error(f'Unexpected error: {e}')
            self.session.rollback()
            raise

    def update_user(self, user_id: int, user_data: PydanticUserUpdate) -> SQLAlchemyUserModel:
        """
        Update a user.

        Args:
            user_id (int): The ID of the user to update.
            user_data (PydanticUserUpdate): the user data to update

        Returns:
            SQLAlchemyUserModel: The updated user.
        """
        db_user = self.get_user_by_id(user_id)
        for key, value in user_data.model_dump().items():
            setattr(db_user, key, value)
        try:
            self.session.commit()
            self.session.refresh(db_user)
            return db_user
        except SQLAlchemyError as e:
            logging.error(f'Unexpected error: {e}')
            self.session.rollback()
            raise
        except Exception as e:
            logging.error(f'Unexpected error: {e}')
            self.session.rollback()
            raise

    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user.

        Args:
            user_id (int): The ID of the user to delete.
        """
        db_user = self.get_user_by_id(user_id)
        try:
            self.session.delete(db_user)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            logging.error(f'Unexpected error: {e}')
            self.session.rollback()
            return False
        except Exception as e:
            logging.error(f'Unexpected error: {e}')
            self.session.rollback()
            return False
