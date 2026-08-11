from rest_framework import serializers
from baseapp.utils import field_error, validate_wallet_id
from baseapp.emails import send_notification
from .models import Subscription, WalletTransaction, StudentWallet, Plan
from enrollments.models import Enrollment
from decimal import Decimal
from django.db.models import F
from notifications.models import Notification


class ReplenishWalletSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    wallet_id = serializers.CharField()
        
    def validate_wallet_id(self, wallet_id):
        validate_wallet_id(wallet_id)
        wallet = StudentWallet.objects.filter(wallet_id=wallet_id).first()
        if not wallet:
            return field_error("wallet_id", "Wallet not found")
                
        return wallet_id
    
    def validate_amount(self, amount):
        if amount <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return amount
    
    def save(self, **kwargs):
        wallet_id = self.validated_data['wallet_id']
        amount = self.validated_data['amount']
        wallet = StudentWallet.objects.filter(wallet_id=wallet_id).first()
        wallet.balance = wallet.balance + amount
        wallet.save()
        WalletTransaction.objects.create(wallet=wallet, amount=amount, transaction_type="REPLENISH")
        Notification.objects.create(user=wallet.student, message=f"Your balanance replenished, ${amount}", notif_type="REPLENISH")
        send_notification(wallet.student.email, message=f"Your balance replenished", data={"total": wallet.balance, 'received': amount})
        return wallet

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'desc', 'period_days', 'price']  
        read_only_fields = fields

class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'subscription_plan', 'created_at', 'expires_at']
        read_only_fields = ['id', 'created_at', 'expires_at']
        
    def validate_subscription_plan(self, plan):
        if not plan:
            return field_error('subscription_plan', "Subscription plan must be given")
        if not plan.is_active:
            return field_error("subscription_plan", "invalid plan")
        if plan not in Plan.objects.all():
            return field_error("subscription_plan", "Subscription plan not found")
        
        student = self.context.get('request').user
        if student.wallet.balance < plan.price:
            return field_error("non_field_error", "Not enough balance")
        
        return plan
    
        
    def save(self, **kwargs):
        user = self.context.get('request').user
        plan = self.validated_data.get('subscription_plan')
        subscription = Subscription.objects.create(student=user, subscription_plan=plan)
        wallet = user.wallet
        price = subscription.subscription_plan.price
        wallet.balance = wallet.balance - price
        wallet.save()
        WalletTransaction.objects.create(wallet=wallet, amount=price, transaction_type="SUBSCRIPTION")
        Notification.objects.create(user=wallet.student, message=f"Subscription successful, Plan: {subscription.subscription_plan}", notif_type="SUBSCRIPTION")
        return subscription
        
        
class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'transaction_type', 'amount', 'created_at']
        read_only_fields = fields


class WalletSerializer(serializers.ModelSerializer):
    transactions = serializers.SerializerMethodField()
    class Meta:
        model = StudentWallet
        fields = ['id', 'wallet_id', 'balance', 'transactions']
        read_only_fields = fields

    def get_transactions(self, obj):
        transactions = obj.wallettransaction_set.order_by('-created_at')
        return WalletTransactionSerializer(transactions, many=True).data


class MySubscriptionSerializer(serializers.ModelSerializer):
    plan = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'created_at', 'expires_at', 'is_active']
        read_only_fields = fields

    def get_plan(self, obj):
        return {
            'id': str(obj.subscription_plan.pk),
            'name': obj.subscription_plan.name,
            'desc': obj.subscription_plan.desc,
            'price': obj.subscription_plan.price,
            'period_days': obj.subscription_plan.period_days,
        }

    def get_is_active(self, obj):
        return obj.is_valid()


class BuyCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['id', 'course']
        read_only_fields = ['id']
        
    def validate_course(self, course):
        if not course:
            return field_error("course", "Course must be set")
        if course.status != "PUBLISHED":
            return field_error("course", "Course status is not published")
        if course.pricing_type == 'FREE':
            return field_error("course", "Course status is free")
        student = self.context.get('request').user
        if student.wallet.balance < course.price:
            return field_error("course", "You have insufficient funds to buy this course")
        
        return course
    
    def save(self, **kwargs):
        course = self.validated_data.get('course')
        student = self.context.get('request').user
        existing_enrollment = student.enrollments.filter(course=course).first()
        if existing_enrollment and existing_enrollment.is_bought == True:
            return field_error("course", "Course is already bought")
        if existing_enrollment:
            enrollment.is_bought=True
            enrollment.save()
        wallet = student.wallet
        wallet.balance = wallet.balance - course.price
        wallet.save()
        WalletTransaction.objects.create(wallet=wallet, amount=course.price, transaction_type=WalletTransaction.TransactionTypes.PAID_COURSE)
        Notification.objects.create(user=student, message=f"You bought the course successfully, Course: {course.title}", notif_type="PAYMENT")
        enrollment = Enrollment.objects.create(student=student, course=course, is_bought=True)
        return enrollment
        
        
    
    
        
        