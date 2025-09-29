from pydantic import BaseModel, Field # type: ignore
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime

class TextBlock(BaseModel):
    block_type: Literal["text"] = Field("text", description="Markdown text block best for general information.")
    title: Optional[str] = Field(None, description="Optional title for the text block.")
    text: str = Field(..., description="The markdown text content.")

class ReactBlock(BaseModel):
    block_type: Literal["react"] = Field("react", description="React component block for custom rendering and complex visualizations.")
    title: Optional[str] = Field(None, description="Optional title for the React block.")
    description: Optional[str] = Field(None, description="One-liner description of the React component shows.")
    code: str = Field(..., description="Raw React component code (JSX) that can be rendered in React.")

class LLMOutputBlock(BaseModel):
    blocks: List[Union[TextBlock, ReactBlock]] = Field(..., description="List of content blocks in the LLM output.")

class ChatRequest(BaseModel):
    query: str = Field(..., description="The user's query.")
    chat_id: Optional[str] = Field(None, description="Unique ID for the chat session. A new chat is started if not provided.")

class ChatResponse(BaseModel):
    response: str = Field(..., description="The response from the AI.")
    chat_id: str = Field(..., description="The ID of the chat session.")
    tool_used: Optional[str] = Field(None, description="The tool used to generate the response, if any.")

class ChatMessageResponse(BaseModel):
    """Pydantic model for a single chat message in a response."""
    id: int
    chat_session_id: str
    role: str
    content: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class ChatHistoryResponse(BaseModel):
    chat_id: str
    messages: List[ChatMessageResponse]

class SessionCreate(BaseModel):
    """Pydantic model for initiating a new chat session with a user and an initial message."""
    user_id: int = Field(..., description="The ID of the user creating the session.")
    initial_message: str = Field(..., description="The user's first message in the session.")
    
class MessageRequest(BaseModel):
    """Pydantic model for sending a new message to an existing chat session."""
    session_id: str = Field(..., description="The ID of the chat session to which the message belongs.")
    user_id: int = Field(..., description="The ID of the user sending the message.")
    content: str = Field(..., description="The content of the new message.")
    
class ChatSessionResponse(BaseModel):
    """Pydantic model for a chat session response."""
    id: str
    user_id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[ChatMessageResponse] = Field(..., description="List of messages in the session.")

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    """Pydantic model for the response after sending a message."""
    session_id: str
    user_message: ChatMessageResponse
    ai_response: ChatMessageResponse
    tool_names_used: List[str] = Field(default=[], description="List of tools utilized by the agent.")

class SessionListResponse(BaseModel):
    """Pydantic model for listing multiple chat sessions."""
    sessions: List[ChatSessionResponse]
