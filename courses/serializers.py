from rest_framework import serializers
from baseapp.utils import field_error
from .models import Course, Category, Module, Lesson, Tag
from authentication.models import CustomUser
from django.utils.text import slugify
from baseapp.utils import field_error


from rest_framework import serializers
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Course, Category, Tag

class CategoryGetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon']
        read_only_fields = ['id', 'slug']
        
    def validate_name(self, value):
        value = value.strip()
        
        if len(value) > 100:
            return field_error("name", "Name cannot exceed 100 characters long")
        elif len(value) < 5:
            return field_error("name", "Name must be at least 5 characters long")
        return value
    
    def validate_icon(self, value):
        value = value.strip()
        if len(value) > 20:
            return field_error("icon", "Icon cannot exceed 20 characters long")
        
        return value
    
    def create(self, validated_data):
        return super().create(validated_data)
    
     
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']
        
    def validate_name(self, value):
        value = value.strip()
        
        if len(value) > 50:
            return field_error("name", "Name cannot exceed 50 characters long")
        elif len(value) < 5:
            return field_error("name", "Name must be at least 5 characters long")
        return value
    
    def create(self, validated_data):
        return super().create(validated_data)
        

class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'subtitle', 'description',
            'category', 'tags', 'level', 'language', 'thumbnail',
            'intro_video', 'pricing_type', 'price', 'requirements',
            'what_included'
        ]
        read_only_fields = ['id','slug']


    def validate_title(self, value):
        value = value.strip()
        if len(value) < 5:
            return field_error("title", "Title must be at least 5 characters long")
        if len(value) > 300:
            return field_error("title", "Title cannot exceed 300 characters")
        return value

    def validate_description(self, value):
        value = value.strip()
        if len(value) < 20:
            return field_error("description", "Description must be at least 20 characters long")
        return value

    def validate_category(self, value):
        if value is None:
            return field_error("category", "Category is required")
        return value

    def validate_tags(self, value):
        if len(value) > 10:
            return field_error("tags", "You can assign a maximum of 10 tags to a course.")
        return value

    def validate_language(self, value):
        # Adjust this list to whatever languages your platform actually supports
        supported_languages = ['en', 'uz', 'ru', 'es', 'fr', 'de', 'zh', 'ar']
        if value not in supported_languages:
            return field_error("language", f"'{value}' is not a supported language code. Choose one of: {', '.join(supported_languages)}."
            )
        return value

    def validate_thumbnail(self, value):
        if value:
            max_size_mb = 10
            if value.size > max_size_mb * 1024 * 1024:
                return field_error("thubmnail", f"Thumbnail size must not exceed {max_size_mb}MB.")

            valid_extensions = ['jpg', 'jpeg', 'png', 'webp']
            ext = value.name.rsplit('.', 1)[-1].lower()
            if ext not in valid_extensions:
                return field_error("thubmnail", f"Unsupported image format '.{ext}'. Allowed formats: {', '.join(valid_extensions)}.")
        return value

    def validate_intro_video(self, value):
        if value:
            allowed_domains = ['youtube.com', 'youtu.be', 'vimeo.com']
            if not any(domain in value for domain in allowed_domains):
                return field_error("intro_video", "Intro video must be a link from YouTube or Vimeo.")
        return value

    def validate_price(self, value):
        if value is not None and value < 0:
            return field_error("price", "Price cannot be negative.")
        return value

    def validate_requirements(self, value):
        if value and len(value.strip()) > 1000:
            return field_error("requirements", "Requirements cannot exceed 1000 characters.")
        return value

    def validate_what_included(self, value):
        if value and len(value.strip()) > 1500:
            return field_error("what_included", "'What's included' cannot exceed 1500 characters")
        return value


    def validate(self, attrs):
        pricing_type = attrs.get(
            'pricing_type',
            getattr(self.instance, 'pricing_type', None)
        )
        price = attrs.get(
            'price',
            getattr(self.instance, 'price', None)
        )

        if pricing_type == Course.PricingType.FREE:
            attrs['price'] = None
        elif pricing_type in (Course.PricingType.MONTHLY, Course.PricingType.SPECIAL):
            if price is None:
                return field_error("price", "Price is required for monthly or special pricing")
            if price <= 0:
                return field_error("price", "Price must be greater than 0 for paid courses")

        return attrs
    
    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)

        new_title = validated_data.get('title')
        if new_title and new_title != instance.title:
            base_slug = slugify(new_title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            instance.slug = slug

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)

        return instance
        
    
    def create(self, validated_data):
        request = self.context['request']
        tags = validated_data.pop('tags', [])
        validated_data['instructor'] = request.user
        
        course = Course.objects.create(**validated_data)
        if tags:
            course.tags.set(tags)
        return course


class ModuleCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ["id", 'course', 'title', 'order']
        read_only_fields = ['id']

    def validate_course(self, value):
        if value.instructor != self.context['request'].user:
            return field_error("course","You have no access to create a module for this course")
        return value

    def validate_title(self, value):
        value = value.strip()
        if not value:
            return field_error("title","Title cannot be empty")
        if len(value) > 255:
            return field_error("title","Title cannot exceed 255 characters long")
        return value

    def validate_order(self, value):
        if value <= 0:
            return field_error("order","Order must be bigger than 0")
        return value


class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'module', 'title', 'lesson_type', 'video_url', 'content', 'duration_minutes', 'order', 'is_preview']
        read_only_fields = ['id']
        
    def validate_title(self, value):
        value = value.strip()
        if not value:
            return field_error("title", "Title cannot be blank")
        if len(value) > 255:
            return field_error("title", "Title cannot exceed 255 characters long")
        
        return value
        
    def validate_lesson_type(self, value):
        if value not in Lesson.LessonType.values:
            field_error("lesson_type", f"Lesson type must be one of {Lesson.LessonType.values}")
        return value
    
    def validate_module(self, value):
        if value.course.instructor != self.context['request'].user:
            field_error("module", "You have no access to add a lesson to this module")
        return value
    
    def validate_duration_minutes(self, value):
        if not value:
            return field_error("duration_minutes", "Duration time must be greater than 0")
        
        return value
    
    def validate_order(self, value):
        if not value:
            return field_error("order", "Order time must be greater than 0")
        
        return value
        
    def validate(self, attrs):
        lesson_type = attrs.get('lesson_type', getattr(self.instance, 'lesson_type', None))
        video_url = attrs.get('video_url', getattr(self.instance, 'video_url', None))
        content = attrs.get('content', getattr(self.instance, 'content', None))

        if lesson_type == Lesson.LessonType.VIDEO and not video_url:
            field_error("video_url", "Video URL is required for video lessons")

        if lesson_type == Lesson.LessonType.ARTICLE and not content:
            field_error("content", "Content is required for article lessons")

        return attrs

# MODULE DETAIL
class CourseMinimalSerializer(serializers.ModelSerializer):
    modules = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields = ['id', 'title', 'slug', 'modules']

    def get_modules(self, obj):
        return list(obj.modules.order_by('order').values('id', 'title', 'order'))


class LessonSerializer(serializers.ModelSerializer):
    quiz = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'lesson_type', 'duration_minutes', 'order', 'is_preview', 'quiz',
        ]

    def get_quiz(self, obj):
        quiz = getattr(obj, 'quiz', None)
        if quiz:
            return {'id': str(quiz.pk), 'title': quiz.title}
        return None


class ModuleDetailSerializer(serializers.ModelSerializer):
    course = CourseMinimalSerializer(read_only=True)
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'title', 'order', 'course', 'lessons']
        read_only_fields = fields

# COURSE DETAIL
class ModuleMinimalSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'title', 'order', 'course', 'lessons']

class InstructorMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'thumbnail']
        read_only_fields = fields

class CourseDetailSerializer(serializers.ModelSerializer):
    modules = ModuleMinimalSerializer(many=True, read_only=True)
    instructor = InstructorMiniSerializer()
    is_enrolled = serializers.SerializerMethodField()
    last_accessed_lesson = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields = [
            'id', 'instructor', 'is_enrolled', 'last_accessed_lesson', 'title', 'slug', 'subtitle', 'description', 'category',
            'tags', 'level', 'language', 'thumbnail', 'intro_video', 'pricing_type',
            'price', 'status', 'published_at', 'total_enrollments', 'average_rating', 'total_shares', 'total_reading_time',
            'rating_count', 'total_reviews', 'requirements', 'what_included', 'modules',
        ]
        
    def get_is_enrolled(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            if user.enrollments.filter(course=obj).exists():
                return True
        return False
        
    def get_last_accessed_lesson(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            enrollment = user.enrollments.filter(course=obj).first()
            if enrollment and enrollment.last_accessed_lesson_id:
                return str(enrollment.last_accessed_lesson_id)
        return None
        
        
# LESSON DETAIL
class LessonCurriculumModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    class Meta:
        model = Module
        fields = ['id', 'title', 'order', 'lessons']

class LessonCurriculumSerializer(serializers.ModelSerializer):
    modules = LessonCurriculumModuleSerializer(many=True, read_only=True)
    class Meta:
        model = Course
        fields = ['id', 'title', 'slug', 'modules']

class LessonDetailSerializer(serializers.ModelSerializer):
    module = ModuleMinimalSerializer(read_only=True)
    curriculum = serializers.SerializerMethodField()
    progress_id = serializers.SerializerMethodField()
    progress_completed = serializers.SerializerMethodField()
    quiz = serializers.SerializerMethodField()
    is_locked = serializers.SerializerMethodField()
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'lesson_type', 'is_locked', 'video_url', 'content', 'duration_minutes', 'order', 'is_preview', 'module', 'curriculum', 'progress_id', 'progress_completed', 'quiz']
        read_only_fields = fields
        
    def get_curriculum(self, obj):
        return LessonCurriculumSerializer(obj.module.course).data

    def _get_progress(self, obj):
        user = self.context.get('request').user
        if not (user and user.is_authenticated):
            return None
        enrollment = user.enrollments.filter(course=obj.module.course).first()
        if not enrollment:
            return None
        return enrollment.lessons_progress.filter(lesson=obj).first()

    def get_progress_id(self, obj):
        progress = self._get_progress(obj)
        return str(progress.pk) if progress else None

    def get_progress_completed(self, obj):
        progress = self._get_progress(obj)
        return bool(progress and progress.is_completed)

    def get_quiz(self, obj):
        quiz = getattr(obj, 'quiz', None)
        return str(quiz.pk) if quiz else None
    
    def get_is_locked(self, obj):
        user = self.context.get('request').user
        enrollment = user.enrollments.filter(course=obj.module.course).first()
        return not enrollment or not enrollment.lessons_progress.filter(lesson=obj).exists()
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data['is_locked']:
            data['video_url'] = None
            data['content'] = None
            data['quiz'] = None
        return data




# COURSE INFO
class CourseInfoSerializer(serializers.ModelSerializer):
    instructor = serializers.SerializerMethodField()
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'subtitle', 'category', 'level', 'language', 'thumbnail', 'total_enrollments',
            'average_rating', 'rating_count', 'total_reviews', 'instructor', 'status', 'pricing_type', 'price',
            'total_shares', 'total_reading_time',
        ]
        read_only_fields = fields
    def get_instructor(self, obj):
        instructor = obj.instructor
        return {
            'id':instructor.pk,
            'full_name': f"{instructor.first_name} {instructor.last_name}",
            "thumbnail": instructor.thumbnail.url if instructor.thumbnail else None
        }
  
        
            
        
    
