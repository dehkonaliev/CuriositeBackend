from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from .serializers import (QuizSerializer, UpQuizSerializer,
    QuestionSerializer, GetQuizSerializer,
    GetQuizSerializer, OptionSerializer, QuizAttemptSerializer
)
from rest_framework.exceptions import ValidationError
from rest_framework import generics, status
from baseapp.permissions import IsInstructorAndOwner, IsAdminOrOwnerOrReadOnlyPublished, IsInstructorOrAdmin, IsStudentAndOwner
from baseapp.utils import success_response, error_response
from .models import QuizOption, Question, Quiz, QuizAttempt
from rest_framework.permissions import IsAuthenticated


class CreateQuizAPIView(APIView):
    permission_classes = [IsInstructorAndOwner]
    def post(self, request):
        serializer = QuizSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Quiz created", data=serializer.data, status_code=201)

class UpDelQuizAPIView(APIView):
    permission_classes = [IsInstructorAndOwner]
    def patch(self, request, pk):
        quiz = Quiz.objects.filter(pk=pk).first()
        if not quiz:
            return error_response(message="Quiz not found", status_code=404)
        self.check_object_permissions(request, quiz.lesson.module.course)
        serializer = UpQuizSerializer(instance=quiz, data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Quiz updated", data=serializer.data)
    
    def delete(self, request, pk):
        quiz = Quiz.objects.filter(pk=pk).first()
        if not quiz:
            return error_response(message="Quiz not found", status_code=404)
        self.check_object_permissions(request, quiz.lesson.module.course)
        quiz.delete()
        
        return success_response(message="Quiz deleted")

class CreateQuestionAPIView(APIView):
    permission_classes = [IsInstructorAndOwner]
    def post(self, request):
        serializer = QuestionSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Question created", data=serializer.data, status_code=201)
    
class DeleteQuestionAPIView(APIView):
    permission_classes = [IsInstructorAndOwner]
    def delete(self, request, pk):
        question = Question.objects.filter(pk=pk).first()
        if not question:
            return error_response(message="Question not found", status_code=404)
        self.check_object_permissions(request, question.quiz.lesson.module.course)
        question.delete()
        
        return success_response(message="Question deleted")
    
class CreateOptionAPIView(APIView):
    permission_classes = [IsInstructorAndOwner]
    def post(self, request):
        serializer = OptionSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Option created", data=serializer.data, status_code=201) 
    
class DeleteOptionAPIView(APIView):
    permission_classes = [IsInstructorAndOwner]
    def delete(self, request, pk):
        option = QuizOption.objects.filter(pk=pk).first()
        if not option:
            return error_response(message="Option not found", status_code=404)
        self.check_object_permissions(request, option.question.quiz.lesson.module.course)
        option.delete()
        
        return success_response(message="Option deleted")         

class GetQuizAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrOwnerOrReadOnlyPublished]
    def get(self, request, pk):
        quiz = Quiz.objects.filter(pk=pk).first()
        if not quiz:
            return error_response(message="Quiz not found", status_code=404)
        self.check_object_permissions(request, quiz.lesson.module.course)
        if request.user.user_role == "STUDENT" and not request.user.enrollments.filter(has_access=True, course=quiz.lesson.module.course).exists():
            return error_response(message="You have no permission for this quiz")
        
        serializer = GetQuizSerializer(quiz)
        return success_response(message="Quiz detail", data=serializer.data)

class QuizAttemptAPIView(APIView):
    permission_classes = [IsAuthenticated, IsStudentAndOwner]
    def post(self, request, pk):
        quiz = Quiz.objects.filter(pk=pk).first()
        if not quiz:
            return error_response(message="Quiz not found", status_code=404)
        attempts_count = QuizAttempt.objects.filter(quiz=quiz, student=request.user).count()
        if attempts_count > 2:
            return error_response(message="You can have three trials on every quiz", status_code=403)
        serializer = QuizAttemptSerializer(data=request.data, context={'user': request.user, 'quiz': quiz})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Attempt saved", data={
            **serializer.data,
            'total': quiz.questions.count(),
            'attempts_left': 2 - attempts_count,
        }, status_code=201)