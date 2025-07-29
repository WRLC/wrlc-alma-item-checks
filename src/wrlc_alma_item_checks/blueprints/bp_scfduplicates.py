"""Timer trigger to fetch duplicate barcodes from the Alma API for SCF."""
import azure.functions as func
import logging

from sqlalchemy.orm import Session
from wrlc_alma_api_client import AlmaApiClient
from wrlc_alma_api_client.models import AnalyticsReportResults

from src.wrlc_alma_item_checks.config import (
    SCF_DUPLICATES_SCHEDULE, SCF_DUPLICATES_CHECK_NAME, NOTIFIER_CONTAINER_NAME, NOTIFIER_QUEUE_NAME
)
from src.wrlc_alma_item_checks.models.check import Check
from src.wrlc_alma_item_checks.repositories.database import SessionMaker
from src.wrlc_alma_item_checks.services.check_service import CheckService
from src.wrlc_alma_item_checks.services.job_service import JobService
from src.wrlc_alma_item_checks.services.storage_service import StorageService

bp = func.Blueprint()


@bp.timer_trigger(schedule=SCF_DUPLICATES_SCHEDULE, arg_name="scfduptimer", run_on_startup=False, use_monitor=False)
def ScfDuplicatesTimer(scfduptimer: func.TimerRequest) -> None:
    """
    Timer function wrapper for the 'scf_duplicates' configuration.

    Args:
        scfduptimer (func.TimerRequest): The timer request object.
    """

    check_name: str = SCF_DUPLICATES_CHECK_NAME  # get check name

    if scfduptimer.past_due:
        logging.info(f'Timer function "{check_name}" is past due!')

    logging.info(f'Python timer trigger function initiating job for "{check_name}".')

    db: Session = SessionMaker()  # get database session

    check_service: CheckService = CheckService(db)  # get check service
    check: Check = check_service.get_check_by_name(check_name)  # get check by name

    db.close()  # close database session

    if not check:  # check if check exists
        logging.info(f'Check "{check_name}" does not exist. Exiting')
        return

    job_service: JobService = JobService()  # get job service
    job_id: str = job_service.generate_job_id(check)  # create job ID

    alma_client: AlmaApiClient = AlmaApiClient(check.api_key, "NA", timeout=250)  # get Alma client

    try:
        report: AnalyticsReportResults = alma_client.analytics.get_report(check.report_path)  # get report
    except Exception as e:
        logging.error(f"Job {job_id}: Error retrieving report: {e}")
        return

    if len(report.rows) == 0:  # check if report is empty
        logging.info(f"Job {job_id}: No results found.")
        return

    storage_service = StorageService()  # get storage service

    storage_service.upload_blob_data(  # upload report to notifier container
        NOTIFIER_CONTAINER_NAME, f"{job_id}.json", report.rows
    )

    storage_service.send_queue_message(  # send message to notifier queue
        NOTIFIER_QUEUE_NAME,
        {
            "job_id": job_id,
            "check_id": check.id,
            "combined_data_container": NOTIFIER_CONTAINER_NAME,
            "combined_data_blob": f"{job_id}.json"
        }
    )
