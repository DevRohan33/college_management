# import json
# from channels.generic.websocket import AsyncWebsocketConsumer


# class ClubChatConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.club_id = self.scope['url_route']['kwargs']['unique_id']
#         self.room_group_name = f"club_{self.club_id}"

#         # Join room group
#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )

#         await self.accept()

#     async def disconnect(self, close_code):
#         # Leave room group
#         await self.channel_layer.group_discard(
#             self.room_group_name,
#             self.channel_name
#         )

#     async def receive(self, text_data):
#         """Handle incoming messages from client.
#         Expected payloads from the frontend:
#           - {"type": "chat_message", "message": "..."}
#           - {"type": "typing"}
#         """
#         try:
#             data = json.loads(text_data)
#         except Exception:
#             return

#         event_type = data.get("type", "chat_message")

#         # Resolve username (may be Anonymous if unauthenticated)
#         username = None
#         try:
#             user = self.scope.get("user")
#             if user and getattr(user, "is_authenticated", False):
#                 username = user.username
#         except Exception:
#             pass
#         username = username or "Anonymous"

#         if event_type == "typing":
#             # Broadcast typing indicator
#             await self.channel_layer.group_send(
#                 self.room_group_name,
#                 {
#                     "type": "typing",  # calls self.typing()
#                     "user": username,
#                 }
#             )
#             return

#         # Default: chat message
#         message = (data.get("message") or "").strip()
#         if not message:
#             return

#         await self.channel_layer.group_send(
#             self.room_group_name,
#             {
#                 "type": "chat_message",  # calls self.chat_message()
#                 "message": message,
#                 "user": username,
#             }
#         )

#     async def chat_message(self, event):
#         await self.send(text_data=json.dumps({
#             "type": "chat_message",
#             "message": event.get("message", ""),
#             "user": event.get("user", "System"),
#         }))

#     async def typing(self, event):
#         await self.send(text_data=json.dumps({
#             "type": "typing",
#             "user": event.get("user", "Someone"),
#         }))


# # Backwards compatibility alias (if any other import still uses ChatConsumer)
# ChatConsumer = ClubChatConsumer
