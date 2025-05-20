"""Fixes SCF NoX events."""
import logging

from sqlalchemy.orm import Session
from wrlc.alma.api_client import AlmaApiClient
from wrlc.alma.api_client.models.item import Item

from src.wrlc.alma.item_checks import config
from src.wrlc.alma.item_checks.models.check import Check
from src.wrlc.alma.item_checks.repositories.database import SessionMaker
from src.wrlc.alma.item_checks.services.check_service import CheckService
from src.wrlc.alma.item_checks.services.job_service import JobService
from src.wrlc.alma.item_checks.services.storage_service import StorageService

PROVENANCE = [
    'Property of American University',
    'Property of American University Law School',
    'Property of Catholic University of America',
    'Property of Gallaudet University',
    'Property of George Mason University',
    'Property of George Washington Himmelfarb',
    'Property of George Washington University',
    'Property of George Washington University School of Law',
    'Property of Georgetown University',
    'Property of Georgetown University School of Law',
    'Property of Howard University',
    'Property of Marymount University',
    'Property of National Security Archive',
    'Property of University of the District of Columbia',
    'Property of University of the District of Columbia Jazz Archives',
]

NOTIFIER_QUEUE_NAME: str = config.NOTIFIER_QUEUE_NAME


# noinspection PyMethodMayBeStatic
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

    def should_process(self) -> Item | None:
        """
        Determine if the event should be processed.

        Returns:
            bool: True if the event should be processed, False otherwise.
        """
        if self.item.institution != 'scf':  # Check if the item is from the SCF
            return None

        if self.item.item_data.barcode.endswith('X'):  # Check if barcode ends with 'X'
            return None

        if self.item.item_data.provenance.value not in PROVENANCE:  # Check if the item has a checked provenance
            return None

        if (  # Check if the item is not in a discard temporary location
            self.item.item_data.temp_location.value
            and 'discard' in self.item.item_data.temp_location.value.lower()
        ):
            return None

        if 'discard' in self.item.item_data.location.value.lower():  # Check if the item is in a discard location
            return None

        check_name: str = "ScfNoX"  # get check name

        db: Session = SessionMaker()  # get database session

        check_service: CheckService = CheckService(db)  # get check service
        check: Check = check_service.get_check_by_name(check_name)  # get check by name

        # Retrieve the item from Alma using the barcode
        alma_client: AlmaApiClient = AlmaApiClient(check.api_key, 'NA')
        item_data: Item = alma_client.items.get_item_by_barcode(self.item.item_data.barcode)

        # Check if the item was found
        if not item_data:
            return None

        return item_data

    def process(self, item_data: Item) -> None:
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
            logging.info(f'Check "{check_name}" does not exist. Exiting')
            return

        alma_client: AlmaApiClient = AlmaApiClient(check.api_key, 'NA')  # get Alma client

        item_data.item_data.barcode += 'X'  # Update the barcode

        alma_client.items.update_item(  # Save the item back to Alma
            mm_id=item_data.bib_data.mms_id,
            holding_id=item_data.holding_data.holding_id,
            item_id=item_data.item_data.pid,
            item_record_data=item_data,
        )

        job_service: JobService = JobService()  # get job service
        job_id: str = job_service.generate_job_id(check)  # create job ID

        title = item_data.bib_data.title if item_data.bib_data.title else ''  # get title
        author = item_data.bib_data.author if item_data.bib_data.author else ''  # get author
        barcode = item_data.item_data.barcode if item_data.item_data.barcode else ''  # get barcode

        # Create item HTML table the email
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
