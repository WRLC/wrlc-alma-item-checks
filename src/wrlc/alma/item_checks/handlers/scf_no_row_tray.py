"""Fixes SCF No Row/Tray events"""
import logging
import re
from sqlalchemy.orm import Session
from wrlc.alma.api_client.models.item import Item
from wrlc.alma.item_checks.api.models.check import Check
from src.wrlc.alma.item_checks.repositories.database import SessionMaker
from src.wrlc.alma.item_checks.services.check_service import CheckService
from src.wrlc.alma.item_checks.services.job_service import JobService
import wrlc.alma.item_checks.config as config
from wrlc.alma.item_checks.services.storage_service import StorageService

NOTIFIER_QUEUE_NAME = config.NOTIFIER_QUEUE_NAME
EXCLUDED_NOTES = config.EXCLUDED_NOTES
SKIP_LOCATIONS = config.SKIP_LOCATIONS


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
        self.item = item
        self.check_service = CheckService
        self.job_service = JobService()

    def should_process(self) -> bool:
        """
        Check if the item should be processed

        Returns:
            bool: True if the item should be processed, False otherwise

        """
        if self.no_row_tray_data() or self.wrong_row_tray_data():  # check if row/tray data present and in right format
            logging.info('Call number and internal note 1 exist, skipping processing')
            return False

        if self.item.item_data.internal_note_1 in EXCLUDED_NOTES:  # check if internal note 1 is an excluded value
            logging.info('internal note 1 is in list, skipping processing')
            return False

        return True

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
            logging.error(f'Check "{check_name}" does not exist. Exiting')
            return

        job_id: str = self.job_service.generate_job_id(check)  # create job ID

        title = self.item.bib_data.title if self.item.bib_data.title else ''
        author = self.item.bib_data.author if self.item.bib_data.author else ''
        barcode = self.item.item_data.barcode if self.item.item_data.barcode else ''
        call_number = self.item.holding_data.call_number if self.item.holding_data.call_number else ''
        internal_note_1 = self.item.item_data.internal_note_1 if self.item.item_data.internal_note_1 else ''

        # Create item HTML table for the email
        addendum_table = f"""
            <table>
                <caption>{check.email_subject}</caption>
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Author</th>
                        <th>Barcode</th>
                        <th>Call Number</th>
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

        storage_service = StorageService()  # Get storage service

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
        Check if row/tray data is missing
        """
        if self.item.holding_data.call_number and self.item.item_data.internal_note_1:
            return False  # if both call # and internal note 1 exist, skip processing

        return True

    def wrong_row_tray_data(self) -> bool:
        """
        Check if row/tray data is in wrong format and not in a skipped location
        """
        pattern = r"^R.*M.*S"  # regex for correct row/tray data format

        if re.search(pattern, self.item.holding_data.call_number):  # if call number in correct format, skip processing
            return False

        for location in SKIP_LOCATIONS:  # if any skip location is in call number, skip processing
            if location in self.item.holding_data.call_number:
                return False

        return True
