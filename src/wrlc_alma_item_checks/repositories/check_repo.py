"""Repository functions for check jobs"""
import logging
from typing import List, Any

from sqlalchemy import Select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from src.wrlc_alma_item_checks.models.check import Check as SQLAlchemyCheckModel


class CheckRepository:
    """
    Repository for managing checks in the Alma item checks system.
    """

    def __init__(self, session: Session):
        self.session: Session = session

    def get_all_checks(self, skip: int = 0, limit: int = 100) -> List[SQLAlchemyCheckModel]:
        """
        Get all checks.

        Returns:
            list[SQLAlchemyCheckModel]: List of check objects
        """
        stmt: Any = Select(SQLAlchemyCheckModel).limit(limit).offset(skip)
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
