"""SCFWithdrawn class to handle SCF WD events"""
import logging

from sqlalchemy.orm import Session
from wrlc_alma_api_client.models.item import Item

from ..models.check import Check
from ..config import NOTIFIER_QUEUE_NAME
from ..repositories.database import SessionMaker
from ..services.check_service import CheckService
from ..services.job_service import JobService
from ..services.storage_service import StorageService


class SCFWithdrawn:
    """
    SCFWithdrawn class to handle SCF WD events

    """
    def __init__(self, item: Item):
        """
        Initialize the SCFWithdrawn class
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
        if (
            self.item.item_data.alternative_call_number == 'WD' or
            self.item.item_data.alternative_call_number == 'WD'
        ):
            return True

        return False

    def process(self) -> None:
        """
        Process the item

        """
        # Notify users
        check_name: str = "SCFWithdrawn"

        db: Session = SessionMaker()

        check_service: CheckService = self.check_service(db)
        check: Check = check_service.get_check_by_name(check_name)

        db.close()

        if not check:
            logging.error(f"SCFWithdrawn: Check {check_name} does not exist. Exiting.")
            return

        job_id = self.job_service.generate_job_id(check)

        title = self.item.bib_data.title if self.item.bib_data.title else ''
        author = self.item.bib_data.author if self.item.bib_data.author else ''
        barcode = self.item.item_data.barcode if self.item.item_data.barcode else ''
        call_number = self.item.item_data.alternative_call_number if self.item.item_data.alternative_call_number else ''
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
