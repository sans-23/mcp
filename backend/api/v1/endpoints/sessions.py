from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.chat import SessionCreate, ChatSessionResponse, MessageRequest, MessageResponse, SessionListResponse, ChatMessageResponse
from crud import chat as chat_crud
from crud import user as user_crud
from db.session import get_db_session
import backend.services.services as services

router = APIRouter()

@router.post("/", response_model=ChatSessionResponse, status_code=201)
async def create_session(
    session_data: SessionCreate, 
    db: AsyncSession = Depends(get_db_session)
):
    """Starts a new chat session for a user."""
    if services.agent_executor is None:
        raise HTTPException(status_code=503, detail="Agent is not initialized.")
        
    user = await user_crud.get_user_by_id(db, session_data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    new_session, _ = await chat_crud.create_chat_session(
        db, session_data.user_id, session_data.initial_message
    )
    
    ai_response_text, tool_names_used = await services.get_agent_response(
        services.agent_executor, session_data.initial_message, []
    )
    
    await chat_crud.add_ai_message_to_session(
        db, new_session.id, ai_response_text, tool_names_used
    )
    
    messages = await chat_crud.get_chat_messages(db, new_session.id)
    
    return ChatSessionResponse(
        id=new_session.id,
        user_id=new_session.user_id,
        title=new_session.title,
        created_at=new_session.created_at,
        updated_at=new_session.updated_at,
        messages=[ChatMessageResponse.from_orm(m) for m in messages]
    )

@router.post("/chat", response_model=MessageResponse)
async def send_message(
    message_data: MessageRequest, 
    db: AsyncSession = Depends(get_db_session)
):
    """Sends a new message to an existing chat session."""
    if services.agent_executor is None:
        raise HTTPException(status_code=503, detail="Agent is not initialized.")
        
    session = await chat_crud.get_chat_session(db, message_data.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
    
    if session.user_id != message_data.user_id:
        raise HTTPException(status_code=403, detail="Forbidden: User ID does not match session owner.")
        
    history_records = await chat_crud.get_chat_messages(db, message_data.session_id)
    lc_history = services.db_messages_to_lc_messages(history_records)
    
    user_message = await chat_crud.add_user_message_to_session(
        db, message_data.session_id, message_data.content
    )
    
    ai_response_text, tool_names_used = await services.get_agent_response(
        services.agent_executor, message_data.content, lc_history
    )
    
    ai_message = await chat_crud.add_ai_message_to_session(
        db, message_data.session_id, ai_response_text, tool_names_used
    )
    
    return MessageResponse(
        session_id=message_data.session_id,
        user_message=ChatMessageResponse.from_orm(user_message),
        ai_response=ChatMessageResponse.from_orm(ai_message),
        tool_names_used=tool_names_used
    )

@router.get("/{session_id}", response_model=ChatSessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db_session)):
    """Retrieves a specific chat session and all its messages."""
    session = await chat_crud.get_chat_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found.")
        
    messages = await chat_crud.get_chat_messages(db, session_id)
    
    return ChatSessionResponse(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[ChatMessageResponse.from_orm(m) for m in messages]
    )

@router.get("/user/{user_id}", response_model=SessionListResponse)
async def list_user_sessions(user_id: int, db: AsyncSession = Depends(get_db_session)):
    """Lists all chat sessions for a specific user."""
    sessions = await chat_crud.get_user_sessions(db, user_id)
    return SessionListResponse(
        sessions=[
            ChatSessionResponse(
                id=s.id,
                user_id=s.user_id,
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at,
                messages=[]
            ) for s in sessions
        ]
    )
