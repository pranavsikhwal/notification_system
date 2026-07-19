from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# What a client sends when CREATING a notification
class NotificationCreate(BaseModel):
    user_id: int
    message: str
    type: str = "info"

# What we send back to the client (includes DB-generated fields)
class NotificationOut(BaseModel):
    id: int
    user_id: int
    message: str
    type: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True  # lets Pydantic read directly from SQLAlchemy objects