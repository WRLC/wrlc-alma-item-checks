"""Fixes SCF NoX events."""
import logging

from sqlalchemy.orm import Session
from wrlc_alma_api_client import AlmaApiClient
from wrlc_alma_api_client.models.item import Item

from ..config import NOTIFIER_QUEUE_NAME
from ..models.check import Check
from ..repositories.database import SessionMaker
from ..services.check_service import CheckService
from ..services.job_service import JobService
from ..services.storage_service import StorageService


class SCFNoX:
    """
    SCFNoX class to handle SCF NoX events.
    """

    def __init__(self, item: Item):
        """
        Initialize the SCFNoX class with the given webhook data.

        Args:
            item (Item): The item data.
        """
        self.item = item
        self.check_service = CheckService
        self.job_service = JobService()

    def should_process(self) -> bool:
        """
        Determine if the event should be processed.

        Returns:
            bool: True if the event should be processed, False otherwise.
        """
        if self.item.item_data.barcode.endswith('X'):  # Check if barcode ends with 'X'
            logging.info(f"ScfNoX: Barcode ends in X, skipping processing")
            return False

        return True

    def process(self) -> None:
        """
        Process the SCF NoX event.

        Returns:
            None
        """
        check_name: str = "ScfNoX"  # get check name

        db: Session = SessionMaker()  # get database session

        check_service: CheckService = CheckService(db)  # get check service
        check: Check = check_service.get_check_by_name(check_name)  # get check by name

        db.close()  # close database session

        if not check:  # check if check_name exists
            logging.error(f'ScfNoX: Check "{check_name}" does not exist. Exiting')
            return

        alma_client: AlmaApiClient = AlmaApiClient(api_key=check.api_key, region='NA')  # get Alma client

        self.item.item_data.barcode += 'X'  # Update the barcode

        alma_client.items.update_item(  # Save the item back to Alma
            mms_id=self.item.bib_data.mms_id,
            holding_id=self.item.holding_data.holding_id,
            item_pid=self.item.item_data.pid,
            item_record_data=self.item,
        )

        job_id: str = self.job_service.generate_job_id(check)  # create job ID

        title = self.item.bib_data.title if self.item.bib_data.title else ''  # get title
        author = self.item.bib_data.author if self.item.bib_data.author else ''  # get author
        barcode = self.item.item_data.barcode if self.item.item_data.barcode else ''  # get barcode

        # Create item HTML table for the email
        addendum_table = f"""
            <table>
                <caption>{check.email_subject}</caption>
                <thead>
                    <tr>
                        <th>Title</th>
                        <th>Author</th>
                        <th>Barcode</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{title}</td>
                        <td>{author}</td>
                        <td>{barcode}</td>
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
