from rest_framework import serializers
from .models import Certificate
from authentication.models import CustomUser


class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'username', 'email']

class CertificateSerializer(serializers.ModelSerializer):
    student = UserMinimalSerializer()
    class Meta:
        model = Certificate
        fields = ['id', 'student', 'course_title', 'total_score', 'assignment_score', 'pdf_file', 'created_at']