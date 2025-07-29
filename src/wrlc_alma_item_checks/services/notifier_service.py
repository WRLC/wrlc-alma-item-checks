"""Service for sending emails using Azure Communication Service (ACS)."""
import io
import logging
import pathlib
import uuid

import azure.functions as func
from azure.storage.blob import BlobClient
from jinja2 import Template, TemplateNotFound, Environment, FileSystemLoader, select_autoescape
import pandas as pd

from ..config import (
    NOTIFIER_CONTAINER_NAME, ACS_SENDER_CONNECTION_STRING, ACS_SENDER_CONTAINER_NAME
)
from ..models.check import Check
from ..models.email import EmailMessage
from .storage_service import StorageService


# noinspection PyMethodMayBeStatic
class NotifierService:
    """Service for preparting and queuing notifications."""

    def __init__(self):
        # Initialize the Jinja2 environment once in the constructor for efficiency
        self.jinja_env: Environment | None = None
        try:
            template_dir = pathlib.Path(__file__).parent.parent / "templates"
            if not template_dir.is_dir():
                logging.error(f"Jinja template directory not found at: {template_dir}")
                raise FileNotFoundError(f"Jinja template directory not found: {template_dir}")

            self.jinja_env = Environment(
                loader=FileSystemLoader(template_dir),
                autoescape=select_autoescape(['html', 'xml'])
            )
            logging.info(f"Jinja2 environment loaded successfully from: {template_dir}")
        except Exception as e:
            logging.exception(f"Failed to initialize Jinja2 environment: {e}")
            # The service can continue, but render_email_body will fail gracefully.

    def render_email_body(
            self, template_name: str, check: Check, body_addendum: str, html_table: str, job_id: str
    ) -> str | None:
        """
        Render the email body using the provided template and context.

        Args:
            template_name (str): The name of the email template file.
            check (Check): The check object containing email subject and body.
            body_addendum (str): Additional text to append to the email body.
            html_table (str): The HTML table to include in the email body.
            job_id (str): The job ID for logging purposes.

        Returns:
             The rendered email body as a string, or None on failure.
        """
        if not self.jinja_env:
            logging.error(f"Job {job_id}: Cannot render email, Jinja2 environment not available.")
            return None
        try:
            template: Template = self.jinja_env.get_template(template_name)
            template_context = {
                "email_caption": check.email_subject,
                "email_body": check.email_body,
                "body_addendum": body_addendum,
                "data_table_html": html_table,
                "job_id": job_id,
            }
            html_content_body: str = template.render(template_context)
            logging.debug(f"Job {job_id}: Email template rendered successfully.")
            return html_content_body
        except TemplateNotFound as template_err:
            logging.error(f"Job {job_id}: Template not found: {template_err}", exc_info=True)
            return None
        except Exception as render_err:
            logging.error(f"Job {job_id}: Error rendering template: {render_err}", exc_info=True)
            return None

    def send_email(self, email_message: EmailMessage, job_id: str) -> None:
        """
        Serializes an email message to a blob, which will trigger the downstream email sending service.

        Args:
            email_message (EmailMessage): The email message to send.
            job_id (str): The job ID for logging purposes.

        """
        if not all([ACS_SENDER_CONNECTION_STRING, ACS_SENDER_CONTAINER_NAME]):
            logging.error(
                f"Job {job_id}: ACS sender connection string or container name is not configured. "
                "Cannot create email blob."
             )
            raise ValueError("ACS sender service is not fully configured in application settings.")

        try:
            blob_name = f"{job_id}-{uuid.uuid4()}.json"
            email_json_content = email_message.model_dump_json()

            logging.info(f"Job {job_id}: Uploading email content to blob '{ACS_SENDER_CONTAINER_NAME}/{blob_name}'.")
            blob_client = BlobClient.from_connection_string(
                conn_str=ACS_SENDER_CONNECTION_STRING,
                container_name=ACS_SENDER_CONTAINER_NAME,
                blob_name=blob_name
            )

            blob_client.upload_blob(email_json_content, overwrite=True)
            logging.info(f"Job {job_id}: Successfully uploaded email content blob.")

        except Exception as e:
            logging.exception(f"Job {job_id}: Failed to create blob for email message: {e}")
            raise e

    def create_html_table(self, msg: func.QueueMessage, job_id: str, check: Check) -> str | None:
        """
        Create an HTML table from JSON data stored in Azure Blob Storage.

        Args:
            msg (func.QueueMessage): The message containing the job ID and check ID.
            job_id (str): The job ID for logging purposes.
            check (Check): The check object containing email subject.

        Returns:
            str | None: The HTML table as a string, or None if an error occurs.

        """
        html_table: str | None = None

        if msg.get_json().get("combined_data_blob"):
            combined_data_blob = msg.get_json().get("combined_data_blob")

            combined_data_container = NOTIFIER_CONTAINER_NAME

            storage_service: StorageService = StorageService()

            try:
                combined_data: str | None = storage_service.download_blob_as_text(
                    container_name=combined_data_container,
                    blob_name=combined_data_blob,
                )
            except Exception as val_err:
                logging.error(f"EJob {job_id}: Error downloading blob: {val_err}")
                return None

            # Convert JSON to HTML Table
            html_table = "Error generating table from data."
            # noinspection PyUnusedLocal
            record_count = 0
            try:
                if combined_data:
                    json_io = io.StringIO(combined_data)
                    df = pd.read_json(json_io, orient='records')  # Adjust 'orient' if needed
                    df.style.set_caption(check.email_subject)

                    # Check if column '0' exists and all its values are '0' (as string or int)
                    if '0' in df.columns and df['0'].astype(str).eq('0').all():
                        logging.debug(f"Job {job_id}: Column '0' contains only '0' values. Dropping column.")
                        df.drop('0', axis=1, inplace=True)

                    record_count = len(df)
                    logging.debug(f"Job {job_id}: Read {record_count} rows into DataFrame.")
                    if not df.empty:
                        html_table = df.to_html(
                            index=False, border=1, escape=True, na_rep=''
                        ).replace(
                            'border="1"',
                            'border="1" style="border-collapse: collapse; border: 1px solid black;"'
                        )
                        logging.debug(f"Job {job_id}: Converted DataFrame to HTML string.")
                    else:
                        html_table = (
                            f"<i>Report generated, but contained no displayable data.</i><br>"
                        )
                else:
                    logging.warning(f"Job {job_id}: No JSON data string available for conversion.")
                    return None
            except Exception as convert_err:
                logging.error(f"Job {job_id}: Failed JSON->HTML conversion: {convert_err}", exc_info=True)

        return html_table
