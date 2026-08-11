from django.db import models
from baseapp.models import BaseModel
from baseapp.utils import generate_wallet_id
from datetime import timedelta
from django.utils import timezone

class StudentWallet(BaseModel):
    student = models.OneToOneField('authentication.CustomUser', on_delete=models.CASCADE, limit_choices_to={'user_role': "STUDENT"}, related_name='wallet')
    wallet_id = models.CharField(unique=True, max_length=8)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def save(self, *args, **kwargs):
        if not self.wallet_id:
            new_id = generate_wallet_id()
            while StudentWallet.objects.filter(wallet_id=new_id).exists():
                new_id = generate_wallet_id()
            self.wallet_id = new_id
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.student.first_name
    
class WalletTransaction(BaseModel):
    class TransactionTypes(models.TextChoices):
        SUBSCRIPTION = 'SUBSCRIPTION', 'subscription'
        PAID_COURSE = 'PAID_COURSE', 'paid_course'
        REPLENISH = 'REPLENISH', 'replenish'
    
    wallet = models.ForeignKey(StudentWallet, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TransactionTypes.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    


class Plan(BaseModel):
    name = models.CharField(max_length=30)
    desc = models.CharField(max_length=500)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    period_days = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
class Subscription(BaseModel):    
    student = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, related_name='subscriptions')
    subscription_plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    expires_at = models.DateTimeField()
    
    def save(self, *args, **kwargs):
        days = self.subscription_plan.period_days
        expiry_date = timezone.now() + timedelta(days=days)
        self.expires_at = expiry_date
        return super().save(*args, **kwargs)
    
    def is_valid(self):
        return self.expires_at > timezone.now()
    
    
    