import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"

        # Check user is participant
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return

        is_participant = await self.check_participant(user, self.conversation_id)
        if not is_participant:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type", "message")

        if message_type == "message":
            user = self.scope["user"]
            content = data.get("content", "").strip()
            if not content:
                return

            message = await self.save_message(user, self.conversation_id, content)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": {
                        "id": str(message.id),
                        "content": message.content,
                        "author": str(user.id),
                        "author_name": user.get_full_name() or user.email,
                        "created_at": message.created_at.isoformat(),
                    }
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    @database_sync_to_async
    def check_participant(self, user, conversation_id):
        from .models import ChatConversation
        try:
            conv = ChatConversation.objects.get(id=conversation_id)
            return conv.participants.filter(id=user.id).exists()
        except ChatConversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, user, conversation_id, content):
        from .models import ChatConversation, ChatMessage
        conv = ChatConversation.objects.get(id=conversation_id)
        msg = ChatMessage.objects.create(
            conversation=conv,
            author=user,
            content=content,
        )
        conv.last_message_at = timezone.now()
        conv.save(update_fields=["last_message_at"])
        return msg
