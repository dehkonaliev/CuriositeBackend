import random
from .models import CodeVerify, CustomUser
import re
from rest_framework import serializers
from django.utils import timezone
from baseapp.models import MyToken
import uuid
from baseapp.utils import field_error

def generate_code(user, verify_type):
    code = str(random.randint(100000, 999999))
    if verify_type=='VIA_EMAIL':
        CodeVerify.objects.create(user=user, code=code, verify_type=verify_type)
    elif verify_type=='VIA_PHONE':
        CodeVerify.objects.create(user=user, code=code, verify_type=verify_type)
        
    return code

def check_email_username_phone(user_input):
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    phone_pattern = r"^\d{9}$"
    username_pattern = r"^(?=.{3,16}$)[a-zA-Z][a-zA-Z0-9]*(?:_[a-zA-Z0-9]+)*$"
    
    if re.fullmatch(email_pattern, user_input):
        return 'VIA_EMAIL'
    elif re.fullmatch(phone_pattern, user_input):
        return 'VIA_PHONE'
    elif re.fullmatch(username_pattern, user_input):
        return 'VIA_USERNAME'
    
    return False

def check_code(user, code):
    verification = user.codes.filter(code=code, is_used=False).order_by('-expire_time').first()
    if not verification:
        return field_error("verification_code", "Invalid code")
    elif verification.expire_time < timezone.now():
        return field_error("verification_code", "Code expired")
    
    return verification

def is_expired_code(user):
    last_code = user.codes.filter(is_used=False).order_by('-expire_time').first()
    if last_code:
        if last_code.expire_time > timezone.now():
            raise serializers.ValidationError({"code":"Please wait until your current code expires before requesting a new one."})
    
    return last_code
        
def generate_mytoken(user, token_for):
    latest_token = user.my_tokens.order_by('-created_at').first()

    if latest_token and latest_token.is_valid():
        raise serializers.ValidationError({"non_field_error":"Please wait until your old access link expires!"})

    token = MyToken.objects.create(user=user, token_for=token_for)
    return token


def base_updater(user, auth_type):
    is_expired_code(user)
    if auth_type == "VIA_EMAIL":
        if user.account_status == CustomUser.AccountStatus.PENDING:
            user.delete()
        elif user.email_verified == False:
            user.email = f"tempemail_{uuid.uuid4().hex[:12]}@gmail.com"
            user.save()
        elif user.account_status != CustomUser.AccountStatus.PENDING:
            raise serializers.ValidationError({"email": f"User with this email already exists!"})
    if auth_type == "VIA_PHONE":
        if user.account_status == CustomUser.AccountStatus.PENDING:
            user.delete()
        elif user.phone_verified == False:
            user.phone_number = ""
            user.save()
        elif user.account_status != CustomUser.AccountStatus.PENDING:
            raise serializers.ValidationError({"phone_number":f"User with this phone number already exists!"})