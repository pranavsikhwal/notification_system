import json
import asyncio
from redis_client import redis_client
from connection_manager import manager, CHANNEL_NAME

async def redis_listener():   #creating a function that keeps listening forever 
    pubsub = redis_client.pubsub()  #creates the subscriber part 
    await pubsub.subscribe(CHANNEL_NAME)  
    print(f"Subscribed to Redis channel: {CHANNEL_NAME}")

    async for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            user_id = data["user_id"]
            notification_payload = data["message"]
            await manager.send_notification(user_id, notification_payload)
            
          #dumps need to convert Python to json and loads does the opposite work 