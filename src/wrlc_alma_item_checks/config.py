"""Configuration for the Alma Item Checks application."""
import os


def _get_required_env(var_name: str) -> str:
    """Gets a required environment variable or raises a ValueError."""
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Missing required environment variable: '{var_name}'")
    return value


# --- Core Application Settings (Required) ---
STORAGE_CONNECTION_STRING: str = _get_required_env("AzureWebJobsStorage")
SQLALCHEMY_CONNECTION_STRING: str = _get_required_env("SQLALCHEMY_CONNECTION_STRING")

# --- Notifier Settings (Required for notifier functionality) ---
NOTIFIER_QUEUE_NAME: str = _get_required_env("NOTIFIER_QUEUE_NAME")
NOTIFIER_CONTAINER_NAME: str = _get_required_env("NOTIFIER_CONTAINER_NAME")
TEMPLATE_FILE_NAME = "email_template.html.j2"

# --- Azure Communication Services (Required for sending emails) ---
ACS_SENDER_CONTAINER_NAME: str = _get_required_env("ACS_SENDER_CONTAINER_NAME")
ACS_STORAGE_CONNECTION_STRING: str = _get_required_env("ACS_STORAGE_CONNECTION_STRING")

# --- SCF Duplicates Timer (Required for the timer trigger) ---
SCF_DUPLICATES_SCHEDULE: str = _get_required_env("SCF_DUPLICATES_SCHEDULE")
SCF_DUPLICATES_CHECK_NAME: str = _get_required_env("SCF_DUPLICATES_CHECK_NAME")

# --- SCF Webhook (Required for the webhook) ---
SCF_WEBHOOK_SECRET: str = _get_required_env("SCF_WEBHOOK_SECRET")

# Disable email
DISABLE_EMAIL: bool = False
disable_email_setting: str | None = os.environ.get("DISABLE_EMAIL")

if disable_email_setting and disable_email_setting.strip().lower() in ("true", "1", "yes", "on"):
    DISABLE_EMAIL = True

# --- Business Logic Constants ---
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

EXCLUDED_NOTES = [
    'At WRLC waiting to be processed',
    'DO NOT DELETE',
    'WD'
]

SKIP_LOCATIONS = [
    "WRLC Gemtrac Drawer",
    "WRLC Microfilm Cabinet",
    "WRLC Microfiche Cabinet",
    "Low Temperature Media Preservation Unit  # 1 @ SCF"
]
