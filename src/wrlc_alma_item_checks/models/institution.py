"""Model for Institution."""
from .base import Base


class Institution(Base):
    """
    SQLAlchemy model for an institution in the Alma item checks system.
    """
    __tablename__ = 'institutions'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(20), nullable=False, unique=True)

    def __repr__(self):
        return f"<Institution(name='{self.name}', code='{self.code}')>"
