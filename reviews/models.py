from django.db import models
from baseapp.models import BaseModel

class Review(BaseModel):
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, related_name='my_reviews')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField()
    comment = models.CharField(max_length=2000, blank=True, null=True)
    
    class Meta:
        unique_together = ['user', 'course']
    