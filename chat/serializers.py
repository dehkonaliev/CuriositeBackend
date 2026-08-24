import uuid

from django.db.models import Count
from rest_framework import serializers
from baseapp.utils import field_error
from authentication.models import CustomUser
from posts.serializers import AuthorMiniSerializer


from chat.models import Conversation, ConversationParticipant, Message, UnreadMessage


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "sender_name",
            "content",
            "file",
            "reply_to",
            "forward",
            "created_at",
        ]
        read_only_fields = ["id", "sender", "sender_name", "conversation", "created_at"]

    def get_sender_name(self, obj):
        return str(obj.sender) if obj.sender else None

    def validate_reply_to(self, value):
        if value is None:
            return value

        conversation = self.context.get("conversation")
        if conversation and value.conversation_id != conversation.id:
            return field_error("reply_to", "reply_to message must belong to the same conversation.")
        return value

    def validate(self, attrs):
        content = attrs.get("content", "")
        file = attrs.get("file")
        forward = attrs.get("forward")

        if not content.strip() and not file and not forward:
            return field_error("non_field_error", "Message must have either content or a file attached.")
        return attrs

    def create(self, validated_data):
        validated_data["conversation"] = self.context["conversation"]
        validated_data["sender"] = self.context["sender"]
        message = Message.objects.create(**validated_data)

        recipient_ids = ConversationParticipant.objects.filter(
            conversation=message.conversation
        ).exclude(user=message.sender).values_list("user_id", flat=True)

        UnreadMessage.objects.bulk_create(
            [
                UnreadMessage(message=message, conversation=message.conversation, user_id=uid)
                for uid in recipient_ids
            ],
            ignore_conflicts=True,
        )

        return message
    

class ConversationParticipantSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    user = AuthorMiniSerializer()

    class Meta:
        model = ConversationParticipant
        fields = ["id", "user", "username"]

    def get_username(self, obj):
        return str(obj.user) if obj.user else None


class ConversationSerializer(serializers.ModelSerializer):
    participants = ConversationParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "is_group", "name", "participants", "last_message", "unread_count", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_last_message(self, obj):
        last = obj.messages.order_by("-created_at").first()
        if last is None:
            return None
        return {
            "content": last.content,
            "sender": str(last.sender) if last.sender else None,
            "created_at": last.created_at.isoformat(),
        }

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if request is None or not request.user.is_authenticated:
            return 0
        return UnreadMessage.objects.filter(conversation=obj, user=request.user).count()

    def validate(self, attrs):
        raw_ids = self.context.get("participant_ids") or []
        requested = []
        for raw_id in raw_ids:
            try:
                requested.append(uuid.UUID(str(raw_id)))
            except (ValueError, TypeError, AttributeError):
                return field_error("participant_ids", f"'{raw_id}' is not a valid user id.")
        if not requested:
            return field_error("participant_ids", "At least one participant is required.")
        found = CustomUser.objects.filter(id__in=requested)
        if found.count() != len(set(requested)):
            return field_error("participant_ids", "One or more participants do not exist.")
        self.context["participants"] = list(found)
        return attrs

    def _find_existing_direct_conversation(self, participants):
        first, second = participants[0], participants[1]
        return (
            Conversation.objects
            .annotate(participant_count=Count("participants"))
            .filter(is_group=False)
            .filter(participants__user=first)
            .filter(participants__user=second)
            .filter(participant_count=2)
            .first()
        )

    def create(self, validated_data):
        participants = list(self.context.get("participants") or [])
        request = self.context.get("request")
        if (
            request is not None
            and request.user.is_authenticated
            and all(p.pk != request.user.pk for p in participants)
        ):
            participants.append(request.user)

        is_group = validated_data.get("is_group", False)
        if not is_group and len(participants) == 2:
            existing = self._find_existing_direct_conversation(participants)
            if existing is not None:
                existing._reused = True
                return existing

        conversation = Conversation.objects.create(**validated_data)
        ConversationParticipant.objects.bulk_create(
            [
                ConversationParticipant(conversation=conversation, user=p)
                for p in participants
            ],
            ignore_conflicts=True,
        )
        return conversation
