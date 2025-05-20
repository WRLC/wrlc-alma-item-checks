"""FastAPI CRUD API for WRLC Alma Item Checks."""
from fastapi import FastAPI, Depends, APIRouter
from typing import List
from sqlalchemy.orm import Session
from src.wrlc.alma.item_checks.api.dependencies import get_db
from src.wrlc.alma.item_checks.api.models.check import Check, CheckCreate, CheckUpdate
from src.wrlc.alma.item_checks.api.models.user import User, UserCreate, UserUpdate
from src.wrlc.alma.item_checks.repositories.check_repo import CheckRepository
from src.wrlc.alma.item_checks.repositories.user_repo import UserRepository

# noinspection PyArgumentEqualDefault
crud_api_app = FastAPI(
    title="WRLC Alma Item Checks CRUD API",
    description="API to manage data related to WRLC Alma Item Checks",
    version="0.1.0",
)
router = APIRouter(prefix="/api")


# CHECK API
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


# USER API
@crud_api_app.post("/users/", response_model=User, status_code=201)
async def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> User:
    """
    Create a new user.

    Args:
        user_in (User): the user to create
        db (Session): the database session

    Returns:
        User: the created user

    """
    user_repo = UserRepository(db)
    db_user = user_repo.create_user(user_data=user_in)
    return db_user


@crud_api_app.get("/users/", response_model=List[User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[User]:
    """
    Read all users.

    Args:
        skip (int): the number of users to skip
        limit (int): the number of users to limit
        db (Session): the database session


    Returns:
        List[User]: the list of users

    """
    user_repo = UserRepository(db)
    users = user_repo.get_all_users(skip=skip, limit=limit)
    return users


@crud_api_app.get("/users/{user_id}", response_model=User)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db())
) -> User:
    """
    Read a user.

    Args:
        user_id (int): the id of the user
        db (Session): the database session

    Returns:
        User: the user

    """
    user_repo = UserRepository(db)
    db_user = user_repo.get_user_by_id(user_id=user_id)
    return db_user


@crud_api_app.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db)
) -> User:
    """
    Update a user.

    Args:
        user_id (int): the user ID to update
        user_in (UserUpdate): the user to update
        db (Session): the database session

    Returns:
        User: the updated user

    """
    user_repo = UserRepository(db)
    db_user = user_repo.update_user(user_id=user_id, user_data=user_in)
    return db_user


@crud_api_app.delete("/users/{user_id}", response_model=User)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db())
) -> bool:
    """
    Delete a user.

    Args:
        user_id (int): the id of the user
        db (Session): the database session

    Returns:
        User: the deleted user

    """
    user_repo = UserRepository(db)
    db_user = user_repo.delete_user(user_id=user_id)
    return db_user


crud_api_app.include_router(router)
