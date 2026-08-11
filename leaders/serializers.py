from rest_framework import serializers
from profiles.models import StudentProfile
from baseapp.utils import field_error
from authentication.serializers import UpdateProfileSerializer


class LeaderSerializer(serializers.ModelSerializer):
    student = UpdateProfileSerializer()
    is_me = serializers.SerializerMethodField()
    rank = serializers.SerializerMethodField()
    class Meta:
        model = StudentProfile
        fields = ['total_courses_enrolled','rank' , 'is_me', 'xp', 'is_visible', 'student']
        
        
    def get_is_me(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated and user.user_role == "STUDENT":
            return obj.student == self.context.get('request').user
        
        return False
    
    def get_rank(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated and user.user_role == "STUDENT":
            return self.context.get('rank')
        return None