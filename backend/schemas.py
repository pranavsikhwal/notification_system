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

#now these three classes usercrete , userout and token are for user authentication and jwt token purpose .      
class UserCreate(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    email: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str