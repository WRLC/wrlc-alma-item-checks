""" SQLAlchemy SessionMaker """
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker

from src.wrlc_alma_item_checks.config import SQLALCHEMY_CONNECTION_STRING

Engine: Engine = create_engine(SQLALCHEMY_CONNECTION_STRING, echo=True)
SessionMaker: sessionmaker = sessionmaker(bind=Engine)
