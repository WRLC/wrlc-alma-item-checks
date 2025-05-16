from sqlalchemy.orm import sessionmaker
from src.wrlc.alma.item_checks.config import SQLALCHEMY_CONNECTION_STRING
from sqlalchemy import create_engine, Engine

Engine: Engine = create_engine(SQLALCHEMY_CONNECTION_STRING, echo=True)
SessionMaker = sessionmaker(bind=Engine)
