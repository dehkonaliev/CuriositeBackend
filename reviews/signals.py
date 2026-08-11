from django.db.models import Avg, Count
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import Review

@receiver([post_save, post_delete], sender=Review)
def update_course_rating(sender, instance, **kwargs):
    course = instance.course
    agg = course.reviews.aggregate(avg=Avg('rating'), count=Count('id'))
    course.average_rating = agg['avg'] or 0
    course.rating_count = agg['count']
    course.save(update_fields=['average_rating', 'rating_count'])