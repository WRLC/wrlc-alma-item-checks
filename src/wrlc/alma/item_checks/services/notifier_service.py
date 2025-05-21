"""Service for sending emails using Azure Communication Service (ACS)."""
import io
import logging
import pathlib
import azure.functions as func
from azure.communication.email import EmailClient
from azure.core.exceptions import HttpResponseError, ServiceRequestError
from azure.identity import DefaultAzureCredential
from jinja2 import Template, TemplateNotFound, Environment, FileSystemLoader, select_autoescape
import pandas as pd
from src.wrlc.alma.item_checks import config
from src.wrlc.alma.item_checks.models.check import Check
from src.wrlc.alma.item_checks.services.storage_service import StorageService

NOTIFIER_CONTAINER_NAME: str = config.NOTIFIER_CONTAINER_NAME


# noinspection PyMethodMayBeStatic
class NotifierService:
    """Service for sending emails."""
    def render_email_body(
            self, template: str, check: Check, body_addendum: str, html_table: str, job_id: str
    ) -> str | None:
        """
        Render the email body using the provided template and context.

        Args:
            template (str): The email template.
            check (Check): The check object containing email subject and body.
            body_addendum (str): Additional text to append to the email body.
            html_table (str): The HTML table to include in the email body.
            job_id (str): The job ID for logging purposes.

        Returns:
            str: The rendered email body.
        """
        # noinspection PyUnusedLocal
        html_content_body: str = "Error rendering email template."

        template_dir = pathlib.Path(__file__).parent.parent / "templates"
        jinja_env: Environment | None = None

        # noinspection PyBroadException
        try:
            if not template_dir.is_dir():
                logging.error(f"Jinja template directory not found at: {template_dir}")
                raise FileNotFoundError(f"Jinja template directory not found: {template_dir}")
            else:
                jinja_env = Environment(
                    loader=FileSystemLoader(template_dir),
                    autoescape=select_autoescape(['html', 'xml'])
                )
                logging.info(f"Jinja2 environment loaded successfully from: {template_dir}")
        except Exception as e:
            logging.exception(f"Failed to initialize Jinja2 environment from {template_dir}: {e}")

        try:
            template: Template = jinja_env.get_template(template)
            template_context = {
                "email_caption": check.email_subject,
                "email_body": check.email_body,
                "body_addendum": body_addendum,
                "data_table_html": html_table,
                "job_id": job_id,
            }
            html_content_body: str = template.render(template_context)
            logging.debug(f"Job {job_id}: Email template rendered successfully.")
        except TemplateNotFound as template_err:
            logging.error(f"Job {job_id}: Template not found: {template_err}", exc_info=True)
            return None
        except Exception as render_err:
            logging.error(f"Job {job_id}: Error rendering template: {render_err}", exc_info=True)
            return None

        return html_content_body

    def send_email(self, check: Check, email: str, body: str, job_id: str, email_client: EmailClient) -> None:
        """
        Send an email using the provided sender, recipient, subject, and body.

        Args:
            check (Check): The check object containing email subject.
            email (str): The recipient's email address.
            body (str): The body of the email.
            job_id (str): The job ID for logging purposes.
            email_client (EmailClient): The email client to use for sending the email.

            """
        try:
            recipient = [{"address": email}]

            message = {
                "senderAddress": config.SENDER_ADDRESS,
                "recipients": {
                    "to": recipient
                },
                "content": {
                    "subject": check.email_subject,
                    "html": body
                }
            }

            logging.info(f"Job {job_id}: Sending email to {recipient} via ACS.")
            poller = email_client.begin_send(message)
            send_result = poller.result()
            logging.info(f"Job {job_id}: ACS send poller finished.")

            status = send_result.get('status') if isinstance(send_result, dict) else None
            message_id = send_result.get('id') if isinstance(send_result, dict) else None

            if status and status.lower() == "succeeded":
                logging.info(f"Job {job_id}: Successfully sent email via ACS. Message ID: {message_id}")
            else:
                error_details = send_result.get('error', {}) if isinstance(send_result, dict) else send_result
                logging.error(
                    f"Job {job_id}: ACS Email send finished with status: {status}. Message ID: {message_id}. Details: "
                    f"{error_details}"
                )
                raise Exception(f"ACS Email send failed with status {status}")

        except (HttpResponseError, ServiceRequestError) as acs_sdk_err:
            logging.exception(f"Job {job_id}: Azure SDK Error sending email via ACS: {acs_sdk_err}")
            raise acs_sdk_err
        except Exception as email_err:
            logging.exception(f"Job {job_id}: Failed to send email via ACS: {email_err}")
            raise email_err

        logging.info(f"Notifier finished successfully for Job ID: {job_id}")

    def create_email_client(self) -> EmailClient:
        """
        Create an email client using the Azure Communication Service (ACS) connection string or endpoint.

        Returns:
            EmailClient: The initialized email client.
        """
        if config.ACS_CONNECTION_STRING:
            logging.debug("Using ACS Connection String.")
            email_client: EmailClient = EmailClient.from_connection_string(config.ACS_CONNECTION_STRING)
        else:
            logging.debug("Using ACS Endpoint and DefaultAzureCredential.")
            credential: DefaultAzureCredential = DefaultAzureCredential()
            # noinspection PyTypeChecker
            email_client: EmailClient = EmailClient(endpoint=config.ACS_ENDPOINT, credential=credential)

        return email_client

    def create_html_table(self, msg: func.QueueMessage, job_id: str) -> str | None:
        """
        Create an HTML table from JSON data stored in Azure Blob Storage.

        Args:
            msg (func.QueueMessage): The message containing the job ID and check ID.
            job_id (str): The job ID for logging purposes.

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
