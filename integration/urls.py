from django.urls import path
from .views import AskInChatAPIView, GetAudioAPIView

urlpatterns = [
    path('ask-ai/<uuid:lesson_pk>', AskInChatAPIView.as_view()),
    path('get-audio', GetAudioAPIView.as_view()),
]