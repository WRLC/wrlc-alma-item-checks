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
