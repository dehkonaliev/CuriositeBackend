from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),

    path('instructors/', views.AdminInstructorListView.as_view(), name='admin-instructors'),
    path('instructors/<uuid:pk>/', views.AdminInstructorDetailView.as_view(), name='admin-instructor-detail'),
    path('instructors/<uuid:pk>/approval/', views.AdminInstructorApprovalView.as_view(), name='admin-instructor-approval'),

    path('students/', views.AdminStudentListView.as_view(), name='admin-students'),
    path('students/<uuid:pk>/', views.AdminStudentDetailView.as_view(), name='admin-student-detail'),

    path('courses/', views.AdminCourseListView.as_view(), name='admin-courses'),
    path('courses/<uuid:pk>/', views.AdminCourseDetailView.as_view(), name='admin-course-detail'),
    path('courses/<uuid:pk>/status/', views.AdminCourseStatusView.as_view(), name='admin-course-status'),

    path('lessons/<uuid:pk>/', views.AdminLessonDetailView.as_view(), name='admin-lesson-detail'),

    path('enrollments/', views.AdminEnrollmentListView.as_view(), name='admin-enrollments'),

    path('wallet-topup/', views.AdminWalletTopupView.as_view(), name='admin-wallet-topup'),

    path('notifications/send/', views.AdminSendNotificationView.as_view(), name='admin-send-notification'),
]
