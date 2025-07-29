"""Fixes SCF No Row/Tray events"""
import logging
import re

from sqlalchemy.orm import Session
from wrlc_alma_api_client.models.item import Item

from src.wrlc_alma_item_checks.config import EXCLUDED_NOTES, SKIP_LOCATIONS, NOTIFIER_QUEUE_NAME
from src.wrlc_alma_item_checks.models.check import Check
from src.wrlc_alma_item_checks.repositories.database import SessionMaker
from src.wrlc_alma_item_checks.services.check_service import CheckService
from src.wrlc_alma_item_checks.services.job_service import JobService
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
        self.job_service: JobService = JobService()

    def should_process(self) -> bool:
        """
        Check if the item should be processed

        Returns:
            bool: True if the item should be processed, False otherwise

        """
        if self.no_row_tray_data() or self.wrong_row_tray_data():  # check if row/tray data present and in right format
            if self.item.item_data.internal_note_1 in EXCLUDED_NOTES:  # check if internal note 1 is an excluded value
                logging.info('SCFNoRowTray: internal note 1 is in excluded list, skipping processing')
                return False
            return True

        return False

    def process(self) -> None:
        """
        Process the SCFNoRowTray event

        Returns:
            None

        """
        # notify users
        check_name: str = "SCFNoRowTray"

        db: Session = SessionMaker()  # get database session

        check_service: CheckService = CheckService(db)  # get check service
        check: Check = check_service.get_check_by_name(check_name)  # get check by name

        db.close()  # close database session

        if not check:  # check if check_name exists
            logging.error(f'SCFNoRowTray: Check "{check_name}" does not exist. Exiting')
            return

        job_id: str = self.job_service.generate_job_id(check)  # create job ID

        title: str = self.item.bib_data.title if self.item.bib_data.title else 'None'
        author: str = self.item.bib_data.author if self.item.bib_data.author else 'None'
        barcode: str = self.item.item_data.barcode if self.item.item_data.barcode else 'None'
        call_number: str = self.item.item_data.alternative_call_number if self.item.item_data.alternative_call_number \
            else 'None'
        internal_note_1: str = self.item.item_data.internal_note_1 if self.item.item_data.internal_note_1 else 'None'

        # Create item HTML table for the email
        addendum_table: str = f"""
            <table>
                <caption>{check.email_subject}</caption>
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Author</th>
                        <th>Barcode</th>
                        <th>Item Call Number</th>
                        <th>Internal Note 1</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{title}</td>
                        <td>{author}</td>
                        <td>{barcode}</td>
                        <td>{call_number}</td>
                        <td>{internal_note_1}</td>
                    </tr>
                </tbody>
            </table>
        """

        storage_service: StorageService = StorageService()  # Get storage service

        storage_service.send_queue_message(  # Send message to notifier queue
            NOTIFIER_QUEUE_NAME,
            {
                "job_id": job_id,
                "check_id": check.id,
                "combined_data_container": None,
                "email_body_addendum": addendum_table
            }
        )

    def no_row_tray_data(self) -> bool:
        """
        Check if row/tray data is missing from alternative call number.

        Returns:
            bool: True if row/tray data is missing, False otherwise
        """
        alt_call_number: str | None = self.item.item_data.alternative_call_number

        if alt_call_number is None:
            logging.info('SCFNoRowTray.no_row_tray_data: Alternative Call Number is not set. Processing.')
            return True

        logging.info(f'SCFNoRowTray.no_row_tray_data: Alternative Call Number {alt_call_number} is set. Skipping.')
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

                if any(loc in field_value for loc in SKIP_LOCATIONS):  # check if call number in a skipped location
                    logging.info(
                        f'SCFNoRowTray.wrong_row_tray_data: Skipping field with value "{field_value}" '
                        f'because it contains a skipped location.')
                    continue

                if re.search(pattern, field_value) is None:  # check if call number matches correct format
                    logging.info(
                        f'SCFNoRowTray.wrong_row_tray_data: {field.get("label")} in incorrect format. Processing.'
                    )
                    return True

        logging.info('SCFNoRowTray.wrong_row_tray_data: All set fields in correct format. Skipping.')
        return False
