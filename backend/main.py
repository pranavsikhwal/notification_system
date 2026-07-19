from fastapi import FastAPI, Depends, HTTPException ,WebSocket,WebSocketDisconnect
from sqlalchemy.orm import Session
from connection_manager import manager

from database import engine, get_db, Base
from models import Notification
from schemas import NotificationCreate, NotificationOut

# This line actually creates the tables in your database based on models.py
Base.metadata.create_all(bind=engine)
#In production we use Alembic migration tool instead of this . 

app = FastAPI(title="Notification System API")

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
async def create_notification(payload: NotificationCreate, db: Session = Depends(get_db)):
    new_notification = Notification(
        user_id=payload.user_id,
        message=payload.message,
        type=payload.type
    )
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    
    await manager.send_notification(new_notification.user_id, {
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
@app.get("/notifications", response_model=list[NotificationOut])
def get_notifications(user_id: int, db: Session = Depends(get_db)):
    notifications = db.query(Notification)\
        .filter(Notification.user_id == user_id)\
        .order_by(Notification.created_at.desc())\
        .all()
    return notifications
  
#PATCH is used when you want to update only part of an existing resource. Here, we're only changing one field (is_read), not replacing the entire notification 
@app.patch("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_as_read(notification_id: int, db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
  
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    print(f"User {user_id} is trying to connect")
    await manager.connect(user_id, websocket)
    try:
        while True:
            # Keeps the connection alive, listening for any client-side messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)