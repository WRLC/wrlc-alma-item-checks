"""Repository functions for check jobs"""
import logging
from typing import List
from sqlalchemy import Select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session
from src.wrlc.alma.item_checks.models.check import Check as SQLAlchemyCheckModel
from src.wrlc.alma.item_checks.api.models.check import CheckCreate as PydanticCheckCreate
from src.wrlc.alma.item_checks.api.models.check import CheckUpdate as PydanticCheckUpdate


class CheckRepository:
    """
    Repository for managing checks in the Alma item checks system.
    """

    def __init__(self, session: Session):
        self.session: Session = session

    def create_check(self, check_data: PydanticCheckCreate) -> SQLAlchemyCheckModel:
        """
        Create a new check.

        Args:
            check_data (PydanticCheckCreate): Check data

        Returns:
            SQLAlchemyCheckModel: The check object
        """
        db_check = SQLAlchemyCheckModel(**check_data.model_dump())
        try:
            self.session.add(db_check)
            self.session.commit()
            self.session.refresh(db_check)
            return db_check
        except SQLAlchemyError as e:
            logging.error(f'Database error: {e}')
            self.session.rollback()
            raise
        except Exception as e:
            logging.error(f'Unexpected error: {e}')
            self.session.rollback()
            raise

    def get_all_checks(self, skip: int = 0, limit: int = 100) -> List[SQLAlchemyCheckModel]:
        """
        Get all checks.

        Returns:
            list[SQLAlchemyCheckModel]: List of check objects
        """
        stmt = Select(SQLAlchemyCheckModel).limit(limit).offset(skip)
        try:
            return list(self.session.execute(stmt).scalars().all())
        except SQLAlchemyError as e:
            logging.error(f'Database error: {e}')
            return []
        except Exception as e:
            logging.error(f'Unexpected error: {e}')
            return []

    def get_check_by_id(self, check_id: int) -> SQLAlchemyCheckModel | None:
        """
        Get a check by its ID.

        Args:
            check_id (int): The ID of the check to retrieve.

        Returns:
            Check: The check object.
        """
        stmt = (
            Select(SQLAlchemyCheckModel)
            .where(SQLAlchemyCheckModel.id == check_id)
        )

        try:
            return self.session.execute(stmt).scalars().first()
        except NoResultFound:
            logging.error(f'No such check: {check_id}')
            return None
        except SQLAlchemyError as e:
            logging.error(f'Database error: {e}')
            return None
        except Exception as e:
            logging.error(f'Unexpected error: {e}')
            return None

    def get_check_by_name(self, check_name: str) -> SQLAlchemyCheckModel | None:
        """
        Get a check by its name.

        Args:
            check_name (str): The name of the check to retrieve.

        Returns:
            Check: The check object.
        """
        stmt = (
            Select(SQLAlchemyCheckModel)
            .where(SQLAlchemyCheckModel.name == check_name)
        )

        try:
            return self.session.execute(stmt).scalars().first()
        except NoResultFound:
            logging.error(f'No such check: {check_name}')
            return None
        except SQLAlchemyError as e:
            logging.error(f'Database error: {e}')
            return None
        except Exception as e:
            logging.error(f'Unexpected error: {e}')
            return None

    def update_check(self, check_id: int, check_data: PydanticCheckUpdate) -> SQLAlchemyCheckModel | None:
        """
        Update a check by its ID.

        Args:
            check_id (int): The ID of the check to update
            check_data (PydanticCheckCreate): Check data

        Returns:
            Check: The updated check object
        """
        db_check = self.get_check_by_id(check_id)
        if db_check is None:
            return None
        for key, value in check_data.model_dump().items():
            setattr(db_check, key, value)
        try:
            self.session.commit()
            self.session.refresh(db_check)
            return db_check
        except SQLAlchemyError as e:
            logging.error(f'Database error: {e}')
            self.session.rollback()
            return None

    def delete_check(self, check_id: int) -> bool:
        """
        Delete a check by its ID.

        Args:
            check_id (int): The ID of the check to delete

        Returns:
            bool: True if the check was deleted, False otherwise
        """
        db_check = self.get_check_by_id(check_id=check_id)
        if db_check is None:
            return False
        try:
            self.session.delete(db_check)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            logging.error(f'Database error: {e}')
            self.session.rollback()
            return False
        except Exception as e:
            logging.error(f'Unexpected error: {e}')
            self.session.rollback()
            return False
