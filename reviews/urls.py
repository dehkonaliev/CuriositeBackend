from django.urls import path
from .views import ReviewCreateAPIView, ReviewUpDelAPIView, GetCourseReviewsAPIView, GetMyReviewsAPIView, IsReviewedAPIView

urlpatterns = [
    path('review-create', ReviewCreateAPIView.as_view()),
    path('review-update-delete/<uuid:pk>', ReviewUpDelAPIView.as_view()),
    path('course/<uuid:pk>', GetCourseReviewsAPIView.as_view()),
    path('my-reviews', GetMyReviewsAPIView.as_view()),
    path('is-reviewed/<uuid:pk>', IsReviewedAPIView.as_view()),
]