from pydantic import BaseModel, Field # type: ignore
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    query: str = Field(..., description="The user's query.")
    chat_id: Optional[str] = Field(None, description="Unique ID for the chat session. A new chat is started if not provided.")

class ChatResponse(BaseModel):
    response: str = Field(..., description="The response from the AI.")
    chat_id: str = Field(..., description="The ID of the chat session.")

class MessageResponse(BaseModel):
    id: int
    chat_session_id: str
    role: str
    content: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatHistoryResponse(BaseModel):
    chat_id: str
    messages: List[MessageResponse]