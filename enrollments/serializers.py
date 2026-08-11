from rest_framework import serializers
from .models import Enrollment, LessonProgress
from baseapp.utils import field_error, XP_QUANTITY, interest_recorder
from courses.models import Lesson
from courses.serializers import CourseInfoSerializer
from profiles.models import StudentProfile


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ['id', 'course']
        read_only_fields = ['id']
        
    def validate_course(self, course):
        if not course:
            return field_error("course", "Course not found")
        if course.status != "PUBLISHED":
            return field_error("course", 'Course not found')
        
        student = self.context.get('request').user
        if course.enrollments.filter(student=student).exists():
            return field_error("course", 'Course already enrolled')
        
        return course
        
    def create(self, validated_data):
        student = self.context.get('request').user
        validated_data['student'] = student
        
        enrollment = Enrollment.objects.create(**validated_data)
        course = validated_data['course']

        interest_recorder(student, course.tags)
        
        
        return enrollment
    

class ProgressCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = ['id', 'lesson']
        read_only_fields = ['id']


    def validate(self, data):
        student = self.context.get('request').user
        lesson = data.get('lesson')
        enrollment = student.enrollments.filter(lesson=lesson).first()
        if not enrollment:
            return field_error("lesson", "Enrollment for this lesson not found")
        
        if not enrollment.has_access:
            raise serializers.ValidationError({"enrollment": "You have no access for this course"})
                
        if lesson.module.course_id != enrollment.course_id:
            raise serializers.ValidationError(
                {"lesson": "Lesson does not belong to the enrolled course"}
            )

        course_lessons = list(
            Lesson.objects.filter(module__course_id=enrollment.course_id)
            .order_by('module__order', 'order')
            .values_list('id', flat=True)
        )
        lesson_index = course_lessons.index(lesson.id)

        if lesson_index > 0:
            previous_lesson_id = course_lessons[lesson_index - 1]
            completed_previous = enrollment.lessons_progress.filter(
                is_completed=True, lesson_id=previous_lesson_id
            ).exists()
            if not completed_previous:
                return field_error("lesson", "You must complete the previous lesson first")

        return data
    

    
class LastLessonSerializer(serializers.ModelSerializer):
    lesson = serializers.SerializerMethodField()
    class Meta:
        model = LessonProgress
        fields = ['id', 'lesson']
        read_only_fields = fields
        
    def get_lesson(self, obj):
        obj = obj.lesson
        return {"id": obj.pk, "title": obj.title, "module": obj.module.title}


class EnrolledCourseSerializer(serializers.ModelSerializer):
    course = CourseInfoSerializer()
    first_lesson = serializers.SerializerMethodField()
    class Meta:
        model = Enrollment
        fields = ['id', 'course', 'status', 'first_lesson', 'is_bought', 'progress_percentage', 'last_accessed_lesson', 'last_accessed_at', 'enrolled_at', 'completed_at']
        read_only_fields = fields

    def get_first_lesson(self, obj):
        module = obj.course.modules.order_by('order').first()
        lesson = module.lessons.order_by('order').first() if module else None
        return str(lesson.pk) if lesson else None