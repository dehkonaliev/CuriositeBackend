from rest_framework.response import Response
from rest_framework import serializers
import secrets
import string
import re
from profiles.models import InterestTag


def generate_wallet_id(length=8):
    alphabet = string.ascii_uppercase + string.digits  # A-Z, 0-9
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def validate_wallet_id(wallet_id):
    WALLET_ID = re.compile(r'^[A-Z0-9]{8}')
    
    value = wallet_id.strip()
    if not value:
        return field_error("wallet_id", f"Wallet cannot be blank.")
    if len(value) != 8:
        return field_error("wallet_id", f"Wallet must be at 8 characters.")
    if not WALLET_ID.match(value):
        return field_error("wallet_id", f"Wallet may only contain capital letters and numbers.")

def success_response(message='', data=None, status_code=200):
    return Response({
        "success": True,
        "message": message,
        "data": data
    }, status=status_code)
    
    
def error_response(message="", errors=None, status_code=400):
    return Response({
        "success": False,
        "message": message,
        "errors": errors
    }, status=status_code)
    
def field_error(field, message):
    raise serializers.ValidationError({
        field: message
    })
    
XP_QUANTITY = 5

def interest_recorder(user, tags):
    tags = tags.all() if hasattr(tags, 'all') else tags

    InterestTag.objects.bulk_create(
        [InterestTag(student=user, tag=tag) for tag in tags],
        ignore_conflicts=True
    )
