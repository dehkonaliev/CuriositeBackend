from django.db.models.signals import post_save
from django.db.models import F
from .models import StudentProfile, InstructorProfile
from courses.models import Course, Lesson
from enrollments.models import Enrollment, LessonProgress
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

@receiver([post_save], sender=Enrollment)
def update_student_enrolled(sender, instance, created, **kwargs):
    if not created:
        return
    lesson = Lesson.objects.filter(module__course=instance.course).order_by('order').first()
    LessonProgress.objects.create(lesson=lesson, enrollment=instance)
    StudentProfile.objects.filter(student=instance.student).update(total_courses_enrolled=F('total_courses_enrolled') + 1)
    Course.objects.filter(pk=instance.course.pk).update(total_enrollments=F('total_enrollments')+1)
    InstructorProfile.objects.filter(instructor=instance.course.instructor).update(total_students_taught=F('total_students_taught') + 1)
    

@receiver(post_save, sender=LessonProgress)
def update_streak(sender, instance, created, **kwargs):
    if not created:
        return

    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    updated = StudentProfile.objects.filter(
        student=instance.enrollment.student
    ).exclude(
        last_streak_day=today  # already counted today, skip
    ).filter(
        last_streak_day=yesterday
    ).update(
        streak=F('streak') + 1,
        last_streak_day=today
    )

    if not updated:
        # either no row existed, last_streak_day was today already,
        # or the streak was broken (gap > 1 day) -> reset to 1
        StudentProfile.objects.filter(
            student=instance.enrollment.student
        ).exclude(
            last_streak_day=today
        ).update(
            streak=1,
            last_streak_day=today
        )