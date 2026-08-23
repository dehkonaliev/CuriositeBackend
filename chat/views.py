from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from baseapp.utils import error_response, success_response

from chat.models import Conversation, Message
from chat.serializers import ConversationSerializer, MessageSerializer
from rest_framework.parsers import MultiPartParser, FormParser

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

import secrets
from django_redis import get_redis_connection  # or raw `redis` client, see note below


class ConversationListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        conversations = Conversation.objects.filter(
            participants__user=request.user
        ).distinct().order_by("-created_at")

        serializer = ConversationSerializer(conversations, many=True, context={"request": request})
        return success_response(message="Conversation list", data=serializer.data)

    def post(self, request):
        participant_ids = request.data.get("participant_ids", [])
        serializer = ConversationSerializer(
            data=request.data,
            context={"request": request, "participant_ids": participant_ids},
        )
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()
        message = (
            "Conversation already exists"
            if getattr(conversation, "_reused", False)
            else "Conversation created"
        )
        return success_response(
            message=message,
            data=ConversationSerializer(conversation, context={"request": request}).data,
        )


class ConversationDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, conversation_id):
        return Conversation.objects.filter(
            pk=conversation_id, participants__user=request.user
        ).first()

    def get(self, request, conversation_id):
        conversation = self.get_object(request, conversation_id)
        if conversation is None:
            error_response(message="Conversation not found", status_code=404)

        serializer = ConversationSerializer(conversation, context={"request": request})
        return success_response(message="Conversation detail", data=serializer.data)
    
    
class MessageListPagination(PageNumberPagination):
    page_size = 30


class MessageListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, conversation_id):
        conversation = Conversation.objects.filter(
            pk=conversation_id, participants__user=request.user
        ).first()

        if conversation is None:
            return error_response(message="Conversation not found", status_code=404)

        messages = Message.objects.filter(
            conversation=conversation
        ).order_by("-created_at")

        paginator = MessageListPagination()
        page = paginator.paginate_queryset(messages, request)
        serializer = MessageSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    


class MessageFileUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, conversation_id):
        conversation = Conversation.objects.filter(
            pk=conversation_id, participants__user=request.user
        ).first()

        if conversation is None:
            return Response(
                {"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND
            )

        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response(
                {"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST
            )

        reply_to_id = request.data.get("reply_to")

        serializer = MessageSerializer(
            data={
                "content": request.data.get("content", ""),
                "file": file_obj,
                "reply_to": reply_to_id,
            },
            context={"conversation": conversation, "sender": request.user},
        )
        serializer.is_valid(raise_exception=True)
        message = serializer.save()

        self._broadcast(message)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _broadcast(self, message):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"conversation_{message.conversation_id}",
            {
                "type": "chat_message",
                "id": str(message.id),
                "conversation": str(message.conversation_id),
                "sender": str(message.sender_id),
                "sender_name": str(message.sender),
                "content": message.content,
                "file": message.file.url if message.file else None,
                "reply_to": str(message.reply_to_id) if message.reply_to_id else None,
                "created_at": message.created_at.isoformat(),
            },
        )


class ChatConnectTicketView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ticket = secrets.token_urlsafe(32)
        redis_conn = get_redis_connection("default")
        redis_conn.setex(f"ws_ticket:{ticket}", 100, str(request.user.id))
        return Response({"ticket": ticket})