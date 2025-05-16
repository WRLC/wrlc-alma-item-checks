"""Repository functions for check jobs"""
import logging
from sqlalchemy import Select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.orm import Session

from src.wrlc.alma.item_checks.models.check import Check


class CheckRepository:
    """
    Repository for managing checks in the Alma item checks system.
    """

    def __init__(self, session: Session):
        self.session: Session = session

    def get_check_by_id(self, check_id: int) -> Check | None:
        """
        Get a check by its ID.

        Args:
            check_id (int): The ID of the check to retrieve.

        Returns:
            Check: The check object.
        """
        stmt = (
            Select(Check)
            .where(Check.id == check_id)
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

    def get_check_by_name(self, check_name: str) -> Check | None:
        """
        Get a check by its name.

        Args:
            check_name (str): The name of the check to retrieve.

        Returns:
            Check: The check object.
        """
        stmt = (
            Select(Check)
            .where(Check.name == check_name)
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
