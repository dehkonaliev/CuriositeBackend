from django.urls import path
from .views import ReadNotificationAPIView, MyNotificationsAPIView


urlpatterns = [
    path('read-delete-notification/<uuid:pk>', ReadNotificationAPIView.as_view()),
    path('my-notifications', MyNotificationsAPIView.as_view()),
]