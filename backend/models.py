from sqlalchemy import Column, Integer, String, JSON, DateTime # type: ignore
from sqlalchemy.sql import func # type: ignore
from database import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_session_id = Column(String, index=True)
    role = Column(String)  # 'user' or 'bot'
    content = Column(JSON) # Store message content as JSON
    created_at = Column(DateTime, server_default=func.now())