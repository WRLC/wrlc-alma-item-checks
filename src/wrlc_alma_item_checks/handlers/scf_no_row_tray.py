"""Fixes SCF No Row/Tray events"""
import logging
import re

from wrlc_alma_api_client.models.item import Item  # type: ignore

from src.wrlc_alma_item_checks.config import EXCLUDED_NOTES, SKIP_LOCATIONS, SCF_NO_ROW_TRAY_CHECK_NAME
from src.wrlc_alma_item_checks.services.storage_service import StorageService


class SCFNoRowTray:
    """
    SCFNoRowTray class to handle SCF No Row/Tray events

    """
    def __init__(self, item: Item):
        """
        Initialize the SCFNoRowTray class

        Args:
            item (Item): The Item data

        """
        self.item: Item = item

    def should_process(self) -> bool:
        """
        Check if the item should be processed

        Returns:
            bool: True if the item should be processed, False otherwise
        """
        if self.no_row_tray_data() or self.wrong_row_tray_data():  # check if row/tray data present and in right format
            if self.item.item_data.internal_note_1 in EXCLUDED_NOTES:  # check if internal note 1 is an excluded value
                logging.info(
                    msg=f"SCFNoRowTray.should_process:Item {self.item.item_data.barcode} failed "
                        f"{SCF_NO_ROW_TRAY_CHECK_NAME} check. Staging for daily report."
                )
                return False
            return True
        return False

    def stage(self) -> None:
        """
        Stage the item in Azure Table Storage for re-processing

        Returns:
            None
        """
        # Use the barcode as the unique identifier for the row
        barcode: str | None = self.item.item_data.barcode

        if not barcode:
            logging.warning(msg="SCFNoRowTray.stage: Cannot stage item for daily check because it has no barcode.")
            return

        # Define the entity to be saved in Azure Table Storage
        # PartitionKey can be the check name to group all items for this specific check
        # RowKey should be a unique identifier for the item, like the barcode
        entity: dict[str, str] = {
            "PartitionKey": SCF_NO_ROW_TRAY_CHECK_NAME,
            "RowKey": barcode,
        }

        storage_service: StorageService = StorageService()
        storage_service.upsert_entity(
            table_name=SCF_NO_ROW_TRAY_CHECK_NAME,
            entity=entity
        )

    def no_row_tray_data(self) -> bool:
        """
        Check if row/tray data is missing from alternative call number.

        Returns:
            bool: True if row/tray data is missing, False otherwise
        """
        alt_call_number: str | None = self.item.item_data.alternative_call_number

        if alt_call_number is None:
            logging.info(msg='SCFNoRowTray.no_row_tray_data: Alternative Call Number is not set. Processing.')
            return True

        logging.info(msg=f'SCFNoRowTray.no_row_tray_data: Alternative Call Number {alt_call_number} is set. Skipping.')
        return False

    def wrong_row_tray_data(self) -> bool:
        """
        Check if row/tray data is in wrong format and not in a skipped location

        Returns:
            bool: True if row/tray data is in wrong format, False otherwise
        """

        fields_to_check: list[dict[str, str]] = [
            {
                "label": "Alt Call Number",
                "value": self.item.item_data.alternative_call_number
            },
            {
                "label": "Internal Note 1",
                "value": self.item.item_data.internal_note_1
            }
        ]

        pattern: str = r"^R.*M.*S"  # regex for correct row/tray data format

        for field in fields_to_check:  # check both fields

            field_value: str | None = field.get('value')

            if field_value is not None:  # only process if the field has value set

                if any(loc in field_value for loc in SKIP_LOCATIONS):  # check if in skipped location
                    logging.info(
                        msg=f'SCFNoRowTray.wrong_row_tray_data: Skipping field with value "{field_value}" '
                        f'because it contains a skipped location.')
                    continue

                if re.search(pattern=pattern, string=field_value) is None:  # check if call number matches format
                    logging.info(
                        msg=f'SCFNoRowTray.wrong_row_tray_data: {field.get("label")} in incorrect format. Processing.'
                    )
                    return True

        logging.info(msg='SCFNoRowTray.wrong_row_tray_data: All set fields in correct format. Skipping.')
        return False
