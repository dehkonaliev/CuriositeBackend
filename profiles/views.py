from django.shortcuts import render
from authentication.models import CustomUser
from .models import StudentProfile, InstructorProfile, FriendRequest, FriendShip
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from baseapp.permissions import IsInstructorOrAdmin, IsStudentAndOwner
from baseapp.utils import error_response, success_response
from rest_framework.permissions import IsAuthenticated
from .serializers import (StudentProfileSerializer, InstructorProfileSerializer, GetStudentProfileSerializer, GetInstructorProfileSerializer,
    SendFriendRequestSerializer, FriendSerializer
)


class StudentProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        profile = StudentProfile.objects.filter(student=request.user).first()
        if not profile:
            return error_response(message="Student profile not found", status_code=404)
        
        
        serializer = StudentProfileSerializer(profile)
        
        return success_response(message="Student profile retreived", data=serializer.data)
    
    def patch(self, request):
        profile = StudentProfile.objects.filter(student=request.user).first()
        if not profile:
            return error_response(message="Student profile not found", status_code=404)
        
        serializer = StudentProfileSerializer(instance=profile, data=request.data, partial=True)
        serializer.is_valid()
        serializer.save()
        
        return success_response(message="Student profile updated", data=serializer.data)
    

class InstructorProfileAPIView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorOrAdmin]
    def get(self, request):
        profile = InstructorProfile.objects.filter(instructor=request.user).first()
        if not profile:
            return error_response(message="Instructor profile not found", status_code=404)
        
        serializer = InstructorProfileSerializer(profile)
        
        return success_response(message="Instructor profile retreived", data=serializer.data)
    
    def patch(self, request):
        profile = InstructorProfile.objects.filter(instructor=request.user).first()
        if not profile:
            return error_response(message="Instructor profile not found", status_code=404)
        
        serializer = InstructorProfileSerializer(instance=profile, data=request.data, partial=True)
        serializer.is_valid()
        serializer.save()
        
        return success_response(message="Instructor profile updated", data=serializer.data)
        

class GetStudentProfileAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, pk):
        student = CustomUser.objects.filter(pk=pk).first()
        if not student:
            return error_response(message="Student not found", status_code=404)
        
        profile = getattr(student, 'student_profile', None)
        if profile and not profile.is_visible and student != request.user:
            return error_response(message="This student's profile is private", status_code=404)
        
        serializer = GetStudentProfileSerializer(student)
        
        return success_response(message="Student profile", data=serializer.data)
    
    
class GetInstructorProfileAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, pk):
        instructor = CustomUser.objects.filter(pk=pk).first()
        if not instructor:
            return error_response(message="Instructor not found", status_code=404)
        
        serializer = GetInstructorProfileSerializer(instructor)
        
        return success_response(message="Instructor profile", data=serializer.data)


class SendFriendRequestAPIView(APIView):
    permission_classes = [IsStudentAndOwner]
    
    def post(self, request):
        serializer = SendFriendRequestSerializer(data=request.data, context={'request':request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Request sent", data=serializer.data)
    
    
class AcceptFriendRequestAPIView(APIView):
    permission_classes = [IsStudentAndOwner]
    def patch(self, request, pk):
        user = request.user
        friend_request = FriendRequest.objects.filter(pk=pk, to_student=user, request_status="PENDING").first()
        if not friend_request:
            return error_response(message="Pending request not found", status_code=404)
        
        friend_request.request_status = 'ACCEPTED'
        friend_request.save()
        FriendShip.objects.bulk_create([
            FriendShip(student=user, friend=friend_request.from_student),
            FriendShip(student=friend_request.from_student, friend=user),
        ], ignore_conflicts=True)
        
        return success_response(message="Request accepted")
    

class RejectFriendRequestAPIView(APIView):
    permission_classes = [IsStudentAndOwner]
    def patch(self, request, pk):
        user = request.user
        friend_request = FriendRequest.objects.filter(pk=pk, to_student=user, request_status="PENDING").first()
        if not friend_request:
            return error_response(message="Pending request not found", status_code=404)
        
        friend_request.request_status = 'REJECTED'
        friend_request.save()
        
        return success_response(message="Request rejected")
    
class CancelFriendRequestAPIView(APIView):
    permission_classes = [IsStudentAndOwner]
    def patch(self, request, pk):
        user = request.user
        friend_request = FriendRequest.objects.filter(pk=pk, from_student=user, request_status="PENDING").first()
        if not friend_request:
            return error_response(message="Pending request not found", status_code=404)
        
        friend_request.request_status = 'CANCELLED'
        friend_request.save()
        
        return success_response(message="Request cancelled")
    
    
class GetMyRequestsAPIView(APIView):
    permission_classes = [IsStudentAndOwner]
    def get(self, request):
        requests = FriendRequest.objects.filter(from_student=request.user)
        
        serializer = SendFriendRequestSerializer(requests, many=True)
        
        return success_response(message="Your requests", data=serializer.data)
    
    
class GetIncomingRequestsAPIView(APIView):
    permission_classes = [IsStudentAndOwner]
    def get(self, request):
        requests = FriendRequest.objects.filter(to_student=request.user, request_status__in=('PENDING', 'ACCEPTED', 'REJECTED'))
        
        serializer = SendFriendRequestSerializer(requests, many=True)
        
        return success_response(message="Incoming request", data=serializer.data)
    
    
class FriendsAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, pk):
        friends = CustomUser.objects.filter(pk=pk).first().friendships
        serializer = FriendSerializer(friends, many=True)
        
        return success_response(message="Friend", data=serializer.data)
        
