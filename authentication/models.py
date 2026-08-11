from django.db import models
from django.contrib.auth.models import AbstractUser
from baseapp.models import BaseModel
import uuid
from datetime import timedelta
from django.utils import timezone
from core import settings
from django.core.validators import FileExtensionValidator


class CustomUser(AbstractUser, BaseModel):
    class UserRole(models.TextChoices):
        STUDENT = 'STUDENT', 'student'
        INSTRUCTOR = 'INSTRUCTOR', 'instructor'
        SUPERUSER = 'SUPERUSER', 'superuser'
        
    class AuthType(models.TextChoices):
        EMAIL = 'EMAIL', 'email'
        PHONE = 'PHONE', 'phone'
        GOOGLE = 'GOOGLE', 'google'
        
    class AccountStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACTIVE = 'ACTIVE', 'Active'
        SUSPENDED = 'SUSPENDED', 'Suspended'
        BLOCKED = 'BLOCKED', 'Blocked'
        DELETED = 'DELETED', 'Deleted'
        
    
    
    account_status = models.CharField(max_length=20, choices=AccountStatus.choices, default=AccountStatus.PENDING)
    user_role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.STUDENT)
    auth_type = models.CharField(max_length=20, choices=AuthType.choices, default=AuthType.EMAIL)
    
    #email
    email = models.EmailField(unique=True, null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    
    
    #phone
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone_verified = models.BooleanField(default=False)
    
    photo = models.ImageField(upload_to='users/', blank=True, null=True, validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])
    ])
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    
    @property
    def is_verified(self):
        return self.email_verified or self.phone_verified
    
    def save(self, *args, **kwargs):            
        if not self.pk and not self.password:
            self.set_unusable_password()
            
        if not self.username:
            self.username = f"user_{uuid.uuid4().hex[:12]}"
        super().save(*args, **kwargs)
        
        
class CodeVerify(BaseModel):
    class VerifyType(models.TextChoices):
        VIA_EMAIL = 'VIA_EMAIL', 'via_email'
        VIA_PHONE = 'VIA_PHONE', 'via_phone'
    
    code = models.CharField(max_length=6)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='codes')
    expire_time = models.DateTimeField(blank=True, null=True)
    verify_type = models.CharField(max_length=10, choices=VerifyType.choices)
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} code: {self.code}"
    
    class Meta:
        ordering = ['expire_time']
    
    def save(self, *args, **kwargs):
        if not self.expire_time:
            expire_min = (
                settings.EMAIL_EXPIRATION_TIME
                if self.verify_type == self.VerifyType.VIA_EMAIL
                else settings.PHONE_EXPIRATION_TIME
            )
            self.expire_time = timezone.now() + timedelta(minutes=expire_min)
        return super().save(*args, **kwargs)
        

class UserPreference(BaseModel):
    class ThemeMode(models.TextChoices):
        LIGHT = 'LIGHT', 'light'
        DARK = 'DARK', 'dark'
        SYSTEM = 'SYSTEM', 'system'
        
    theme = models.CharField(max_length=10, choices=ThemeMode.choices, default=ThemeMode.SYSTEM)
        
    user = models.OneToOneField('authentication.CustomUser', on_delete=models.CASCADE, related_name='preference')
    language = models.CharField(max_length=20, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    
    def __str__(self):
        return self.user.username or self.user.email
    
