from rest_framework import serializers
from .models import Notification
from posts.serializers import AuthorMiniSerializer


class NotificationSerializer(serializers.ModelSerializer):
    sender = AuthorMiniSerializer()
    class Meta:
        model = Notification
        fields = ['id', 'message', 'sender', 'notif_type', 'is_read']