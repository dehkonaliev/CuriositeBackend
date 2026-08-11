from django.urls import path
from .views import (EnrollmentCreateAPIView, EnrollmentDropAPIView, CompleteLessonAPIView, LastLessonAPIView,
    MyEnrollmentsAPIView
)

urlpatterns = [
    # ENROLLMENT
    path('enrollment-create', EnrollmentCreateAPIView.as_view()),
    path('enrollment-drop/<uuid:pk>', EnrollmentDropAPIView.as_view()),
    path('my-enrollments', MyEnrollmentsAPIView.as_view()),
    
    # LESSON
    path('lesson-progress/<uuid:pk>', CompleteLessonAPIView.as_view()),
    path('last-lesson', LastLessonAPIView.as_view()),
    
]