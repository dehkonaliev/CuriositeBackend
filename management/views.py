from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Q

from authentication.models import CustomUser
from profiles.models import InstructorProfile, StudentProfile
from courses.models import Course, Lesson
from enrollments.models import Enrollment
from payments.models import StudentWallet

from .permissions import IsSuperuser
from .serializers import (
    DashboardSerializer,
    InstructorListSerializer,
    InstructorDetailSerializer,
    InstructorApprovalSerializer,
    StudentListSerializer,
    StudentDetailSerializer,
    AdminCourseListSerializer,
    AdminCourseDetailSerializer,
    CourseStatusSerializer,
    AdminLessonDetailSerializer,
    WalletTopupSerializer,
    SendNotificationSerializer,
    AdminEnrollmentSerializer,
)
from baseapp.utils import success_response, error_response


# ──────────────────────────────────────────────
#  DASHBOARD – platform-wide stats
# ──────────────────────────────────────────────

class AdminDashboardView(APIView):
    permission_classes = [IsSuperuser]

    def get(self, request):
        total_students = CustomUser.objects.filter(user_role='STUDENT').count()
        total_instructors = CustomUser.objects.filter(user_role='INSTRUCTOR').count()

        course_counts = dict(
            Course.objects.aggregate(
                total=Count('id'),
                published=Count('id', filter=Q(status='PUBLISHED')),
                in_review=Count('id', filter=Q(status='IN_REVIEW')),
                draft=Count('id', filter=Q(status='DRAFT')),
                rejected=Count('id', filter=Q(status='REJECTED')),
            )
        )

        total_enrollments = Enrollment.objects.count()
        total_revenue = (
            StudentWallet.objects.aggregate(
                total=Sum('balance')
            )['total']
            or 0
        )

        data = {
            "total_students": total_students,
            "total_instructors": total_instructors,
            "total_courses": course_counts['total'],
            "published_courses": course_counts['published'],
            "in_review_courses": course_counts['in_review'],
            "draft_courses": course_counts['draft'],
            "rejected_courses": course_counts['rejected'],
            "total_enrollments": total_enrollments,
            "total_revenue": total_revenue,
        }

        serializer = DashboardSerializer(data)
        return success_response("Dashboard stats retrieved.", serializer.data)


# ──────────────────────────────────────────────
#  INSTRUCTORS
# ──────────────────────────────────────────────

class AdminInstructorListView(APIView):
    permission_classes = [IsSuperuser]

    def get(self, request):
        profiles = InstructorProfile.objects.select_related('instructor').all()

        approval = request.query_params.get('approval_status')
        if approval:
            profiles = profiles.filter(approval_status=approval.upper())

        search = request.query_params.get('search')
        if search:
            profiles = profiles.filter(
                Q(instructor__first_name__icontains=search)
                | Q(instructor__last_name__icontains=search)
                | Q(instructor__email__icontains=search)
            )

        serializer = InstructorListSerializer(profiles, many=True)
        return success_response("Instructors retrieved.", serializer.data)


class AdminInstructorDetailView(APIView):
    permission_classes = [IsSuperuser]

    def get(self, request, pk):
        try:
            profile = InstructorProfile.objects.select_related('instructor').get(instructor_id=pk)
        except InstructorProfile.DoesNotExist:
            return error_response("Instructor not found.", status_code=404)

        serializer = InstructorDetailSerializer(profile)
        return success_response("Instructor detail retrieved.", serializer.data)


class AdminInstructorApprovalView(APIView):
    permission_classes = [IsSuperuser]

    def patch(self, request, pk):
        try:
            profile = InstructorProfile.objects.select_related('instructor').get(instructor_id=pk)
        except InstructorProfile.DoesNotExist:
            return error_response("Instructor not found.", status_code=404)

        serializer = InstructorApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['approval_status']
        profile.approval_status = new_status
        profile.save()

        return success_response(
            f"Instructor approval status updated to {new_status}.",
            InstructorDetailSerializer(profile).data,
        )


# ──────────────────────────────────────────────
#  STUDENTS
# ──────────────────────────────────────────────

class AdminStudentListView(APIView):
    permission_classes = [IsSuperuser]

    def get(self, request):
        profiles = StudentProfile.objects.select_related('student').all()

        search = request.query_params.get('search')
        if search:
            profiles = profiles.filter(
                Q(student__first_name__icontains=search)
                | Q(student__last_name__icontains=search)
                | Q(student__email__icontains=search)
            )

        status_filter = request.query_params.get('status')
        if status_filter:
            profiles = profiles.filter(student__account_status=status_filter.upper())

        serializer = StudentListSerializer(profiles, many=True)
        return success_response("Students retrieved.", serializer.data)


class AdminStudentDetailView(APIView):
    permission_classes = [IsSuperuser]

    def get(self, request, pk):
        try:
            profile = StudentProfile.objects.select_related('student').get(student_id=pk)
        except StudentProfile.DoesNotExist:
            return error_response("Student not found.", status_code=404)

        serializer = StudentDetailSerializer(profile)
        return success_response("Student detail retrieved.", serializer.data)


# ──────────────────────────────────────────────
#  COURSES – list, detail, status change
# ──────────────────────────────────────────────

class AdminCourseListView(APIView):
    permission_classes = [IsSuperuser]

    def get(self, request):
        courses = Course.objects.select_related('instructor', 'category').all()

        course_status = request.query_params.get('status')
        if course_status:
            courses = courses.filter(status=course_status.upper())

        search = request.query_params.get('search')
        if search:
            courses = courses.filter(
                Q(title__icontains=search)
                | Q(instructor__first_name__icontains=search)
                | Q(instructor__last_name__icontains=search)
            )

        category = request.query_params.get('category')
        if category:
            courses = courses.filter(category__slug=category)

        level = request.query_params.get('level')
        if level:
            courses = courses.filter(level=level.upper())

        ordering = request.query_params.get('ordering', '-created_at')
        courses = courses.order_by(ordering)

        serializer = AdminCourseListSerializer(courses, many=True)
        return success_response("Courses retrieved.", serializer.data)


class AdminCourseDetailView(APIView):
    permission_classes = [IsSuperuser]

    def get(self, request, pk):
        try:
            course = Course.objects.select_related('instructor', 'category').prefetch_related('modules', 'modules__lessons').get(pk=pk)
        except Course.DoesNotExist:
            return error_response("Course not found.", status_code=404)

        serializer = AdminCourseDetailSerializer(course)
        return success_response("Course detail retrieved.", serializer.data)


class AdminCourseStatusView(APIView):
    permission_classes = [IsSuperuser]

    def patch(self, request, pk):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return error_response("Course not found.", status_code=404)

        if course.status != 'IN_REVIEW':
            return error_response(
                "Only courses with IN_REVIEW status can be published or rejected.",
                status_code=400,
            )

        serializer = CourseStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        course.status = new_status

        if new_status == 'PUBLISHED':
            from django.utils import timezone
            course.published_at = timezone.now()

        course.save()

        return success_response(
            f"Course status updated to {new_status}.",
            AdminCourseDetailSerializer(course).data,
        )


class AdminLessonDetailView(APIView):
    permission_classes = [IsSuperuser]

    def get(self, request, pk):
        try:
            lesson = Lesson.objects.select_related('module', 'module__course').get(pk=pk)
        except Lesson.DoesNotExist:
            return error_response("Lesson not found.", status_code=404)

        serializer = AdminLessonDetailSerializer(lesson)
        return success_response("Lesson detail retrieved.", serializer.data)


# ──────────────────────────────────────────────
#  ENROLLMENTS – view all
# ──────────────────────────────────────────────

class AdminEnrollmentListView(APIView):
    permission_classes = [IsSuperuser]

    def get(self, request):
        enrollments = Enrollment.objects.select_related('student', 'course').all()

        course_id = request.query_params.get('course_id')
        if course_id:
            enrollments = enrollments.filter(course_id=course_id)

        student_id = request.query_params.get('student_id')
        if student_id:
            enrollments = enrollments.filter(student_id=student_id)

        enroll_status = request.query_params.get('status')
        if enroll_status:
            enrollments = enrollments.filter(status=enroll_status.upper())

        serializer = AdminEnrollmentSerializer(enrollments, many=True)
        return success_response("Enrollments retrieved.", serializer.data)


# ──────────────────────────────────────────────
#  WALLET TOP-UP
# ──────────────────────────────────────────────

class AdminWalletTopupView(APIView):
    permission_classes = [IsSuperuser]

    def post(self, request):
        serializer = WalletTopupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wallet = serializer.save()

        return success_response(
            "Wallet topped up successfully.",
            {
                "wallet_id": wallet.wallet_id,
                "new_balance": str(wallet.balance),
            },
        )


# ──────────────────────────────────────────────
#  SEND NOTIFICATIONS
# ──────────────────────────────────────────────

class AdminSendNotificationView(APIView):
    permission_classes = [IsSuperuser]

    def post(self, request):
        serializer = SendNotificationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return success_response(
            "Notifications sent successfully.",
            result,
        )
