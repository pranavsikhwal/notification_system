from fastapi import FastAPI, Depends, HTTPException ,WebSocket,WebSocketDisconnect
from sqlalchemy.orm import Session
from connection_manager import manager
from dependencies import get_current_user
from database import engine, get_db, Base
from models import Notification
from schemas import NotificationCreate, NotificationOut

from fastapi import Query
from auth_utils import decode_access_token
from jose import JWTError
from fastapi.security import OAuth2PasswordRequestForm
from auth_utils import hash_password, verify_password, create_access_token
from models import User
from schemas import UserCreate, UserOut, Token

# This line actually creates the tables in your database based on models.py
Base.metadata.create_all(bind=engine)
#In production we use Alembic migration tool instead of this . 

from contextlib import asynccontextmanager #this is used to manage application lifespan 
import asyncio
from redis_listener import redis_listener

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: launch the Redis listener as a background task
    task = asyncio.create_task(redis_listener())
    yield
    # Shutdown: cancel the listener task cleanly
    task.cancel()

app = FastAPI(title="Notification System API", lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#notification sent by client is getting saved in db 
@app.post("/notifications", response_model=NotificationOut)
async def create_notification(payload: NotificationCreate,current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_notification = Notification(
        user_id = current_user.id,
        message=payload.message,
        type=payload.type
    )
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    
    await manager.publish_notification(new_notification.user_id, {
    "id": new_notification.id,
    "user_id": new_notification.user_id,
    "message": new_notification.message,
    "type": new_notification.type,
    "is_read": new_notification.is_read,
    "created_at": new_notification.created_at.isoformat(),
    })

    #"Earlier, the API only saved notifications in the database, so users had to refresh the page to see new ones. I made the endpoint asynchronous and added manager.send_notification() so that after saving the notification, it is pushed instantly to users who have an active WebSocket connection, enabling real-time updates."
    return new_notification
  
#sending a list of all the notifications of a particular user 
from typing import Optional

@app.get("/notifications", response_model=list[NotificationOut])
def get_notifications(
    before_id: Optional[int] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)

    if before_id is not None:
        query = query.filter(Notification.id < before_id)

    notifications = query.order_by(Notification.id.desc()).limit(limit).all()
    return notifications
#PATCH is used when you want to update only part of an existing resource. Here, we're only changing one field (is_read), not replacing the entire notification 
@app.patch("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this notification")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
  
#Browsers don't allow custom headers during the WebSocket handshake, so we can't send Authorization: Bearer <token> like we do with REST APIs. The common solution is to send the JWT as a query parameter (or use cookies) and verify it on the server before accepting the WebSocket connection
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except JWTError:
        await websocket.close(code=1008)  # 1008 = policy violation
        return

    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        
        
        
@app.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


#to count the unread notifications 
@app.get("/notifications/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = db.query(Notification)\
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)\
        .count()
    return {"unread_count": count}