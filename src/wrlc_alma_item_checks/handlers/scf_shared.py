"""SCFShared class to handle shared SCF Item checks"""
import logging

from wrlc_alma_api_client import AlmaApiClient
from wrlc_alma_api_client.exceptions import AlmaApiError
from wrlc_alma_api_client.models.item import Item

from src.wrlc_alma_item_checks.config import PROVENANCE
from src.wrlc_alma_item_checks.services.check_service import CheckService
from src.wrlc_alma_item_checks.repositories.database import SessionMaker
from src.wrlc_alma_item_checks.models.check import Check


class SCFShared:
    """
    SCFShared class to handle shared SCF Item checks
    """
    def __init__(self, barcode: str):
        """
        Initialize the SCFShared class

        Args:
            barcode (str): The barcode of the item to check

        """
        self.barcode = barcode

    def should_process(self) -> Item | None:
        """
        Check if the item should be processed

        Returns:
            Item | None: the item data, if found, else None
        """
        # Get item by barcode to see if active
        check_name: str = "ScfShared"  # get check name

        with SessionMaker() as db:
            check_service: CheckService = CheckService(db)
            check: Check = check_service.get_check_by_name(check_name)

        if not check or not check.api_key:
            logging.error(f"Could not find check '{check_name}' or it has no API key. Cannot proceed.")
            return None

        # Retrieve the item from Alma using the barcode
        alma_client: AlmaApiClient = AlmaApiClient(check.api_key, 'NA')

        try:
            item_data: Item = alma_client.items.get_item_by_barcode(self.barcode)
        except AlmaApiError as e:  # If there is an error retrieving the item from Alma, log a warning and return None
            logging.warning(f"Error retrieving item {self.barcode} from Alma, skipping processing: {e}")
            return None

        # Check if the item was found
        if not item_data:
            logging.info(f"Item {self.barcode} not active in Alma, skipping processing")
            return None

        if (  # Check if the item is not in a discard temporary location
                item_data.holding_data.temp_location.value
                and 'discard' in item_data.holding_data.temp_location.value.lower()
        ):
            logging.info(f"Item {self.barcode} is in a discard temporary location, skipping processing")
            return None

        if 'discard' in item_data.item_data.location.value.lower():  # Check if the item is in a discard location
            logging.info(f"Item {self.barcode} is in a discard location, skipping processing")
            return None

        if not item_data.item_data.provenance or item_data.item_data.provenance.desc not in PROVENANCE:
            logging.info(f"Item {self.barcode} has no checked provenance, skipping processing")
            return None

        return item_data
