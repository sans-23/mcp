from sqlalchemy import Column, Integer, String, DateTime # type: ignore
from sqlalchemy.sql import func # type: ignore
from db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
