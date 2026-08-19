from django.db import models
from baseapp.models import BaseModel

class StudentProfile(BaseModel):
    class Genders(models.TextChoices):
        MALE = 'MALE', 'male'
        FEMALE = 'FEMALE', 'female'
    
    student = models.OneToOneField('authentication.CustomUser', on_delete=models.CASCADE, related_name='student_profile')
    gender = models.CharField(max_length=10, choices=Genders.choices, blank=True, null=True)
    friends_count = models.PositiveIntegerField(default=0)
    bio = models.CharField(max_length=1500, blank=True, null=True)
    is_visible = models.BooleanField(default=True)
    xp = models.PositiveIntegerField(default=0)
    streak = models.PositiveIntegerField(default=0)
    last_streak_day = models.DateTimeField(blank=True, null=True)
    level = models.PositiveIntegerField(default=1)
    
    total_courses_enrolled = models.PositiveIntegerField(default=0)
    total_courses_completed = models.PositiveIntegerField(default=0)
    total_certificates_earned = models.PositiveIntegerField(default=0)
   

class InstructorProfile(BaseModel):
    instructor = models.OneToOneField('authentication.CustomUser', on_delete=models.CASCADE, related_name='instructor_profile')
    headline = models.CharField(max_length=200, blank=True, null=True)
    bio = models.CharField(max_length=2000, blank=True, null=True)
    
    linkedin_url = models.URLField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    
    class ApprovalStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        
    total_courses_created = models.PositiveIntegerField(default=0)
    total_students_taught = models.PositiveIntegerField(default=0)
    
    approval_status = models.CharField(max_length=10, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING)
    

class InterestTag(BaseModel):
    student = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, related_name='interests')
    tag = models.ForeignKey('courses.Tag', on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ['student', 'tag']
        
        
class FriendRequest(BaseModel):
    from_student = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, related_name='my_requests', limit_choices_to={'user_role': "STUDENT"})
    to_student = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, related_name='incoming_requests', limit_choices_to={'user_role': "STUDENT"})
    class RequestStatus(models.TextChoices):
        PENDING = "PENDING", 'pending'
        ACCEPTED = "ACCEPTED", 'accepted'
        REJECTED = "REJECTED", 'rejected'
        CANCELLED = "CANCELLED", 'cancelled'
        
    request_status = models.CharField(max_length=15, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    
    class Meta:
        unique_together = ['from_student', 'to_student']
        

class FriendShip(BaseModel):
    student = models.ForeignKey('authentication.CustomUser', related_name='friendships', on_delete=models.CASCADE)
    friend = models.ForeignKey('authentication.CustomUser', related_name='+', on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('friend', 'student')