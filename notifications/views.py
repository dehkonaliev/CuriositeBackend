from django.shortcuts import render
from rest_framework.views import APIView
from .models import Notification
from rest_framework.permissions import IsAuthenticated
from baseapp.utils import success_response, error_response
from baseapp.permissions import IsOwner
from .serializers import NotificationSerializer


class MyNotificationsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        serializer = NotificationSerializer(request.user.notifications.order_by('-created_at'), many=True)
        
        return success_response(message="My notifications", data=serializer.data)
        
    


class ReadNotificationAPIView(APIView):
    permission_classes = [IsOwner]
    def patch(self, request, pk):
        notification = Notification.objects.filter(pk=pk).first()
        if not notification:
            return error_response(message="No notification", status_code=404)
        self.check_object_permissions(request, notification)
        
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        
        return success_response(message="Notification read")
    
    def delete(self, request, pk):
        notification = Notification.objects.filter(pk=pk).first()
        if not notification:
            return error_response(message="No notification", status_code=404)
        self.check_object_permissions(request, notification)
        
        notification.delete()
        
        return success_response(message="Notification deleted")