from django.urls import path
from .views import (CreateQuizAPIView, CreateQuestionAPIView, CreateOptionAPIView, UpDelQuizAPIView, DeleteQuestionAPIView,
    DeleteOptionAPIView, GetQuizAPIView, QuizAttemptAPIView
)


urlpatterns = [
    #QUIZZES
    path('create-quiz', CreateQuizAPIView.as_view()),
    path('update-delete-quiz/<uuid:pk>', UpDelQuizAPIView.as_view()),
    path('get-quiz/<uuid:pk>', GetQuizAPIView.as_view()),
    
    #QUESTION
    path('create-question', CreateQuestionAPIView.as_view()),
    path('delete-question/<uuid:pk>', DeleteQuestionAPIView.as_view()),
    
    #OPTIONS
    path('create-option', CreateOptionAPIView.as_view()),
    path('delete-option/<uuid:pk>', DeleteOptionAPIView.as_view()),
    
    #QUIZ ATTEMPY
    path('quiz-attempt/<uuid:pk>', QuizAttemptAPIView.as_view())
    
]