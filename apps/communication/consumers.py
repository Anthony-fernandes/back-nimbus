import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"

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
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        message_type = data.get("type", "message")

        if message_type == "typing":
            user = self.scope["user"]
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": {
                        "type": "typing",
                        "conversation": self.conversation_id,
                        "author": str(user.id),
                        "author_name": user.get_full_name() or user.email,
                    },
                },
            )
            return

        if message_type == "message":
            user = self.scope["user"]
            content = data.get("content", "").strip()
            if not content or len(content) > 10000:
                return
            reply_to = data.get("reply_to") or None

            message, participant_ids = await self.save_message(
                user, self.conversation_id, content, reply_to
            )

            payload = {
                "id": str(message.id),
                "conversation": self.conversation_id,
                "content": message.content,
                "author": str(user.id),
                "author_name": user.get_full_name() or user.email,
                "reply_to": str(message.reply_to_id) if message.reply_to_id else None,
                "created_at": message.created_at.isoformat(),
            }

            # Broadcast to conversation room
            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat_message", "message": payload},
            )

            # Also notify each participant's personal channel so they get
            # alerts even when they're not connected to this conversation
            for uid in participant_ids:
                if str(uid) != str(user.id):
                    await self.channel_layer.group_send(
                        f"user_{uid}",
                        {
                            "type": "chat_notification",
                            "message": {
                                **payload,
                                "event": "chat.new_message",
                            },
                        },
                    )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    async def chat_notification(self, event):
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
    def save_message(self, user, conversation_id, content, reply_to=None):
        from .models import ChatConversation, ChatMessage
        conv = ChatConversation.objects.get(id=conversation_id)
        reply_obj = None
        if reply_to:
            reply_obj = ChatMessage.objects.filter(id=reply_to, conversation=conv).first()
        msg = ChatMessage.objects.create(
            conversation=conv,
            author=user,
            content=content,
            reply_to=reply_obj,
        )
        conv.last_message_at = timezone.now()
        conv.save(update_fields=["last_message_at"])
        participant_ids = list(conv.participants.values_list("id", flat=True))
        return msg, participant_ids


class UserNotificationConsumer(AsyncWebsocketConsumer):
    """Personal channel — receives cross-conversation chat notifications."""

    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.group_name = f"user_{user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass  # client doesn't send anything on this channel

    async def chat_notification(self, event):
        await self.send(text_data=json.dumps(event["message"]))
