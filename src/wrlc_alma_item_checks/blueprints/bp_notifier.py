"""Notifier blueprint for Alma item checks."""
import logging

import azure.functions as func
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from ..config import NOTIFIER_QUEUE_NAME, TEMPLATE_FILE_NAME
from ..repositories.check_repo import CheckRepository
from ..repositories.database import SessionMaker
from ..repositories.user_repo import UserRepository
from ..models.check import Check
from ..models.user import User
from ..services.notifier_service import NotifierService
from ..models.email import EmailMessage

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
        "combined_data_blob": "...",
        "email_body_addendum": "..."
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
            check: Check = check_repo.get_check_by_id(check_id)

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

    html_table: str | None = notifier_service.create_html_table(
        msg=msg,
        job_id=job_id,
        check=check
    )
    # Get the addendum if it exists, otherwise it remains None
    body_addendum: str | None = message_data.get("email_body_addendum")

    if not html_table and not body_addendum:
        logging.info(f"Job {job_id}: No data table or addendum to send. Skipping email.")
        return

    # Corrected keyword argument from 'template' to 'template_name'
    html_content_body: str = notifier_service.render_email_body(
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
