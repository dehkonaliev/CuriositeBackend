from django.urls import path
from .views import (PostCreateAPIView, PostDetailAPIView, PostImageUploadAPIView, PostUpdateDeleteAPIView, FilteredPostsAPIView,
    InstructorPostsAPIView, FeedPostsAPIView, LikePostAPIView, PostCommentAPIView, CommentUpdateDeleteAPIView, GetMyLikesAPIView,
    MyCommentsAPIView, 
)

urlpatterns = [
    path('create-post', PostCreateAPIView.as_view()),
    path('post-detail/<slug:slug>', PostDetailAPIView.as_view()),
    path('post-image-upload', PostImageUploadAPIView.as_view()),
    path('post-update-delete/<uuid:pk>', PostUpdateDeleteAPIView.as_view()),
    path('filtered-posts', FilteredPostsAPIView.as_view()),
    path('feed-posts', FeedPostsAPIView.as_view()),
    path('instructor-posts/<uuid:pk>', InstructorPostsAPIView.as_view()),
    path('like-post/<uuid:pk>', LikePostAPIView.as_view()),
    path('comment-post/<uuid:pk>', PostCommentAPIView.as_view()),
    path('comment-update-delete/<uuid:pk>', CommentUpdateDeleteAPIView.as_view()),
    path('my-likes', GetMyLikesAPIView.as_view()),
    path('my-comments', MyCommentsAPIView.as_view()),
]