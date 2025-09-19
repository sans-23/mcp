from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    query: str = Field(..., description="The user's query.")
    chat_id: Optional[str] = Field(None, description="Unique ID for the chat session. A new chat is started if not provided.")

class ChatResponse(BaseModel):
    response: str = Field(..., description="The response from the AI.")
    chat_id: str = Field(..., description="The ID of the chat session.")