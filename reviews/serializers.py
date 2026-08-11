from rest_framework import serializers
from .models import Review
from courses.models import Course
from baseapp.utils import field_error



class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'course', 'rating', 'comment']
        read_only_fields = ['id']
        
    def validate_course(self, course):
        return course
    
    def validate_rating(self, rating):
        if not rating:
            return field_error("rating", "Rating cannot be null")
        if rating > 5:
            return field_error("rating", "Rating must be between 1 and 5")
        if rating < 1:
            return field_error("rating", "Rating must be between 1 and 5")
        
        return rating
        
    def validate_comment(self, comment):
        if len(comment) > 2000:
            return field_error("comment", "Comment cannot exceed from 2000 characters long!")
        return comment
    
    def create(self, validated_data):
        user = self.context.get('user')
        course = validated_data.get('course')
        if Review.objects.filter(user=user, course=course).exists():
            return field_error("course", "You can rate a specific course once only")
        review = Review.objects.create(user=user, course=course, comment=validated_data.get('comment'), rating=validated_data.get('rating'))
        return review
    
class CourseMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'title', 'slug', 'thumbnail']

    

        
class MyReviewSerializer(serializers.ModelSerializer):
    course = CourseMinimalSerializer()
    class Meta:
        model = Review
        fields = ['id', 'course', 'rating', 'comment']
        read_only_fields = fields