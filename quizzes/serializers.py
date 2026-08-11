from rest_framework import serializers
from .models import Quiz, QuizOption, Question, QuizAttempt
from profiles.models import StudentProfile
from baseapp.utils import field_error, XP_QUANTITY
from decimal import Decimal
import uuid
      
class QuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'lesson']
        read_only_fields = ['id']
        
    def validate_title(self, title):
        if not title:
            return field_error("title", 'Title is required')
        title = title.strip()
        if len(title) > 1000:
            return field_error("title", "Title cannot exceed 1000 characters long")
        
        return title
    
    def validate_lesson(self, lesson):
        if not lesson:
            return field_error("lesson", "Lesson must be set")
        user = self.context.get('request').user
        if lesson.module.course.instructor != user:
            return field_error("lesson", "You cannot create a Quizee for this course")
        if lesson.lesson_type not in ['QUIZ', 'ASSIGNMENT']:
            return field_error("lesson","You cannot create a quiz for this type of lesson")
        if Quiz.objects.filter(lesson=lesson).exists():
            return field_error("lesson", "Quiz already exists for this lesson")
        
        return lesson

class UpQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'title']
        read_only_fields = ['id']
        
    def validate_title(self, title):
        if not title:
            return field_error("title", 'Title is required')
        title = title.strip()
        
        if len(title) > 1000:
            return field_error("title", "Title cannot exceed 1000 characters long")
        
        return title
    
class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'quiz', 'question', 'question_type']
        read_only_fields = ['id']
        
    def validate_question(self, question):
        if not question:
            return field_error("question", 'Question is required')
        question = question.strip()
        if len(question) > 2000:
            return field_error("question", "Question cannot exceed 2000 characters long")
        
        return question
    
    def validate_quiz(self, quiz):
        if not quiz:
            return field_error("quiz", "Quiz must be set")
        user = self.context.get('request').user
        if quiz.lesson.module.course.instructor != user:
            return field_error("quiz", "You cannot create a question for this quiz")        
        
        return quiz
    
    def validate_question_type(self, question_type):
        if not question_type:
            return field_error("question_type", "Question type is required")
        if question_type not in Question.QuestionTypes.values:
            return field_error("question_type", "Invalid question type")
        
        return question_type
    
class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizOption
        fields = ['id','question', 'option', 'is_correct']
        read_only_fields = ['id']
        
    def validate_question(self, question):
        if not question:
            return field_error("question", 'Question is required')
        user = self.context.get('request').user
        if question.quiz.lesson.module.course.instructor != user:
            return field_error("question", "You have no permission to create an option for this question")
        if question.question_type == "TEXT" and QuizOption.objects.filter(question=question).exists():
            return field_error("question", "You cannot create a multiple options for this type question")
        
        return question
    
    def validate(self, attrs):
        is_correct = attrs.get('is_correct')
        question = attrs.get('question')
        if is_correct and question.question_type == "RADIO" and QuizOption.objects.filter(question=question, is_correct=True).exists():
            return field_error("is_correct","You cannot create two correct options for this type question")
        if question.question_type == "TEXT" and not is_correct:
            return field_error("is_correct", "This type question can only have a single and correct option")
        
        return attrs
    
    
# GET QUIZ
class OptionMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizOption
        fields = ['id', 'option']
        read_only_fields = fields

class QuestionWithOptionSerializer(serializers.ModelSerializer):
    options = OptionMiniSerializer(many=True)
    class Meta:
        model = Question
        fields = ['id', 'question', 'question_type', 'options']
        read_only_fields = fields


class GetQuizSerializer(serializers.ModelSerializer):
    questions = QuestionWithOptionSerializer(many=True)
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'lesson', 'questions']
        read_only_fields = fields
        

class QuizAttemptSerializer(serializers.ModelSerializer):
    response = serializers.ListField(write_only=True)
    correct_count = serializers.SerializerMethodField()
    class Meta:
        model = QuizAttempt
        fields = ['response', 'score', 'correct_count']
        read_only_fields = ['score', 'correct_count']
        extra_kwargs = {'score': {'coerce_to_string': False}}
        
    def validate_response(self, response):
        quiz = self.context.get('quiz')
        if not isinstance(response, list):
            return field_error("response", "Response must be a list")
        if len(response) != quiz.questions.count():
            return field_error("response", "Response must contain an answer for every question in the quiz")
        
        return response
        
    def get_correct_count(self, obj):
        return getattr(obj, '_correct_count', 0)
        
    def save(self, **kwargs):
        response = self.validated_data.get('response')
        quiz = self.context.get('quiz')
        questions = Question.objects.filter(quiz=quiz)
        counter = 0
        for answer in response:
            try:
                question_id = uuid.UUID(str(answer['question_id']))
            except (KeyError, ValueError, TypeError):
                return field_error("response", "Response contains invalid data")
            try:
                selected_options = answer['selected_options']
            except KeyError:
                return field_error("response", "Response is missing selected_options for a question")
            if not isinstance(selected_options, list):
                return field_error("response", "selected_options must be a list")
            question = questions.filter(pk=question_id).first()
            if not question:
                return field_error("response", "Response contains a question that is not part of this quiz")
            if question.question_type == "RADIO":
                correct_option = question.options.filter(is_correct=True).first()
                if not correct_option:
                    return field_error("response", "No correct answer found for a question")
                if len(selected_options) == 1 and str(selected_options[0]) == str(correct_option.pk):
                    counter += 1
            elif question.question_type == "CHECKBOX":
                correct_options = question.options.filter(is_correct=True)
                if len(correct_options) < 1:
                    return field_error("response", "No correct answers found for a question")
                correct = set(str(pk) for pk in correct_options.values_list('pk', flat=True))
                selected = set(str(pk) for pk in selected_options)
                if selected == correct:
                    counter += 1
            elif question.question_type == "TEXT":
                correct_option = question.options.filter(is_correct=True).first()
                if not correct_option:
                    return field_error("response", "No correct answer found for a question")
                if len(selected_options) > 0 and correct_option.option.strip().lower() == str(selected_options[0]).strip().lower():
                    counter += 1
        total = len(questions)
        score = round(Decimal(counter) / Decimal(total) * 100, 2) if total else Decimal("0.00")
        student = self.context.get('user')
        attempt = QuizAttempt.objects.create(score=score, quiz=quiz, student=student)
        attempt._correct_count = counter
        self.instance = attempt
        
        profile = StudentProfile.objects.filter(student=student).first()
        if profile:
            profile.xp = profile.xp + int(score * (XP_QUANTITY + 3 * profile.level) // 100)
            profile.save(update_fields=['xp'])
        
        return attempt
        
        
data = [
    {
        "question_id": "question_id",
        "selected_options": [
            "option_id",
            "option_id"
        ]
    },
    {
        "question": "question_id",
        "selected_options": [
            "option_id"
        ]
    },
    {
        "question": "question_id",
        "selected_options": [
            "Text info data"
        ]
    },
]