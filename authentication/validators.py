from rest_framework import serializers
import re
from .models import CustomUser
from baseapp.utils import field_error


def name_validator(name, type):
    NAME_REGEX = re.compile(r'^[A-Za-z\u00C0-\u017F\s\'-]+$')
    
    value = name.strip()
    if not value:
        return field_error(type, f"{type} cannot be blank.")
    if len(value) < 2:
        return field_error(type, f"{type} must be at least 2 characters.")
    if len(value) > 50:
        return field_error(type, f"{type} is too long.")
    if not NAME_REGEX.match(value):
        return field_error(type, f"{type} may only contain letters, spaces, hyphens, and apostrophes.")
    return value.title()

def username_validator(username):
    value = username.strip()
    if not value:
        return field_error("username", "Username cannot be blank.")
    if len(value) < 3:
        return field_error("username", "Username must be at least 3 characters.")
    if len(value) > 50:
        return field_error("username", "Username is too long.")
    if not re.fullmatch(r'^[A-Za-z0-9_]+$', value):
        return field_error("username", "Username may only contain letters, numbers, and underscores.")
    if value[0].isdigit():
        return field_error("username", "Username cannot start with a number.")
    if CustomUser.objects.filter(username=value).exists():
        return field_error("username", "A user with this username already exists!")
    return value


def password_validator(password):
    if not re.search(r'[A-Z]', password):
        return field_error("password", f"Password must contain at least one uppercase letter.")
    if not re.search(r'[a-z]', password):
        return field_error("password", "Password must contain at least one lowercase letter.")
    if not re.search(r'[0-9]', password):
        return field_error("password", "Password must contain at least one digit.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\/;\'~`]', password):
        return field_error("password", "Password must contain at least one special character.")
    return True