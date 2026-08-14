from django.db import models
import uuid
import secrets
from django.utils import timezone
from datetime import timedelta

class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class MyToken(BaseModel):
    class TokenFor(models.TextChoices):
        ACTIVATION = 'ACTIVATION', 'activation'
        RESET_PASSWORD = 'RESET_PASSWORD', 'reset_password'
    
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, related_name='my_tokens')
    token = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe(32))
    is_used = models.BooleanField(default=False)
    token_for = models.CharField(max_length=20, choices=TokenFor.choices)
    expire_time = models.DateTimeField(null=True, blank=True)
    
    
    def save(self, *args, **kwargs):
        self.expire_time = timezone.now() + timedelta(minutes=100)
        return super().save()
    