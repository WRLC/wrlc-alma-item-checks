"""Service for managing checks in the Alma item checks system."""
from sqlalchemy.orm import Session

from src.wrlc.alma.item_checks.models.check import Check
from src.wrlc.alma.item_checks.repositories.check_repo import CheckRepository


class CheckService:
    """
    Service for managing checks in the Alma item checks system.
    """

    def __init__(self, session: Session):
        self.check_repo = CheckRepository(session)

    def get_check_by_id(self, check_id: int) -> Check:
        """
        Get a check by its ID.

        Args:
            check_id (int): The ID of the check to retrieve.

        Returns:
            Check: The check object.
        """
        return self.check_repo.get_check_by_id(check_id)

    def get_check_by_name(self, check_name: str) -> Check:
        """
        Get a check by its name.

        Args:
            check_name (str): The name of the check to retrieve.

        Returns:
            Check: The check object.
        """
        return self.check_repo.get_check_by_name(check_name)
