""" Handles IZ No Row/Tray events """
from wrlc_alma_api_client.models.item import Item

from src.wrlc_alma_item_checks.services.job_service import JobService


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class IzNoRowTray:
    """
    IZNoRowTray class to handle IZ No Row/Tray events
    """
    def __init__(self, iz: str, item: Item):
        """
        Initialize the IZNoRowTray class

        Args:
            item (Item): The Item data

        """
        self.item: Item = item
        self.job_service: JobService = JobService()

    def should_process(self) -> bool:
        """
        Check if the item should be processed

        Returns:
            bool: True if the item should be processed, False otherwise
        """

        return False
