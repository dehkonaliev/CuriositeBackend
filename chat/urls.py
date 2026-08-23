from django.urls import path

from chat.views import (
    ConversationListCreateView,
    ConversationDetailView,
    MessageListView,
    MessageFileUploadView,
    ChatConnectTicketView,
)

urlpatterns = [
    path("", ConversationListCreateView.as_view(), name="conversation-list-create"),
    path("<uuid:conversation_id>/", ConversationDetailView.as_view(), name="conversation-detail"),
    path("<uuid:conversation_id>/messages/", MessageListView.as_view(), name="conversation-messages"),
    path("conversations/<uuid:conversation_id>/messages/upload/", MessageFileUploadView.as_view(), name="conversation-message-upload"),
    path("connect-ticket/", ChatConnectTicketView.as_view(), name="chat-connect-ticket"),
]