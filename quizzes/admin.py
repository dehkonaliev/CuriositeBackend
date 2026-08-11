from django.contrib import admin
from .models import Quiz, Question, QuizOption, QuizAttempt

admin.site.register(Quiz)
admin.site.register(QuizOption)
admin.site.register(Question)
admin.site.register(QuizAttempt)