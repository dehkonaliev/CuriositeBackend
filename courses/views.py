from django.shortcuts import render
from rest_framework.views import APIView
from .models import Category, Course, Lesson, Module, Tag
from django.db.models import Count
from django.utils import timezone
from enrollments.models import Enrollment, LessonProgress
from authentication.models import CustomUser
from quizzes.models import QuizAttempt, Quiz
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Q, F
from certificates.services import generate_certificate
from profiles.models import StudentProfile
from baseapp.utils import success_response, error_response
from baseapp.pagination import CoursePagination
from .serializers import (CourseCreateUpdateSerializer, CategoryGetCreateSerializer, TagSerializer,
    ModuleCreateUpdateSerializer, LessonCreateUpdateSerializer, CourseDetailSerializer, ModuleDetailSerializer,
    LessonDetailSerializer, CourseInfoSerializer
)
from baseapp.permissions import (IsInstructorOrAdmin, IsAdminOrReadOnly, IsInstructorAndOwner,
    IsAdminOrOwnerOrReadOnlyPublished, IsStudentAndOwner
)


class CourseCreateAPIView(APIView):
    permission_classes = [IsInstructorAndOwner]
    def post(self, request):
        serializer = CourseCreateUpdateSerializer(data=request.data, context={"request":request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Course created", data=serializer.data, status_code=201)
   
    
class CourseUpDelAPIView(APIView):
    permission_classes = [IsInstructorAndOwner]

    def patch(self, request, pk):
        course = Course.objects.filter(pk=pk).first()
        if not course:
            return error_response(message="Course not found", status_code=404)

        self.check_object_permissions(request, course)

        serializer = CourseCreateUpdateSerializer(
            instance=course,
            data=request.data,
            context={"request": request},
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return success_response(message="Course updated", data=serializer.data, status_code=200)
    
    def delete(self, request, pk):
        course = Course.objects.filter(pk=pk).first()
        if not course:
            return error_response(message="Course not found", status_code=404)

        self.check_object_permissions(request, course)
        
        course.delete()
        
        return success_response(message="Course deleted")


class CourseDetailAPIView(APIView):
    permission_classes = [IsAdminOrOwnerOrReadOnlyPublished]
    def get(self, request, pk):
        course = Course.objects.filter(pk=pk).first()
        
        if not course:
            return error_response(message="Course not found", status_code=404)
        if not request.user.is_authenticated and course.status != Course.Status.PUBLISHED:
            return error_response(message="Course not found", status_code=404)
        
        self.check_object_permissions(request, course)
        
        serializer = CourseDetailSerializer(course, context={'request':request})
        return success_response(message="Course detail", data=serializer.data)


class ModuleCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsInstructorAndOwner]
    def post(self, request):
        user = request.user
        serializer = ModuleCreateUpdateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Module created", status_code=201, data=serializer.data)


class ModuleUpdateDeleteAPIView(APIView):
    permission_classes = [IsInstructorAndOwner]
    
    def patch(self, request, pk):
        module = Module.objects.filter(pk=pk).first()
        if not module:
            return error_response(message="Module not found", status_code=404)
        
        self.check_object_permissions(request, module.course)
        
        serializer = ModuleCreateUpdateSerializer(instance=module, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Module updated", data=serializer.data)
    
    def delete(self, request, pk):
        module = Module.objects.filter(pk=pk).first()
        if not module:
            return error_response(message="Module not found", status_code=404)
        
        self.check_object_permissions(request, module.course)
        
        module.delete()
        
        return success_response(message="Module deleted")


class ModuleDetailAPIView(APIView):
    permission_classes = [IsAdminOrOwnerOrReadOnlyPublished]
    def get(self, request, pk):
        module = Module.objects.filter(pk=pk).first()
        if not module:
            return error_response(message="Module not found", status_code=404)
        if not request.user.is_authenticated and module.course.status != Course.Status.PUBLISHED:
            return error_response(message="Module not found", status_code=404)
        
        self.check_object_permissions(request, module.course)
        
        serializer = ModuleDetailSerializer(module)
        return success_response(message="Module detail", data=serializer.data)


class LessonCreateAPIView(APIView):
    permission_classes = [IsInstructorAndOwner]
    def post(self, request):
        serializer = LessonCreateUpdateSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Lesson created", data=serializer.data, status_code=201)
          
           
class LessonUpDelAPIView(APIView):
    permission_classes = [IsInstructorAndOwner]
    def patch(self, request, pk):
        lesson = Lesson.objects.filter(pk=pk).first()
        if not lesson:
            return error_response(message="Lesson not found", status_code=404)
        serialier = LessonCreateUpdateSerializer(instance=lesson, data=request.data, partial=True, context={'request': request})
        serialier.is_valid(raise_exception=True)
        serialier.save()
        
        return success_response(message="Lesson updated", data=serialier.data)
    
    def delete(self, request, pk):
        lesson = Lesson.objects.filter(pk=pk).first()
        if not lesson:
            return error_response(message="Lesson not found", status_code=404)
        
        self.check_object_permissions(request, lesson.module.course)
        lesson.delete()
        
        return success_response(message="Lesson deleted")
       
       
class LessonDetailAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrOwnerOrReadOnlyPublished]
    def get(self, request, pk):
        user = request.user
        lesson = Lesson.objects.filter(pk=pk).first()
        if not lesson:
            return error_response(message="Lesson not found", status_code=404)
        
        is_owner = request.user.is_authenticated and request.user == lesson.module.course.instructor
        if lesson.module.course.status != Course.Status.PUBLISHED and not is_owner:
            return error_response(message="Lesson not found", status_code=404)
        
        self.check_object_permissions(request, lesson.module.course)
        enrollment = user.enrollments.filter(course=lesson.module.course, has_access=True).first()
        if user.user_role == "STUDENT" and not enrollment and not lesson.is_preview:
            return error_response(message="You have no active enrollment for this courses")
        
        if enrollment:
            enrollment.last_accessed_lesson = lesson
            enrollment.last_accessed_at = timezone.now()
            enrollment.save(update_fields=['last_accessed_lesson', 'last_accessed_at'])
        
        serializer = LessonDetailSerializer(lesson, context={'request': request})
        return success_response(message="Lesson detail", data=serializer.data)


class FilteredCoursesAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        
        search = request.query_params.get('search')
        instructor = request.query_params.get('instructor')
        category = request.query_params.get('category')
        tag = request.query_params.get('tag')
        level = request.query_params.get('level')
        language = request.query_params.get('language')
        pricing_type = request.query_params.get('pricing_type')
        rating = request.query_params.get('rating')
        
        courses = Course.objects.filter(status=Course.Status.PUBLISHED)
        
        if search:
            courses = courses.filter(
                Q(title__icontains=search) |
                Q(subtitle__icontains=search) |
                Q(what_included__icontains=search)
            )
        
        if instructor:
            courses = courses.filter(instructor=instructor)
        if category:
            courses = courses.filter(category=category)
        if tag:
            courses = courses.filter(tags__name=tag)
        if level:
            courses = courses.filter(level=level)
        if language:
            courses = courses.filter(language=language)
        if pricing_type:
            courses = courses.filter(pricing_type=pricing_type)
        if rating:
            try:
                rating_value = float(rating)
                courses = courses.filter(average_rating__gte=rating_value)
            except:
                return error_response(message="Rating must a number")
            
        paginator = CoursePagination()
        page = paginator.paginate_queryset(courses, request)
        serializer = CourseInfoSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    
class FilteredCoursesInstructorAPIView(APIView):
    permission_classes = [IsInstructorAndOwner]
    pagination_class = CoursePagination
    def get(self, request):
        
        search = request.query_params.get('search')
        instructor = request.query_params.get('instructor')
        category = request.query_params.get('category')
        tag = request.query_params.get('tag')
        level = request.query_params.get('level')
        language = request.query_params.get('language')
        pricing_type = request.query_params.get('pricing_type')
        rating = request.query_params.get('rating')
        
        # The instructor's OWN courses across ALL statuses (draft, in review,
        # rejected, published, archived) so they can manage their whole catalog.
        courses = Course.objects.filter(instructor=request.user)
        
        if search:
            courses = courses.filter(
                Q(title__icontains=search) |
                Q(subtitle__icontains=search) |
                Q(what_included__icontains=search)
            )
        
        if instructor:
            courses = courses.filter(instructor=instructor)
        if category:
            courses = courses.filter(category=category)
        if tag:
            courses = courses.filter(tags__name__icontains=tag)
        if level:
            courses = courses.filter(level=level)
        if language:
            courses = courses.filter(language=language)
        if pricing_type:
            courses = courses.filter(pricing_type=pricing_type)
        if rating:
            try:
                rating_value = float(rating)
                courses = courses.filter(average_rating__gte=rating_value)
            except:
                return error_response(message="Rating must a number")
            
        courses = courses.distinct()
        pagination = CoursePagination()
        page = pagination.paginate_queryset(courses, request)
        serializer = CourseInfoSerializer(page, many=True)
        
        return success_response(message="Filtered instructor courses", data=serializer.data)
    

class GetMyFeedAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        if not request.user.is_authenticated:
            courses = Course.objects.filter(status="PUBLISHED").order_by('-created_at')[:20]
            serializer = CourseInfoSerializer(courses, many=True)
            return success_response(message="My feed", data=serializer.data)

        interests = request.user.interests
        tag_ids = interests.values_list('tag', flat=True)
        enrolled_course_ids = Enrollment.objects.filter(student=request.user).values_list('course', flat=True)

        matched_courses = list(
            Course.objects.filter(tags__id__in=tag_ids, status="PUBLISHED")
            .exclude(id__in=enrolled_course_ids)
            .annotate(match_count=Count('tags', filter=Q(tags__id__in=tag_ids), distinct=True))
            .order_by('-match_count')
            .distinct()[:20]
        )

        if len(matched_courses) < 20:
            remaining = 20 - len(matched_courses)
            matched_ids = [c.id for c in matched_courses]

            fallback_courses = Course.objects.filter(status="PUBLISHED") \
                .exclude(id__in=enrolled_course_ids) \
                .exclude(id__in=matched_ids) \
                .order_by('-created_at')[:remaining]

            matched_courses += list(fallback_courses)

        serializer = CourseInfoSerializer(matched_courses, many=True)
        
        return success_response(message="My feed", data=serializer.data)
     
  
class CategoryAPIView(APIView):
    permission_classes = [IsAdminOrReadOnly]
    def post(self, request):
        serializer = CategoryGetCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Category created", data=serializer.data, status_code=201)
    
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategoryGetCreateSerializer(categories, many=True)
        
        return success_response(message="Category list", data=serializer.data)
    
  
class TagAPIView(APIView):
    permission_classes = [IsAdminOrReadOnly]
    def post(self, request):
        serializer = TagSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Tag created", data=serializer.data, status_code=201)
    
    def get(self, request):
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        
        return success_response(message="Tag list", data=serializer.data)


class InstructorsAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        instructors = CustomUser.objects.filter(
            user_role=CustomUser.UserRole.INSTRUCTOR,
            courses__status=Course.Status.PUBLISHED,
        ).distinct()

        data = [
            {
                'id': instructor.pk,
                'full_name': f"{instructor.first_name} {instructor.last_name}".strip()
                    or (instructor.email or "Instructor"),
                'photo': instructor.photo.url if instructor.photo else None,
            }
            for instructor in instructors
        ]

        return success_response(message="Instructors", data=data)
    
    
class SendToReview(APIView):
    permission_classes = [IsInstructorAndOwner]
    def patch(self, request, pk):
        course = Course.objects.filter(pk=pk).first()
        if not course:
            return error_response(message="Course not found", status_code=404)
        if course.status not in ['DRAFT', 'REJECTED']:
            return error_response(message="To send review your course status must be Draft or Rejected!")
        self.check_object_permissions(request, course)
        lesson = Lesson.objects.filter(module__course=course, lesson_type=Lesson.LessonType.ASSIGNMENT).first()
        if not lesson:
            return error_response(message="You have no assignment lesson yet", status_code=403)
        if not Quiz.objects.filter(lesson=lesson).exists():
            return error_response(message="You have no quiz belong to your assignment lesson!")
        course.status = "IN_REVIEW"
        course.save()
        serializer = CourseInfoSerializer(course)
        
        return success_response(message="Course sent to review!", data=serializer.data)
 
 
class CompleteCourseAPIView(APIView):
    permission_classes = [IsStudentAndOwner]
    def patch(self, request, pk):
        enrollment = Enrollment.objects.filter(course__pk=pk, student=request.user).first()
        if not enrollment:
            return error_response(message="Enrollment not found!", status_code=404)
        if enrollment.progress_percentage != 100:
            return error_response(message="You cannnot complete the course. First finish all lessons!", status_code=403)
        if not QuizAttempt.objects.filter(quiz__lesson__module__course=enrollment.course, quiz__lesson__lesson_type="ASSIGNMENT", student=request.user, score__gt=67).exists():
            return error_response(message="You do not have assignment with grade more than 67%", status_code=403)
        if enrollment.status == "COMPLETED":
            return error_response(message="Course already completed", status_code=403)
        StudentProfile.objects.filter(student=request.user).update(total_courses_completed=F('total_courses_completed') + 1, total_certificates_earned=F('total_certificates_earned') + 1)
        
        enrollment.status = "COMPLETED"
        enrollment.save(update_fields=['status'])
        generate_certificate(enrollment=enrollment)
        return success_response(message="Congratulations, Course completed!")