from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.chat import ChatSession, ChatMessage
from uuid import uuid4
from typing import List

async def create_chat_session(db: AsyncSession, user_id: int, initial_message: str):
    session_id = str(uuid4())
    initial_title = initial_message[:30] + "..."
    
    new_session = ChatSession(id=session_id, user_id=user_id, title=initial_title)
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    user_message = ChatMessage(
        chat_session_id=session_id,
        role="user",
        content={"text": initial_message}
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)
    
    return new_session, user_message

async def add_ai_message_to_session(db: AsyncSession, session_id: str, ai_response_text: str, tools_used: List[str] = None):
    """Adds an AI message to a session, optionally including tools used."""
    ai_message = ChatMessage(
        chat_session_id=session_id,
        role="ai",
        content={"text": ai_response_text.strip()},
        tool_used=", ".join(tools_used) if tools_used else None
    )
    db.add(ai_message)
    await db.commit()
    await db.refresh(ai_message)
    return ai_message

async def get_chat_session(db: AsyncSession, session_id: str):
    result = await db.execute(select(ChatSession).filter(ChatSession.id == session_id))
    return result.scalars().first()

async def get_chat_messages(db: AsyncSession, session_id: str):
    result = await db.execute(
        select(ChatMessage)
        .filter(ChatMessage.chat_session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    return result.scalars().all()

async def get_user_sessions(db: AsyncSession, user_id: int):
    result = await db.execute(
        select(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
    )
    return result.scalars().all()

async def add_user_message_to_session(db: AsyncSession, session_id: str, content: str):
    user_message = ChatMessage(
        chat_session_id=session_id,
        role="user",
        content={"text": content}
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)
    return user_message
