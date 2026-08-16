from django.db import models
from baseapp.models import BaseModel
from authentication.models import CustomUser
from django.utils.text import slugify
import math
import re
from django.utils import timezone



class Post(BaseModel):
    class PostStatus(models.TextChoices):
        DRAFT = "DRAFT", 'draft'
        PUBLISHED = "PUBLISHED", 'published'
        ARCHIVED = "ARCHIVED", 'archived'
    instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_role': "INSTRUCTOR"}, related_name='posts')
    title = models.CharField(max_length=1000)
    body = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='posts/covers/', blank=True, null=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    excerpt = models.CharField(max_length=300, blank=True)
    published_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    views_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=PostStatus.choices)
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        
    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:250]
            slug = base
            n=1
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
            
        if not self.excerpt and self.body:
            text = re.sub(r"<[^>]+>", " ", self.body)
            text = re.sub(r"\s+", " ", text).strip()
            self.excerpt = (text[:277] + "...") if len(text) > 280 else text
            
        if self.status == self.PostStatus.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        return super().save()
    
    @property
    def reading_time_minutes(self):
        words = len(re.sub(r"<[^>]+>", " ", self.body or "").split())
        return max(1, math.ceil(words / 200))
    
    def __str__(self):
        return self.title
    

class PostImage(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='posts/body')
    
    
class PostLike(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='my_likes')
    
    class Meta:
        unique_together = ['post', 'user']
        
class PostComment(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='my_comments')
    comment = models.CharField(max_length=2000)
    

    
    