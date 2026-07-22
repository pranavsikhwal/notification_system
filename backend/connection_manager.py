from fastapi import WebSocket
from typing import Dict
import json
from redis_client import redis_client
CHANNEL_NAME = "notifications"   #this is redis pub/sub channel . Publisher publish and subscriber receives 
class ConnectionManager:
    def __init__(self): #It is a constructor
        # Maps user_id -> their active WebSocket connection
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):  #function calls when a user connects .
        await websocket.accept()  #accepts the websocket connection
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_notification(self, user_id: int, message: dict):
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            await websocket.send_json(message)
        #this only works if user is connected to same server . 
    async def publish_notification(self, user_id: int, message: dict):
        payload = { 
            "user_id": user_id,
            "message": message
        }
        await redis_client.publish(CHANNEL_NAME, json.dumps(payload))   #Redis Pub/Sub only transmits strings, so we serialize our dict into a JSON string before publishing via json dumps
manager = ConnectionManager() #now calling the class 

#Think of a delivery office.
# active_connections = Address book of people currently at home.
# connect() = A person arrives and registers their address.
# disconnect() = A person leaves, so their address is removed.
# send_notification() = Deliver a package to a specific person's address.
#This class manages all active WebSocket connections. When a user connects, it stores their WebSocket against their user ID. When a notification needs to be sent, it looks up that user's connection and sends the message instantly. When the user disconnects, it removes their connection from memory."
#WebSockets use async and await because network operations are non-blocking and can take time. While one client is waiting to send or receive data, the server can continue handling other connected clients efficiently.