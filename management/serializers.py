from rest_framework import serializers
from authentication.models import CustomUser
from profiles.models import InstructorProfile, StudentProfile
from courses.models import Course, Module, Lesson
from enrollments.models import Enrollment
from payments.models import StudentWallet, WalletTransaction
from notifications.models import Notification
from baseapp.utils import field_error
from baseapp.emails import send_notification
from django.db.models import Q
from decimal import Decimal


# ──────────────────────────────────────────────
#  DASHBOARD
# ──────────────────────────────────────────────

class DashboardSerializer(serializers.Serializer):
    total_students = serializers.IntegerField()
    total_instructors = serializers.IntegerField()
    total_courses = serializers.IntegerField()
    published_courses = serializers.IntegerField()
    in_review_courses = serializers.IntegerField()
    draft_courses = serializers.IntegerField()
    rejected_courses = serializers.IntegerField()
    total_enrollments = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)


# ──────────────────────────────────────────────
#  USER / INSTRUCTOR / STUDENT LISTING
# ──────────────────────────────────────────────

class AdminUserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'first_name', 'last_name', 'email',
            'phone_number', 'user_role', 'account_status',
            'email_verified', 'phone_verified', 'thumbnail', 'photo',
            'created_at',
        ]


class InstructorListSerializer(serializers.ModelSerializer):
    instructor_id = serializers.UUIDField(source='instructor.id', read_only=True)
    email = serializers.EmailField(source='instructor.email', read_only=True)
    first_name = serializers.CharField(source='instructor.first_name', read_only=True)
    last_name = serializers.CharField(source='instructor.last_name', read_only=True)
    account_status = serializers.CharField(source='instructor.account_status', read_only=True)

    class Meta:
        model = InstructorProfile
        fields = [
            'instructor_id', 'email', 'first_name', 'last_name',
            'account_status', 'headline', 'approval_status',
            'total_courses_created', 'total_students_taught', 'created_at',
        ]


class InstructorDetailSerializer(serializers.ModelSerializer):
    instructor = AdminUserMiniSerializer(read_only=True)

    class Meta:
        model = InstructorProfile
        fields = [
            'id', 'instructor', 'headline', 'bio',
            'linkedin_url', 'website_url', 'approval_status',
            'total_courses_created', 'total_students_taught', 'created_at',
        ]


class StudentListSerializer(serializers.ModelSerializer):
    student_id = serializers.UUIDField(source='student.id', read_only=True)
    email = serializers.EmailField(source='student.email', read_only=True)
    first_name = serializers.CharField(source='student.first_name', read_only=True)
    last_name = serializers.CharField(source='student.last_name', read_only=True)
    account_status = serializers.CharField(source='student.account_status', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'student_id', 'email', 'first_name', 'last_name',
            'account_status', 'xp', 'streak', 'level',
            'total_courses_enrolled', 'total_courses_completed',
            'total_certificates_earned', 'created_at',
        ]


class StudentDetailSerializer(serializers.ModelSerializer):
    student = AdminUserMiniSerializer(read_only=True)
    wallet_id = serializers.SerializerMethodField()
    wallet_balance = serializers.SerializerMethodField()

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'student', 'gender', 'bio', 'xp', 'streak', 'level',
            'total_courses_enrolled', 'total_courses_completed',
            'total_certificates_earned', 'wallet_id', 'wallet_balance',
            'created_at',
        ]

    def get_wallet_id(self, obj):
        wallet = getattr(obj.student, 'wallet', None)
        return wallet.wallet_id if wallet else None

    def get_wallet_balance(self, obj):
        wallet = getattr(obj.student, 'wallet', None)
        return str(wallet.balance) if wallet else None


# ──────────────────────────────────────────────
#  COURSE LISTING & REVIEW
# ──────────────────────────────────────────────

class AdminCourseListSerializer(serializers.ModelSerializer):
    instructor_name = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'status', 'pricing_type', 'price',
            'level', 'language', 'total_enrollments', 'average_rating',
            'rating_count', 'total_reviews', 'instructor_name',
            'category_name', 'created_at', 'published_at',
        ]

    def get_instructor_name(self, obj):
        return f"{obj.instructor.first_name} {obj.instructor.last_name}".strip()

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None


class AdminCourseDetailSerializer(serializers.ModelSerializer):
    instructor = AdminUserMiniSerializer(read_only=True)
    category_name = serializers.SerializerMethodField()
    module_count = serializers.SerializerMethodField()
    lesson_count = serializers.SerializerMethodField()
    modules = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'subtitle', 'description',
            'status', 'pricing_type', 'price', 'level', 'language',
            'thumbnail', 'intro_video', 'requirements', 'what_included',
            'total_enrollments', 'average_rating', 'rating_count',
            'total_reviews', 'total_shares', 'total_reading_time',
            'instructor', 'category_name', 'module_count', 'lesson_count',
            'modules', 'created_at', 'published_at', 'updated_at',
        ]

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_module_count(self, obj):
        return obj.modules.count()

    def get_lesson_count(self, obj):
        return Lesson.objects.filter(module__course=obj).count()

    def get_modules(self, obj):
        modules = obj.modules.prefetch_related('lessons')
        return AdminModuleSerializer(modules, many=True).data



class AdminLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'lesson_type', 'duration_minutes', 'order', 'video_url']
        read_only_fields = fields


class AdminQuizOptionSerializer(serializers.ModelSerializer):
    class Meta:
        from quizzes.models import QuizOption
        model = QuizOption
        fields = ['id', 'option', 'is_correct']
        read_only_fields = fields


class AdminQuizQuestionSerializer(serializers.ModelSerializer):
    options = AdminQuizOptionSerializer(many=True, read_only=True)

    class Meta:
        from quizzes.models import Question
        model = Question
        fields = ['id', 'question', 'question_type', 'options']
        read_only_fields = fields


class AdminQuizSerializer(serializers.ModelSerializer):
    questions = AdminQuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        from quizzes.models import Quiz
        model = Quiz
        fields = ['id', 'title', 'questions']
        read_only_fields = fields


class AdminLessonDetailSerializer(serializers.ModelSerializer):
    module_title = serializers.CharField(source='module.title', read_only=True)
    course_id = serializers.UUIDField(source='module.course.id', read_only=True)
    course_title = serializers.CharField(source='module.course.title', read_only=True)
    quiz = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'lesson_type', 'video_url', 'content',
            'duration_minutes', 'order', 'is_preview',
            'module_title', 'course_id', 'course_title', 'quiz',
        ]
        read_only_fields = fields

    def get_quiz(self, obj):
        quiz = getattr(obj, 'quiz', None)
        if quiz:
            return AdminQuizSerializer(quiz).data
        return None

class AdminModuleSerializer(serializers.ModelSerializer):
    lessons = AdminLessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'title', 'order', 'lessons']
        read_only_fields = fields

class CourseStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[('PUBLISHED', 'Published'), ('REJECTED', 'Rejected')],
        help_text="Only PUBLISHED or REJECTED allowed. Course must be IN_REVIEW.",
    )

    def validate_status(self, value):
        if value not in ('PUBLISHED', 'REJECTED'):
            raise serializers.ValidationError("Only PUBLISHED or REJECTED are allowed.")
        return value


class InstructorApprovalSerializer(serializers.Serializer):
    approval_status = serializers.ChoiceField(
        choices=[('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
    )

    def validate_approval_status(self, value):
        if value not in ('APPROVED', 'REJECTED'):
            raise serializers.ValidationError("Only APPROVED or REJECTED are allowed.")
        return value


# ──────────────────────────────────────────────
#  WALLET TOP-UP
# ──────────────────────────────────────────────

class WalletTopupSerializer(serializers.Serializer):
    wallet_id = serializers.CharField(max_length=8)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_wallet_id(self, value):
        value = value.strip().upper()
        if len(value) != 8:
            raise serializers.ValidationError("Wallet ID must be exactly 8 characters.")
        wallet = StudentWallet.objects.filter(wallet_id=value).first()
        if not wallet:
            raise serializers.ValidationError("Wallet not found.")
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def save(self, **kwargs):
        wallet_id = self.validated_data['wallet_id']
        amount = self.validated_data['amount']
        wallet = StudentWallet.objects.get(wallet_id=wallet_id)
        wallet.balance += amount
        wallet.save()
        WalletTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type=WalletTransaction.TransactionTypes.REPLENISH,
        )
        Notification.objects.create(
            user=wallet.student,
            message=f"Your wallet has been topped up with ${amount} by admin.",
            notif_type=Notification.NotifTypes.REPLENISH,
        )
        send_notification(
            wallet.student.email,
            message=f"Your balance has been replenished by ${amount}",
            data={"total": str(wallet.balance), "received": str(amount)},
        )
        return wallet


# ──────────────────────────────────────────────
#  NOTIFICATIONS
# ──────────────────────────────────────────────

class SendNotificationSerializer(serializers.Serializer):
    NOTIF_TYPES = [c[0] for c in Notification.NotifTypes.choices]

    message = serializers.CharField(max_length=2000)
    notif_type = serializers.ChoiceField(choices=NOTIF_TYPES, default='NOTIFICATION')
    send_to = serializers.ChoiceField(
        choices=[('all', 'All'), ('specific', 'Specific'), ('filtered', 'Filtered')],
    )
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="Required when send_to='specific'. List of user UUIDs.",
    )
    role = serializers.ChoiceField(
        choices=[c[0] for c in CustomUser.UserRole.choices],
        required=False,
        help_text="Required when send_to='filtered'. Filter by role.",
    )
    has_enrollment = serializers.BooleanField(
        required=False,
        help_text="Optional filter: only students with active enrollments.",
    )

    def validate(self, data):
        send_to = data.get('send_to')
        if send_to == 'specific' and not data.get('user_ids'):
            raise serializers.ValidationError(
                {"user_ids": "user_ids is required when send_to='specific'."}
            )
        if send_to == 'filtered' and not data.get('role'):
            raise serializers.ValidationError(
                {"role": "role is required when send_to='filtered'."}
            )
        return data

    def save(self, **kwargs):
        data = self.validated_data
        message = data['message']
        notif_type = data['notif_type']
        send_to = data['send_to']
        sender = self.context['request'].user

        users = CustomUser.objects.none()

        if send_to == 'all':
            users = CustomUser.objects.filter(account_status='ACTIVE')
        elif send_to == 'specific':
            users = CustomUser.objects.filter(id__in=data['user_ids'], account_status='ACTIVE')
        elif send_to == 'filtered':
            users = CustomUser.objects.filter(user_role=data['role'], account_status='ACTIVE')
            if data.get('has_enrollment'):
                enrolled_student_ids = Enrollment.objects.values_list('student_id', flat=True).distinct()
                users = users.filter(id__in=enrolled_student_ids)

        notifications = [
            Notification(user=user, message=message, notif_type=notif_type, sender=sender)
            for user in users
        ]
        Notification.objects.bulk_create(notifications, batch_size=500)
        return {"notifications_created": len(notifications)}


# ──────────────────────────────────────────────
#  ENROLLMENT LISTING (within admin)
# ──────────────────────────────────────────────

class AdminEnrollmentSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source='student.email', read_only=True)
    student_name = serializers.SerializerMethodField()
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id', 'student_email', 'student_name', 'course_title',
            'status', 'has_access', 'is_bought', 'progress_percentage',
            'enrolled_at', 'completed_at',
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}".strip()

