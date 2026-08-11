from django.shortcuts import render
from rest_framework.views import APIView
from baseapp.utils import success_response, error_response
from .serializers import ReviewSerializer, MyReviewSerializer
from baseapp.permissions import IsOwner
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Review
from courses.models import Course


class ReviewCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        if user.account_status != "ACTIVE":
            return error_response(message="User is not active")
        
        serializer = ReviewSerializer(data=request.data, context={'user': user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Review Created", data=serializer.data)
    
class ReviewUpDelAPIView(APIView):
    permission_classes = [IsAuthenticated, IsOwner]
    def patch(self, request, pk):
        review = Review.objects.filter(pk=pk).first()
        if not review:
            return error_response(message="Review not found", status_code=404)
        
        self.check_object_permissions(request, review)
        
        serializer = ReviewSerializer(instance=review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Review updated", data=serializer.data)
    
    def delete(self, request, pk):
        review = Review.objects.filter(pk=pk).first()
        if not review:
            return error_response(message="Review not found", status_code=404)
        
        self.check_object_permissions(request, review)
        
        review.delete()
        
        return success_response(message="Review deleted")
    
    
class GetCourseReviewsAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, pk):
        course = Course.objects.filter(pk=pk).first()
        if not course:
            return error_response(message="Course not found", status_code=404)
        reviews = course.reviews.order_by('created_at')
        serializer = ReviewSerializer(reviews, many=True)
        return success_response(message="Reviews on course", data=serializer.data)
    
class GetMyReviewsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        reviews = request.user.my_reviews.order_by('-created_at')
        serializer = MyReviewSerializer(reviews, many=True)
        return success_response(message="Your reviews", data=serializer.data)
    
class IsReviewedAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        if request.user.my_reviews.filter(course__pk=pk).exists():
            return success_response(message="Reviewed!", data={"is_reviewed": True})
        return success_response(message="Not Reviewed!", data={"is_reviewed": False})        
                