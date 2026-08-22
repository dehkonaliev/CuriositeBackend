from django.db import models
from baseapp.models import BaseModel
from django.utils.text import slugify
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

def resize_image(image_field, max_width=800, max_height=800, quality=85):
    img = Image.open(image_field)
    img.thumbnail((max_width, max_height), Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format='JPEG', quality=quality)
    buffer.seek(0)

    return InMemoryUploadedFile(
        buffer, 'ImageField', image_field.name,
        'image/jpeg', sys.getsizeof(buffer), None
    )

class Category(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.CharField(unique=True, blank=True)
    icon = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
        
        
class Tag(BaseModel):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    

class Course(BaseModel):
    instructor = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, related_name='courses', limit_choices_to={'user_role': 'INSTRUCTOR'})
    
    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300)
    subtitle = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField()
    
    #CATEGORIZING
    category = models.ForeignKey('courses.Category', on_delete=models.SET_NULL, null=True, related_name='courses')
    tags = models.ManyToManyField('courses.Tag', blank=True, related_name='courses')
    
    #LEVELS
    class Level(models.TextChoices):
        BEGINNER = 'BEGINNER', 'Beginner'
        INTERMEDIATE = 'INTERMEDIATE', 'Intermediate'
        ADVANCED = 'ADVANCED', 'Advanced'
        ALL_LEVELS = 'ALL_LEVELS', 'All Levels'
        
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.ALL_LEVELS)
    language = models.CharField(max_length=10, default='en')
    
    #MEDIA
    thumbnail = models.ImageField(upload_to='courses/thumbnails/', blank=True, null=True)
    intro_video = models.URLField(blank=True, null=True)
    
    #PRICING
    class PricingType(models.TextChoices):
        FREE = 'FREE', 'free'
        MONTHLY = 'MONTHLY', 'monthly'
        SPECIAL = 'SPECIAL', 'special'
    pricing_type = models.CharField(max_length=10, choices=PricingType.choices, default=PricingType.MONTHLY)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, blank=True, null=True)
    
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        IN_REVIEW = 'IN_REVIEW', 'In Review'
        REJECTED = 'REJECTED', 'Rejected'
        PUBLISHED = 'PUBLISHED', 'Published'
        ARCHIVED = 'ARCHIVED', 'Archived'
        
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(blank=True, null=True)
    
    total_enrollments = models.PositiveIntegerField(default=0)
    total_shares = models.PositiveIntegerField(default=0)
    total_reading_time = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    rating_count = models.PositiveIntegerField(default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    
    requirements = models.CharField(max_length=1000, blank=True, null=True)
    what_included = models.CharField(max_length=1500, blank=True, null=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_thumbnail = self.thumbnail.name if self.thumbnail else None
    
    def save(self, *args, **kwargs):
        if self.thumbnail and self.thumbnail.name != self._original_thumbnail:
            self.thumbnail = resize_image(self.thumbnail)
            
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
            
    def __str__(self):
        return self.title
    

class Module(BaseModel):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)  # for drag-and-drop reordering

    class Meta:
        ordering = ['order']
        
        
class Lesson(BaseModel):
    class LessonType(models.TextChoices):
        VIDEO = 'VIDEO', 'Video'
        ARTICLE = 'ARTICLE', 'Article'
        QUIZ = 'QUIZ', 'Quiz'
        ASSIGNMENT = 'ASSIGNMENT', 'Assignment'

    module = models.ForeignKey('courses.Module', on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    lesson_type = models.CharField(max_length=20, choices=LessonType.choices, default=LessonType.VIDEO)
    video_url = models.URLField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)  # for articles
    duration_minutes = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=0)
    is_preview = models.BooleanField(default=False)  # free preview lesson, visible before enrollment

    class Meta:
        ordering = ['order']
        
    def __str__(self):
        return f"{self.module.title} {self.title}"

    
