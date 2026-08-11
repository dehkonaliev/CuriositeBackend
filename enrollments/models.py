from django.db import models
from baseapp.models import BaseModel
from django.utils import timezone


class Enrollment(BaseModel):
    student = models.ForeignKey(
        'authentication.CustomUser',
        on_delete=models.CASCADE,
        related_name='enrollments',
        limit_choices_to={'user_role': 'STUDENT'}
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='enrollments' 
    )
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'active'
        COMPLETED = 'COMPLETED', 'completed'
        DROPPED = 'DROPPED', 'dropped'
        DEACTIVATED = 'DEACTIVATED', 'deactivated'
        
    has_access = models.BooleanField(default=True)
        
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ACTIVE)
    is_bought = models.BooleanField(default=False)
    
    progress_percentage = models.DecimalField(max_length=5, max_digits=5, decimal_places=2, default=0.00)
    last_accessed_lesson = models.ForeignKey(
        'courses.Lesson', on_delete=models.SET_NULL, blank=True, null=True, related_name='+'
    )
    last_accessed_at = models.DateTimeField(blank=True, null=True)
    
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ['student', 'course']
        ordering = ['enrolled_at']
        
    def __str__(self):
        return f"{self.student.email} -> {self.course.title}"
        

class LessonProgress(BaseModel):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name='lessons_progress')
    lesson = models.ForeignKey('courses.Lesson', on_delete=models.CASCADE, related_name='progress_records')
    
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ['enrollment', 'lesson']
        
    def save(self, *args, **kwargs):
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)
        
    
    
    
