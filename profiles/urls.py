from django.urls import path
from .views import (StudentProfileAPIView, InstructorProfileAPIView, GetInstructorProfileAPIView, GetStudentProfileAPIView,
    SendFriendRequestAPIView, RejectFriendRequestAPIView, CancelFriendRequestAPIView, AcceptFriendRequestAPIView,
    GetMyRequestsAPIView, GetIncomingRequestsAPIView, FriendsAPIView
)

urlpatterns = [
    path('student-profile', StudentProfileAPIView.as_view()),
    path('instructor-profile', InstructorProfileAPIView.as_view()),
    path('get-instructor-profile/<uuid:pk>', GetInstructorProfileAPIView.as_view()),
    path('get-student-profile/<uuid:pk>', GetStudentProfileAPIView.as_view()),
    
    #Friend Request
    path('send-request', SendFriendRequestAPIView.as_view()),
    path('accept-request/<uuid:pk>', AcceptFriendRequestAPIView.as_view()),
    path('reject-request/<uuid:pk>', RejectFriendRequestAPIView.as_view()),
    path('cancel-request/<uuid:pk>', CancelFriendRequestAPIView.as_view()),
    
    #Requests View
    path('my-requests', GetMyRequestsAPIView.as_view()),
    path('incoming-requests', GetIncomingRequestsAPIView.as_view()),
    
    # Friends
    path('friends/<uuid:pk>', FriendsAPIView.as_view())
]