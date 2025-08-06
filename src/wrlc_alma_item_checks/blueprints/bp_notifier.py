"""Notifier blueprint for Alma item checks."""
import logging

import azure.functions as func
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from src.wrlc_alma_item_checks.config import NOTIFIER_QUEUE_NAME, TEMPLATE_FILE_NAME
from src.wrlc_alma_item_checks.repositories.check_repo import CheckRepository
from src.wrlc_alma_item_checks.repositories.database import SessionMaker
from src.wrlc_alma_item_checks.repositories.user_repo import UserRepository
from src.wrlc_alma_item_checks.services.storage_service import StorageService
from src.wrlc_alma_item_checks.models.check import Check
from src.wrlc_alma_item_checks.models.user import User
from src.wrlc_alma_item_checks.services.notifier_service import NotifierService
from src.wrlc_alma_item_checks.models.email import EmailMessage

bp = func.Blueprint()


@bp.queue_trigger(queue_name=NOTIFIER_QUEUE_NAME, connection="AzureWebJobsStorage", arg_name="msg")
def ItemCheckNotifier(msg: func.QueueMessage) -> None:
    """
    Queue trigger for processing items.

    Args:
        msg (func.QueueMessage): The item to process.

    Expected message format:
    {
        "job_id": "123456",
        "check_id": 123,
        "combined_data_blob": "...", # Optional: for reports generated from a blob of JSON
        "email_body_addendum": "...", # Optional: for small, inline text
        "email_body_addendum_blob_name": "..." # Optional: for large reports stored in a blob
    }
    """
    try:  # Get the job ID and check ID from the message
        message_data = msg.get_json()
        job_id: str = message_data.get("job_id")
        check_id: int = message_data.get("check_id")
        if not all([job_id, check_id]):
            raise ValueError("Message is missing 'job_id' or 'check_id'")
    except (ValueError, AttributeError) as val_err:
        logging.error(f"Invalid or malformed message received: {val_err}")
        return

    try:
        # Use a 'with' statement for robust session management
        with SessionMaker() as db:
            check_repo: CheckRepository = CheckRepository(db)
            check: Check | None = check_repo.get_check_by_id(check_id)

            user_repo: UserRepository = UserRepository(db)
            users: list[User] = user_repo.get_users_by_check_id(check_id)
    except NoResultFound:
        # This covers the case where the check doesn't exist, or no users are assigned.
        logging.warning(f"Job {job_id}: No check found or no users are subscribed to notifications. Exiting.")
        return
    except SQLAlchemyError as db_err:
        logging.error(f"Job {job_id}: Database error while fetching check/users: {db_err}", exc_info=True)
        return

    if not users:
        logging.warning(f"Job {job_id}: No users are subscribed to notifications. Exiting.")
        return

    notifier_service: NotifierService = NotifierService()

    if not check:
        logging.error(f"Job {job_id}: No check is subscribed to notifications. Exiting.")
        return

    html_table: str | None = notifier_service.create_html_table(
        msg=msg,
        job_id=job_id,
        check=check
    )
    # Get the addendum, prioritizing the blob pointer if it exists
    body_addendum: str | None
    addendum_blob_name = message_data.get("email_body_addendum_blob_name")
    addendum_container_name = message_data.get("email_body_addendum_container_name")

    if addendum_blob_name and addendum_container_name:
        try:
            storage_service = StorageService()
            body_addendum = storage_service.download_blob_as_text(
                container_name=addendum_container_name,
                blob_name=addendum_blob_name
            )
            # Clean up the temporary blob now that we have its content
            storage_service.delete_blob(addendum_container_name, addendum_blob_name)
        except Exception as e:
            logging.error(f"Job {job_id}: Failed to download or delete addendum blob '{addendum_blob_name}': {e}")
            # Fallback to an error message in the email body
            body_addendum = "<i>[Error: Could not load report content from storage.]</i>"
    else:
        # Fallback to the old method for backward compatibility or other use cases
        body_addendum = message_data.get("email_body_addendum")

    if not html_table and not body_addendum:
        logging.info(f"Job {job_id}: No data table or addendum to send. Skipping email.")
        return

    # Corrected keyword argument from 'template' to 'template_name'
    html_content_body: str | None = notifier_service.render_email_body(
        template_name=TEMPLATE_FILE_NAME,
        check=check,
        body_addendum=body_addendum,
        html_table=html_table,
        job_id=job_id
    )

    if not html_content_body:
        logging.error(f"Job {job_id}: Failed to render email body. Aborting send.")
        return

    email_to_send: EmailMessage = EmailMessage(
        to=[user.email for user in users],
        subject=check.email_subject,
        html=html_content_body
    )

    notifier_service.send_email(email_message=email_to_send, job_id=job_id)
