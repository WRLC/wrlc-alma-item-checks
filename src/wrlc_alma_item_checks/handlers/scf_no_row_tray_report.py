"""Handler for the SCF No Row/Tray report"""
import logging

from sqlalchemy.orm import Session
from wrlc_alma_api_client.models.item import Item  # type: ignore

from src.wrlc_alma_item_checks.config import (
    NOTIFIER_CONTAINER_NAME,
    NOTIFIER_QUEUE_NAME,
    SCF_NO_ROW_TRAY_CHECK_NAME
)
from src.wrlc_alma_item_checks.models.check import Check
from src.wrlc_alma_item_checks.repositories.database import SessionMaker
from src.wrlc_alma_item_checks.services.check_service import CheckService
from src.wrlc_alma_item_checks.services.job_service import JobService
from src.wrlc_alma_item_checks.services.storage_service import StorageService


# noinspection PyMethodMayBeStatic
class ScfNoRowTrayReport:
    """Handler for the SCF No Row/Tray report"""
    def __init__(self):
        self.job_service = JobService()

    def process(self, items_still_failing: list[Item]) -> None:
        """
        Process the SCFNoRowTray report

        Returns:
            None

        """
        db: Session = SessionMaker()  # get database session

        check_service: CheckService = CheckService(db)  # get check service
        check: Check | None = check_service.get_check_by_name(SCF_NO_ROW_TRAY_CHECK_NAME)  # get check by name

        db.close()  # close database session

        if not check:  # check if check_name exists
            logging.error(f'SCFNoRowTrayReport.process: Check "{SCF_NO_ROW_TRAY_CHECK_NAME}" does not exist. Exiting')
            return

        job_id: str = self.job_service.generate_job_id(check)  # create job ID
        html_table = self._generate_report_html(check, items_still_failing)

        storage_service: StorageService = StorageService()  # Get storage service

        # Save the large HTML report to a blob to avoid exceeding queue message size limits
        addendum_blob_name = f"{job_id}-addendum.html"
        storage_service.upload_blob_data(
            container_name=NOTIFIER_CONTAINER_NAME,
            blob_name=addendum_blob_name,
            data=html_table
        )

        # Send a small message to the notifier queue with a pointer to the blob
        message_payload = {
            "job_id": job_id,
            "check_id": check.id,
            "email_body_addendum_blob_name": addendum_blob_name,
            "email_body_addendum_container_name": NOTIFIER_CONTAINER_NAME
        }

        storage_service.send_queue_message(
            queue_name=NOTIFIER_QUEUE_NAME,
            message_content=message_payload
        )

    def _generate_report_html(self, check: Check, items: list[Item]) -> str:
        """Generates a consolidated HTML table for a list of items."""
        rows_html = ""
        for item in items:
            # Safely get attributes, providing 'None' as a default string
            title = item.bib_data.title or 'None'
            author = item.bib_data.author or 'None'
            barcode = item.item_data.barcode or 'None'
            call_number = item.item_data.alternative_call_number or 'None'
            internal_note_1 = item.item_data.internal_note_1 or 'None'
            rows_html += f"""
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;">{title}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{author}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{barcode}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{call_number}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{internal_note_1}</td>
            </tr>
            """

        return f"""
            <table style="width: 100%; border-collapse: collapse; font-family: sans-serif;">
                <caption style="font-size: 1.2em; margin: 0.5em 0; font-weight: bold;">{check.email_subject}</caption>
                <thead style="background-color: #f2f2f2;">
                    <tr>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Title</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Author</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Barcode</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Item Call Number</th>
                        <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Internal Note 1</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        """
