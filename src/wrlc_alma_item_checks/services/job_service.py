"""Service functions for check jobs"""
import datetime
import uuid

from ..models.check import Check


# noinspection PyMethodMayBeStatic
class JobService:
    """Service functions for check jobs"""
    def generate_job_id(self, check: Check) -> str:
        """
        Generate a unique job ID.

        Returns:
            str: The generated job ID.
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        job_id = f"job_{check.name}_{timestamp}_{unique_id}"  # Use passed name

        return job_id
