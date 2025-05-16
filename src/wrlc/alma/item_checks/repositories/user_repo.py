from sqlalchemy import Select

from src.wrlc.alma.item_checks.models.check import Check
from src.wrlc.alma.item_checks.models.notification import Notification
from src.wrlc.alma.item_checks.models.user import User


class UserRepository:
    """
    Repository for managing users in the Alma item checks system.
    """

    def __init__(self, session):
        self.session = session

    def get_users_by_check_id(self, check_id: int) -> list[User]:
        """
        Get a user by their ID.

        Args:
            check_id (int): The ID of the check to retrieve.

        Returns:
            User: The user object.
        """
        stmt = (
            Select(User)
            .join(Notification, User.id == Notification.user_id)
            .where(Notification.check_id == check_id)
        )

        return self.session.execute(stmt).scalars().all()
