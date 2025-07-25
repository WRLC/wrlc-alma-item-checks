"""Dependencies for the database connection"""
from src.wrlc_alma_item_checks.repositories.database import SessionMaker


def get_db():
    """Function to get the database session."""
    db = SessionMaker()
    try:
        yield db
    finally:
        db.close()
