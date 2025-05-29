"""Configuration for the Alma Item Checks application."""
import os

SQLALCHEMY_CONNECTION_STRING: str = os.getenv("SQLALCHEMY_CONNECTION_STRING", "sqlite:///alma_item_checks.db")

STORAGE_CONNECTION_STRING_NAME: str = os.getenv("STORAGE_CONNECTION_STRING_NAME", "AzureWebJobsStorage")
NOTIFIER_QUEUE_NAME: str = os.getenv("NOTIFIER_QUEUE_NAME", "alma-item-checks-input-queue")
NOTIFIER_CONTAINER_NAME: str = os.getenv("NOTIFIER_CONTAINER_NAME", "alma-item-checks-input-container")

ACS_CONNECTION_STRING: str = os.getenv("ACS_CONNECTION_STRING")
ACS_ENDPOINT: str = os.getenv("ACS_ENDPOINT")
SENDER_ADDRESS: str = os.getenv("SENDER_ADDRESS")

SCF_DUPLICATES_SCHEDULE: str = os.getenv("SCF_DUPLICATES_SCHEDULE")
SCF_DUPLICATES_CHECK_NAME: str = os.getenv("SCF_DUPLICATES_CHECK_NAME")

SCF_WEBHOOK_SECRET: str = os.getenv("SCF_WEBHOOK_SECRET")

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
