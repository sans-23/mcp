from pydantic import BaseModel, Field # type: ignore
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

class QandAProps(BaseModel):
    """Properties for a simple text/Q&A component."""
    content: str = Field(..., description="The main text content.")

class TableProps(BaseModel):
    """Properties for a tabular data component."""
    columns: List[Dict[str, Any]] = Field(..., description="A list of column definitions.")
    rows: List[Dict[str, Any]] = Field(..., description="The list of data rows.")

class CodeProps(BaseModel):
    """Properties for a code block component."""
    code: str = Field(..., description="The code to be displayed.")
    language: Optional[str] = Field(None, description="The programming language for syntax highlighting.")

class ImageProps(BaseModel):
    """Properties for an image component."""
    url: str = Field(..., description="The URL of the image.")
    alt_text: str = Field(..., description="Alternative text for accessibility.")

# Your Superclass model as the main output schema
class Superclass(BaseModel):
    """The main response schema, which can be any of the component types."""
    # We use Union to allow the model to select one of the defined component models
    response: Union[
        QandAProps,
        TableProps,
        CodeProps,
        ImageProps
    ] = Field(..., description="The structured response in a format that best fits the user's query.")

class ChatRequest(BaseModel):
    query: str = Field(..., description="The user's query.")
    chat_id: Optional[str] = Field(None, description="Unique ID for the chat session. A new chat is started if not provided.")

class ChatResponse(BaseModel):
    response: str = Field(..., description="The response from the AI.")
    chat_id: str = Field(..., description="The ID of the chat session.")
    tool_used: Optional[str] = Field(None, description="The tool used to generate the response, if any.")

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

# --- Request Models ---

class UserCreate(BaseModel):
    """Pydantic model for creating a new user."""
    username: str = Field(..., description="The username for the new user.")

class SessionCreate(BaseModel):
    """Pydantic model for initiating a new chat session with a user and an initial message."""
    user_id: int = Field(..., description="The ID of the user creating the session.")
    initial_message: str = Field(..., description="The user's first message in the session.")
    
class MessageRequest(BaseModel):
    """Pydantic model for sending a new message to an existing chat session."""
    session_id: str = Field(..., description="The ID of the chat session to which the message belongs.")
    user_id: int = Field(..., description="The ID of the user sending the message.")
    content: str = Field(..., description="The content of the new message.")
    
# --- Response Models ---

class UserSchema(BaseModel):
    """Pydantic model for a user record."""
    id: int
    username: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ChatMessageResponse(BaseModel):
    """Pydantic model for a single chat message in a response."""
    id: int
    chat_session_id: str
    role: str
    content: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

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