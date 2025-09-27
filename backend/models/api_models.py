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