import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ClubChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.club_id = self.scope['url_route']['kwargs']['unique_id']
        self.room_group_name = f"club_{self.club_id}"

        # Join room
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]

        # Send message to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"]
        }))
