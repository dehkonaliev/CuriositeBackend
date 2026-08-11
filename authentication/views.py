from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import CustomUser, CodeVerify
from .utils import generate_code, check_code, is_expired_code
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from baseapp.emails import send_verification_code
from baseapp.utils import success_response, error_response, field_error
from django.db.models import Q
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import (EmailOrPhoneSerializer, VerifyCodeSerializer, ActivateUserSerializer,
    LoginSerializer, LogoutSerializer, UpdateProfileSerializer, PasswordChangeSerializer, 
    VerifyEmailSerializer, VerifyPhoneSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    UserSerializer, UserPreferenceSerializer
)




class EmailOrPhoneAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = EmailOrPhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        auth_type = serializer.validated_data.get('auth_type')
        
        code = generate_code(user, auth_type)
        
        if auth_type == 'VIA_EMAIL':
            send_verification_code(user.email, code)
            return success_response(message="We have sent the code to your email, please check!", data={"email": user.email})
        elif auth_type == 'VIA_PHONE':
            return success_response(message="You can get the verification code via telegram on this number!", data={"phone_number": user.phone_number})
            
class VerifyCodeAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data.get('user')
        veirification = serializer.validated_data.get('verification')
        veirification.is_used = True
        veirification.save()
        if veirification.verify_type == "VIA_EMAIL":
            user.email_verified = True
            user.save()
            return success_response(
                message="Email verified", 
                data={"email": user.email, "token": serializer.validated_data['token']}
            )
        elif veirification.verify_type == "VIA_PHONE":
            user.phone_verified = True
            user.save()
            
            return success_response(
                message="Email verified", 
                data={"email": user.email, "token": serializer.validated_data['token']}
            )
            
class ActivateUserAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = ActivateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(
            message="User activated", 
            data=serializer.data
        )
 
class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = serializer.validated_data['tokens']
        
        return success_response(message="Logged in", data=tokens)
        
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid()
        serializer.save()
        
        return success_response(message="Logged out")
        
class UpdateProfileAPIView(APIView):
    parser_classes = [FormParser, MultiPartParser]
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        user = request.user
        serializer = UpdateProfileSerializer(instance=user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Profile updated", data=serializer.data)
    
class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        user = CustomUser.objects.filter(pk=pk).first()
        if not user:
            return error_response(message="User not found")
        
        serializer = UserSerializer(user)
        return success_response(message="Profile info", data=serializer.data)
    
class MyProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        
        serializer = UserSerializer(request.user)
        return success_response(message="My profile info", data=serializer.data)

class PasswordChangeAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = PasswordChangeSerializer(instance=request.user, data=request.data, context={'user':request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Password changed")
        
class DeleteAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user

        # Confirm the deletion with the code we sent earlier.
        if 'verification_code' in request.data:
            code = request.data.get('verification_code')
            if not code or not code.isdigit() or len(code) != 6:
                return field_error("code", "Invalid code!")
            verification = user.codes.filter(code=code, is_used=False).order_by('-expire_time').first()
            if not verification:
                return field_error("code", "Invalid code!")
            elif verification.expire_time < timezone.now():
                return field_error("code", "Verification code expired!")

            verification.is_used = True
            verification.save()
            user.account_status = CustomUser.AccountStatus.DELETED
            user.save()

            return success_response(message="Account set deleted")

        # Send a verification code over the requested verified channel.
        verify_type = request.data.get('verify_type')
        if verify_type == "VIA_EMAIL":
            if not user.email_verified:
                return error_response(message="You cannot delete your account via email. Your email is not verified!")

            is_expired_code(user)
            code = generate_code(user, verify_type)
            send_verification_code(user.email, code)

            return success_response(
                message="We have sent the verification code to your email. Please verify your email!",
                data={"verify_type": "VIA_EMAIL"}
            )
        elif verify_type == "VIA_PHONE":
            if not user.phone_verified:
                return error_response(message="You cannot delete your account via phone. Your phone number is not verified!")

            is_expired_code(user)
            code = generate_code(user, verify_type)

            return success_response(
                message="You can get the verification code in telegram!",
                data={"verify_type": "VIA_PHONE"}
            )
        else:
            return error_response(message="Invalid verify type!")

class VerifyEmailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Confirm the code → mark the email verified.
        if 'code' in request.data:
            code = request.data.get('code')
            if not code or not code.isdigit() or len(code) != 6:
                return field_error("code", "Invalid code!")

            verification = check_code(user, code)
            verification.is_used = True
            verification.save()

            user.email_verified = True
            user.save()

            return success_response(
                message="Email verified!",
                data={"email": user.email}
            )

        # Send a verification code to the (possibly new) email.
        if 'email' not in request.data:
            return field_error("email", "Email is required!")

        serializer = VerifyEmailSerializer(instance=user, data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        new_email = serializer.validated_data.get('email')

        is_expired_code(user)
        code = generate_code(user, "VIA_EMAIL")
        send_verification_code(new_email, code)

        return success_response(
            message="We have sent the verification code to your email, please check it!",
            data={"email": user.email}
        )

class VerifyPhoneAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Confirm the code → mark the phone verified.
        if 'code' in request.data:
            code = request.data.get('code')
            if not code or not code.isdigit() or len(code) != 6:
                return field_error("code", "Invalid code!")

            verification = check_code(user, code)
            verification.is_used = True
            verification.save()

            user.phone_verified = True
            user.save()

            return success_response(
                message="Your phone number verified!",
                data={"phone_number": user.phone_number}
            )

        # Send a verification code for the (possibly new) phone number.
        if 'phone_number' not in request.data:
            return field_error("phone_number", "Phone number is required!")

        serializer = VerifyPhoneSerializer(instance=user, data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        new_phone = serializer.validated_data.get('phone_number')

        is_expired_code(user)
        code = generate_code(user, "VIA_PHONE")

        return success_response(
            message="You can get your code via our telegram bot!",
            data={"phone_number": user.phone_number}
        )

class PasswordResetRequestAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        verify_type = serializer.validated_data['verify_type']
        if verify_type == 'VIA_EMAIL':
            return success_response(
                message="We have sent reset password link to your email!",
                data={"email": serializer.validated_data['email_or_phone']}
            )
        if verify_type == 'VIA_PHONE':
            return success_response(
                message="You can get reset password link via our telegram bot!",
                data={"phone_number": serializer.validated_data['email_or_phone']}
            )

class PasswordResetConfirmAPIView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Password reset!")
            
        
        
class PreferenceUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request):
        serializer = UserPreferenceSerializer(instance=request.user.preference, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="User preference", data=serializer.data)
    
    def get(self, request):
            serializer = UserPreferenceSerializer(request.user.preference)
            
            return success_response(message="User preference", data=serializer.data)
        
            
        
                    