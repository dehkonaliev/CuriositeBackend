from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Course
from profiles.models import InstructorProfile
from django.db.models import F


@receiver([post_save], sender=Course)
def update_total_courses(sender, instance, created, **kwargs):
    if not created:
        return
    
    InstructorProfile.objects.filter(instructor=instance.instructor).update(total_courses_created=F('total_courses_created')+1)
    