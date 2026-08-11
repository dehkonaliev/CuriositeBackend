from django.db import models
from baseapp.models import BaseModel


class Notification(BaseModel):
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, related_name='notifications')
    class NotifTypes(models.TextChoices):
        NOTIFICATION = "NOTIFICATION", 'notification'
        REQUEST = "REQUEST", 'request'
        SUBSCRIPTION = "SUBSCRIPTION", "subscription"
        WARNING = "WARNING", "warning"
        REPLENISH = "REPLENISH", "replenish"
        PAYMENT = "PAYMENT", 'payment'
        PROGRESS = "PROGRESS", 'progress'
    message = models.CharField(max_length=2000)
    sender = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, blank=True, null=True)
    notif_type = models.CharField(max_length=20, choices=NotifTypes.choices, default=NotifTypes.NOTIFICATION)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return self.message
    