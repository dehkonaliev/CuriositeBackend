import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.exceptions import ValidationError

from chat.models import Conversation, ConversationParticipant, Message, UnreadMessage
from chat.serializers import MessageSerializer


class ChatConsumer(AsyncJsonWebsocketConsumer):

    RATE_LIMIT_MESSAGES = 100
    RATE_LIMIT_WINDOW_SECONDS = 100

    # ---------- connection lifecycle ----------

    async def connect(self):
        self.user = self.scope["user"]
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.group_name = f"conversation_{self.conversation_id}"
        self._message_timestamps = []

        if not self.user.is_authenticated:
            await self.close(code=4001)
            return

        self.conversation = await self.get_conversation()
        if self.conversation is None:
            await self.close(code=4004)
            return

        is_participant = await self.check_participant()
        if not is_participant:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "presence_event",
                "user_id": str(self.user.id),
                "user_name": str(self.user),
                "status": "online",
            },
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "presence_event",
                    "user_id": str(self.user.id),
                    "user_name": str(self.user),
                    "status": "offline",
                },
            )
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # ---------- incoming message router ----------

    async def receive_json(self, content, **kwargs):
        message_type = content.get("type", "message")

        if message_type == "ping":
            await self.send_json({"type": "pong"})
            return

        if message_type == "typing":
            await self.handle_typing(content)
            return

        if message_type == "read":
            await self.handle_read(content)
            return

        if not self._check_rate_limit():
            await self.send_json({
                "type": "error",
                "errors": {"detail": "Too many messages. Slow down."},
            })
            return

        message, errors = await self.save_message(content)

        if errors:
            await self.send_json({"type": "error", "errors": errors})
            return

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat_message",
                "id": str(message.id),
                "conversation": str(message.conversation_id),
                "sender": str(message.sender_id),
                "sender_name": str(message.sender),
                "content": message.content,
                "reply_to": str(message.reply_to_id) if message.reply_to_id else None,
                "created_at": message.created_at.isoformat(),
            },
        )

    # ---------- group event handlers ----------

    async def chat_message(self, event):
        await self.send_json(event)

    async def typing_event(self, event):
        if event["user_id"] == str(self.user.id):
            return
        await self.send_json(event)

    async def presence_event(self, event):
        await self.send_json(event)

    async def read_event(self, event):
        if event["user_id"] == str(self.user.id):
            return
        await self.send_json(event)

    # ---------- typing ----------

    async def handle_typing(self, content):
        is_typing = content.get("is_typing", False)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "typing_event",
                "user_id": str(self.user.id),
                "user_name": str(self.user),
                "is_typing": is_typing,
            },
        )

    # ---------- read receipts ----------

    async def handle_read(self, content):
        message_id = content.get("message_id")
        if not message_id:
            return

        deleted_ids = await self.mark_read_up_to(message_id)
        if not deleted_ids:
            return

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "read_event",
                "message_ids": deleted_ids,
                "user_id": str(self.user.id),
            },
        )

    @database_sync_to_async
    def mark_read_up_to(self, message_id):
        try:
            target = Message.objects.get(pk=message_id, conversation_id=self.conversation_id)
        except (Message.DoesNotExist, ValidationError, ValueError):
            return []

        qs = UnreadMessage.objects.filter(
            conversation_id=self.conversation_id,
            user=self.user,
            message__created_at__lte=target.created_at,
        )
        message_ids = list(qs.values_list("message_id", flat=True))
        qs.delete()
        return [str(mid) for mid in message_ids]

    # ---------- rate limiting ----------

    def _check_rate_limit(self):
        now = time.monotonic()
        cutoff = now - self.RATE_LIMIT_WINDOW_SECONDS

        self._message_timestamps = [t for t in self._message_timestamps if t > cutoff]

        if len(self._message_timestamps) >= self.RATE_LIMIT_MESSAGES:
            return False

        self._message_timestamps.append(now)
        return True

    # ---------- db helpers ----------

    @database_sync_to_async
    def get_conversation(self):
        return Conversation.objects.filter(pk=self.conversation_id).first()

    @database_sync_to_async
    def check_participant(self):
        return ConversationParticipant.objects.filter(
            conversation_id=self.conversation_id, user=self.user
        ).exists()

    @database_sync_to_async
    def save_message(self, data):
        serializer = MessageSerializer(
            data=data,
            context={"conversation": self.conversation, "sender": self.user},
        )
        if serializer.is_valid():
            message = serializer.save()
            return message, None
        return None, serializer.errors