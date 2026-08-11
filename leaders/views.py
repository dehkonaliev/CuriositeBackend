from django.shortcuts import render
from profiles.models import StudentProfile
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from baseapp.permissions import IsStudentAndOwner
from .serializers import LeaderSerializer
from baseapp.utils import success_response, error_response


class LeadersAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        leaders = StudentProfile.objects.order_by('-xp')[:20]
        serializer = LeaderSerializer(leaders, many=True, context={'request': request})
        
        return success_response(message="Leaders", data=serializer.data)
    
class MyPlaceAPIView(APIView):
    permission_classes = [IsStudentAndOwner]
    def get(self, request):
        me = StudentProfile.objects.filter(student=request.user).first()
        if not me:
            return error_response(message="Student profile not found")
        rank = StudentProfile.objects.filter(xp__gt=me.xp).count() + 1
        serializer = LeaderSerializer(me, context={'request': request, 'rank': rank})
        
        return success_response(message="Your place", data=serializer.data)