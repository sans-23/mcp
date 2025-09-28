from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """Pydantic model for creating a new user."""
    username: str = Field(..., description="The username for the new user.")

class UserSchema(BaseModel):
    """Pydantic model for a user record."""
    id: int
    username: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
