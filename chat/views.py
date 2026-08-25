from rest_framework import permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from baseapp.utils import error_response, success_response
from django.core.exceptions import ValidationError
from django.db.models import F, Max

from chat.models import Conversation, ConversationParticipant, Message
from chat.serializers import ConversationSerializer, MessageSerializer
from courses.models import Course
from posts.models import Post
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
        ).distinct().annotate(
            last_message_at=Max("messages__created_at")
        ).order_by("-last_message_at")

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

    def delete(self, request, conversation_id):
        """DELETE — removes the whole conversation for every participant
        (messages cascade). Everyone still connected gets a
        conversation_deleted event so open panes can react."""
        conversation = self.get_object(request, conversation_id)
        if conversation is None:
            return error_response(message="Conversation not found", status_code=404)

        broadcast_chat_event(
            conversation_id,
            {
                "type": "conversation_deleted",
                "conversation_id": str(conversation_id),
            },
        )
        conversation.delete()
        return success_response(message="Conversation deleted")
    
    
class MessageDetailActionView(APIView):
    """PATCH/DELETE /api/chat/messages/<id>/ — edit or remove a message.
    Only the sender may touch their own message. Both actions broadcast
    chat_message_edit / chat_message_delete to every open socket in the
    conversation (including the actor, whose client dedupes)."""

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, message_id):
        return Message.objects.filter(
            pk=message_id, conversation__participants__user=request.user
        ).first()

    def patch(self, request, message_id):
        message = self.get_object(request, message_id)
        if message is None:
            return error_response(message="Message not found", status_code=404)
        if message.sender_id != request.user.id:
            return error_response(
                message="You can only edit your own messages.", status_code=403
            )

        content = str(request.data.get("content", ""))
        if not content.strip():
            return error_response(message="Message cannot be empty.", status_code=400)

        message.content = content
        message.save(update_fields=["content"])

        broadcast_chat_event(
            message.conversation_id,
            {
                "type": "chat_message_edit",
                "id": str(message.id),
                "conversation": str(message.conversation_id),
                "content": message.content,
            },
        )
        return success_response(message="Message edited")

    def delete(self, request, message_id):
        message = self.get_object(request, message_id)
        if message is None:
            return error_response(message="Message not found", status_code=404)
        if message.sender_id != request.user.id:
            return error_response(
                message="You can only delete your own messages.", status_code=403
            )

        payload = {
            "type": "chat_message_delete",
            "id": str(message.id),
            "conversation": str(message.conversation_id),
        }
        message.delete()
        broadcast_chat_event(message.conversation_id, payload)
        return success_response(message="Message deleted")


class MessageListPagination(PageNumberPagination):
    page_size = 30


def broadcast_chat_event(conversation_id, payload):
    """Generic group broadcast for one conversation. `payload["type"]` selects
    the consumer handler (chat_message, chat_message_edit, ...)."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(f"conversation_{conversation_id}", payload)


def broadcast_chat_message(message):
    """Push a saved Message to every open socket in its conversation.
    Mirrors the WS payload so REST- and socket-created messages render
    identically (including file attachments and forwarded previews)."""
    broadcast_chat_event(
        message.conversation_id,
        {
            "type": "chat_message",
            "id": str(message.id),
            "conversation": str(message.conversation_id),
            "sender": str(message.sender_id),
            "sender_name": str(message.sender),
            "content": message.content,
            "file": message.file.url if message.file else None,
            "reply_to": str(message.reply_to_id) if message.reply_to_id else None,
            "forward": message.forward,
            "created_at": message.created_at.isoformat(),
        },
    )


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

        broadcast_chat_message(message)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


FORWARD_SUMMARY_MAX_CHARS = 300


def _trim_summary(text):
    text = (text or "").strip()
    if len(text) > FORWARD_SUMMARY_MAX_CHARS:
        return f"{text[:FORWARD_SUMMARY_MAX_CHARS]}..."
    return text


class MessageForwardView(APIView):
    """POST {item_type: "post"|"course", item_id: <uuid>, content?: str} —
    shares a published post/course into a conversation as a preview-card
    message. The card data (image, title, summary, detail-page link) lives
    in Message.forward so the client renders it without extra fetches."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conversation_id):
        conversation = Conversation.objects.filter(
            pk=conversation_id, participants__user=request.user
        ).first()
        if conversation is None:
            return error_response(message="Conversation not found", status_code=404)

        item_type = str(request.data.get("item_type", "")).lower().strip()
        if item_type not in ("post", "course"):
            return error_response(
                message="'item_type' must be 'post' or 'course'.", status_code=400
            )

        payload = self._build_forward_payload(item_type, request.data.get("item_id"))
        if payload is None:
            return error_response(
                message=f"This {item_type} does not exist or is not publicly visible.",
                status_code=404,
            )

        serializer = MessageSerializer(
            data={
                "content": request.data.get("content", ""),
                "forward": payload,
            },
            context={"conversation": conversation, "sender": request.user},
        )
        serializer.is_valid(raise_exception=True)
        message = serializer.save()

        if item_type == "course":
            Course.objects.filter(pk=payload["id"]).update(total_shares=F("total_shares") + 1)

        broadcast_chat_message(message)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _build_forward_payload(item_type, item_id):
        try:
            if item_type == "post":
                post = Post.objects.filter(
                    pk=item_id, status=Post.PostStatus.PUBLISHED
                ).first()
                if post is None:
                    return None
                return {
                    "type": "post",
                    "id": str(post.id),
                    "slug": post.slug,
                    "title": post.title,
                    "image": post.cover_image.url if post.cover_image else None,
                    "summary": _trim_summary(post.excerpt),
                    "url": f"/posts/{post.slug}",
                }

            course = Course.objects.filter(
                pk=item_id, status=Course.Status.PUBLISHED
            ).first()
            if course is None:
                return None
            return {
                "type": "course",
                "id": str(course.id),
                "slug": course.slug,
                "title": course.title,
                "image": course.thumbnail.url if course.thumbnail else None,
                "summary": _trim_summary(course.subtitle or course.description),
                "url": f"/courses/{course.slug}",
            }
        except (ValidationError, ValueError, TypeError):
            # malformed item_id (not a UUID)
            return None


class JoinCourseGroupView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        course_id = request.data.get("course_id")
        if not course_id:
            return error_response(message="course_id is required.", status_code=400)

        try:
            course = Course.objects.get(pk=course_id)
        except (Course.DoesNotExist, ValidationError, ValueError, TypeError):
            return error_response(message="Course not found.", status_code=404)

        conversation, created = Conversation.objects.get_or_create(
            course=course,
            is_group=True,
            defaults={"name": course.title},
        )

        participant, added = ConversationParticipant.objects.get_or_create(
            conversation=conversation,
            user=request.user,
        )

        if created:
            message = "Course group created"
        elif added:
            message = "Joined course group"
        else:
            message = "Already in course group"

        serializer = ConversationSerializer(conversation, context={"request": request})
        return success_response(message=message, data=serializer.data)


class ChatConnectTicketView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ticket = secrets.token_urlsafe(32)
        redis_conn = get_redis_connection("default")
        redis_conn.setex(f"ws_ticket:{ticket}", 100, str(request.user.id))
        return Response({"ticket": ticket})