"""FastAPI CRUD API for WRLC Alma Item Checks."""
from fastapi import FastAPI, Depends, APIRouter
from typing import List
from sqlalchemy.orm import Session
from src.wrlc.alma.item_checks.api.models.check import Check, CheckCreate, CheckUpdate
from src.wrlc.alma.item_checks.api.dependencies import get_db
from src.wrlc.alma.item_checks.repositories.check_repo import CheckRepository


# noinspection PyArgumentEqualDefault
crud_api_app = FastAPI(
    title="WRLC Alma Item Checks CRUD API",
    description="API to manage data related to WRLC Alma Item Checks",
    version="0.1.0",
)
router = APIRouter(prefix="/api")


@crud_api_app.post("/checks/", response_model=Check, status_code=201)
async def create_check(
    check_in: CheckCreate,
    db: Session = Depends(get_db)
) -> Check:
    """
    Create a new check.

    Args:
        check_in (CheckCreate): the check to create.
        db (Session): the database session

    Returns:
        Check: the created check

    """
    check_repo = CheckRepository(db)
    db_check = check_repo.create_check(check_data=check_in)
    return db_check


@crud_api_app.get("/checks/", response_model=List[Check])
async def read_checks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[Check]:
    """
    Read all checks.

    Args:
        skip (int): the number of checks to skip
        limit (int): the number of checks to
        db (Session): the database session

    Returns:
        List[Check]: the list of checks

    """
    check_repo = CheckRepository(db)
    checks = check_repo.get_all_checks(skip=skip, limit=limit)
    return checks


@crud_api_app.get("/checks/{check_id}", response_model=Check)
async def read_check(
    check_id: int,
    db: Session = Depends(get_db)
) -> Check:
    """
    Read a check.

    Args:
        check_id (int): the id of the check
        db (Session): the database session

    Returns:
        Check: the check

    """
    check_repo = CheckRepository(db)
    db_check = check_repo.get_check_by_id(check_id=check_id)
    return db_check


@crud_api_app.put("/checks/{check_id}", response_model=Check)
async def update_check(
    check_id: int,
    check_in: CheckUpdate,
    db: Session = Depends(get_db)
) -> Check:
    """
    Update a check.

    Args:
        check_id (int): the id of the check
        check_in (CheckUpdate): the check update object
        db (Session): the database session

    Returns:
        Check: the updated check

    """
    check_repo = CheckRepository(db)
    db_check = check_repo.update_check(check_id=check_id, check_data=check_in)
    return db_check


@crud_api_app.delete("/checks/{check_id}", response_model=Check)
async def delete_check(
    check_id: int,
    db: Session = Depends(get_db())
) -> bool:
    """
    Delete a check.

    Args:
        check_id (int): the id of the check to be deleted
        db (Session): the database session

    Returns:
        Check: the deleted check

    """
    check_repo = CheckRepository(db)
    db_check = check_repo.delete_check(check_id=check_id)
    return db_check


crud_api_app.include_router(router)
