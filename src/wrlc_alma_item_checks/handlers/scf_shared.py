"""SCFShared class to handle shared SCF Item checks"""
import logging

from sqlalchemy.orm import Session
from wrlc_alma_api_client import AlmaApiClient
from wrlc_alma_api_client.exceptions import AlmaApiError
from wrlc_alma_api_client.models.item import Item

from ..config import PROVENANCE
from ..services.check_service import CheckService
from ..repositories.database import SessionMaker
from ..models.check import Check


class SCFShared:
    """
    SCFShared class to handle shared SCF Item checks
    """
    def __init__(self, item: Item):
        """
        Initialize the SCFShared class

        Args:
            item (Item): The item data

        """
        self.item = item
        self.check_service = CheckService

    def should_process(self) -> Item | None:
        """
        Check if the item should be processed

        Returns:
            Item | None: the item data, if found, else None

        """
        if (  # Check if the item is not in a discard temporary location
                self.item.holding_data.temp_location.value
                and 'discard' in self.item.holding_data.temp_location.value.lower()
        ):
            logging.info(f"Item is in a discard temporary location, skipping processing")
            return None

        if 'discard' in self.item.item_data.location.value.lower():  # Check if the item is in a discard location
            logging.info(f"Item is in a discard location, skipping processing")
            return None

        if self.item.item_data.provenance.desc not in PROVENANCE:  # Check if the item has a checked provenance
            logging.info(f"Item has no checked provenance, skipping processing")
            return None

        # Get item by barcode to see if active
        check_name: str = "ScfShared"  # get check name

        db: Session = SessionMaker()  # get database session

        check_service: CheckService = CheckService(db)  # get check service
        check: Check = check_service.get_check_by_name(check_name)  # get check by name

        db.close()  # close database session

        # Retrieve the item from Alma using the barcode
        alma_client: AlmaApiClient = AlmaApiClient(check.api_key, 'NA')

        try:
            item_data: Item = alma_client.items.get_item_by_barcode(self.item.item_data.barcode)
        except AlmaApiError as e:  # If there is an error retrieving the item from Alma, log a warning and return None
            logging.info(f"Error retrieving item from Alma, skipping processing: {e}")
            return None

        # Check if the item was found
        if not item_data:
            logging.info(f"Item not active in Alma, skipping processing")
            return None

        return item_data
