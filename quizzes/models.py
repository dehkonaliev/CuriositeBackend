from django.db import models
from baseapp.models import BaseModel
from courses.models import Lesson
from authentication.models import CustomUser


class Quiz(BaseModel):
    title = models.CharField(max_length=1000)
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz')
    
    def __str__(self):
        return self.title
    
class Question(BaseModel):
    class QuestionTypes(models.TextChoices):
        RADIO = 'RADIO', 'radio'
        CHECKBOX = 'CHECKBOX', 'checkbox'
        TEXT = 'TEXT', 'text'
        
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question = models.CharField(max_length=2000)
    question_type = models.CharField(max_length=15, choices=QuestionTypes.choices)
    
class QuizOption(BaseModel):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    option = models.CharField(max_length=2000)
    is_correct = models.BooleanField(default=False)
    
class QuizAttempt(BaseModel):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='quiz_attempts')
    score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    