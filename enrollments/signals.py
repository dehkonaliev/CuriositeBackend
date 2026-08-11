from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LessonProgress, Enrollment
from courses.models import Course, Lesson
from django.db.models import F, Count
from decimal import Decimal


@receiver([post_save], sender=LessonProgress)
def update_progress_precentage(sender, instance, created, **kwargs):
    course_lessons_count = Lesson.objects.filter(module__course=instance.enrollment.course).count()
    if course_lessons_count == 0:
        course_lessons_count = Decimal('0')
    percentage = Decimal(len(LessonProgress.objects.filter(enrollment=instance.enrollment))) / Decimal(course_lessons_count) * 100
    Enrollment.objects.filter(pk=instance.enrollment.pk).update(progress_percentage=percentage)