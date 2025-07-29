"""Notifier blueprint for Alma item checks."""
import logging

import azure.functions as func
from sqlalchemy.exc import SQLAlchemyError, NoResultFound
from sqlalchemy.orm import Session

from ..config import NOTIFIER_QUEUE_NAME, NOTIFIER_CONTAINER_NAME, TEMPLATE_FILE_NAME
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
        "check_id": "123456",
        "combined_data_blob": "...",
        "email_body_addendum": "..."
    }
    """
    try:  # Get the job ID and check ID from the message
        job_id: str = msg.get_json().get("job_id")
        check_id: int = msg.get_json().get("check_id")
    except ValueError as val_err:
        logging.error(f"Missing job_id or check_id in JSON request: {val_err}")
        return
    except Exception as val_err:
        logging.error(f"Unexpected error processing message: {val_err}", exc_info=True)
        return

    db: Session = SessionMaker()  # get database session

    try:
        check_repo: CheckRepository = CheckRepository(db)  # get check repository
        check: Check = check_repo.get_check_by_id(check_id)  # get check by id

        user_repo: UserRepository = UserRepository(db)  # get user repository
        users: list[User] = user_repo.get_users_by_check_id(check_id)  # get users by check id
    except NoResultFound:
        logging.error(f"No check or user found for job {job_id}. Exiting.")
        return
    except SQLAlchemyError as val_err:
        logging.error(f"Job {job_id}: Database error: {val_err}")
        return
    except Exception as val_err:
        logging.error(f"Job {job_id}: Unexpected error: {val_err}", exc_info=True)
        return
    finally:
        db.close()  # close database session

    if not users:  # check if users exist
        logging.error(f"No users found for job {job_id}. Exiting.")
        return

    notifier_service: NotifierService = NotifierService()  # get notifier service

    html_table: str | None = notifier_service.create_html_table(  # create HTML table from JSON data
        msg=msg,
        job_id=job_id,
        check=check
    )

    body_addendum: str | None = None  # initialize email body addendum

    if msg.get_json().get("email_body_addendum"):  # check if email body addendum exists)
        body_addendum: str = msg.get_json().get("email_body_addendum")  # get email body addendum

    html_content_body: str = notifier_service.render_email_body(  # render email body
        template=TEMPLATE_FILE_NAME,
        check=check,
        body_addendum=body_addendum,
        html_table=html_table,
        job_id=job_id
    )
    email_to_send: EmailMessage = EmailMessage(
        to=[user.email for user in users],
        subject=check.email_subject,
        html=html_content_body
    )

    notifier_service.send_email(email_message=email_to_send, job_id=job_id)
