from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey # type: ignore
from sqlalchemy.sql import func # type: ignore
from db.base import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String, index=True, default="New Chat")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_session_id = Column(String, ForeignKey("chat_sessions.id"), index=True)
    role = Column(String)  # 'user' or 'ai'
    is_summary = Column(Integer, default=0)  # 1 if summary message, else 0
    tool_used = Column(String, nullable=True)  # Name of the tool used, if any
    content = Column(JSON) # Store message content as JSON
    created_at = Column(DateTime, server_default=func.now())
