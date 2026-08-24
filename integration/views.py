from django.shortcuts import render
from rest_framework.views import APIView
from baseapp.utils import error_response, success_response
from .serializers import GetAudioSerializer
from rest_framework.permissions import IsAuthenticated
from courses.models import Lesson
from .integrate import generate_text_async, generate_audio_async
from asgiref.sync import async_to_sync



class AskInChatAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, lesson_pk):
        lesson = Lesson.objects.filter(pk=lesson_pk, module__course__status="PUBLISHED").first()
        if not lesson:
            return error_response(message="Lesson not found", status_code=404)
    
        interaction_id = request.query_params.get('interaction_id')
        prompt = request.query_params.get('prompt')
        
        if interaction_id:
            output = async_to_sync(generate_text_async)(lesson.title, first_name=request.user.first_name, interaction_id=interaction_id, student_message=prompt)
            return success_response(message="Initialized", data=output)
            
        else:
            output = async_to_sync(generate_text_async)(lesson.title, first_name=request.user.first_name)
            return success_response(message="Response", data=output)
        
        
class GetAudioAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = GetAudioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        text_input = serializer.validated_data.get('text_input')
        
        return async_to_sync(generate_audio_async)(text_input)