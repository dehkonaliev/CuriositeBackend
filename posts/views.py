from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import IsInstructor, IsOwnerOrReadOnly
from baseapp.permissions import IsOwner
from .serializers import (PostListSerializer, PostDetailSerializer, PostImageUploadSerializer, PostCreateUpdateSerializer,
    CommentCreateUpdateSerializer, LikeInPostSerializer, LikeInUserSerializer, CommentsInPostSerializer, CommentsInUserSerializer,
                           
)
from django.core.cache import cache
from baseapp.utils import success_response, error_response
from .models import Post, PostImage, PostLike, PostComment
from baseapp.pagination import CoursePagination, LikePagination, CommentPagination
from django.db.models import Q, F


class PostImageUploadAPIView(APIView):
    permission_classes = [IsInstructor]
    def post(self, request):
        serializer = PostImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Image uploaded!", data=serializer.data, status_code=201)
    

class PostCreateAPIView(APIView):
    permission_classes = [IsInstructor]
    def post(self, request):
        serializer = PostCreateUpdateSerializer(data=request.data, context={'instructor': request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Post created", data=serializer.data, status_code=201)
    
class PostUpdateDeleteAPIView(APIView):
    permission_classes = [IsInstructor, IsOwnerOrReadOnly]
    def patch(self, request, pk):
        post = Post.objects.filter(pk=pk).first()
        if not post:
            return error_response(message="Post not found", status_code=404)
        self.check_object_permissions(request, post)
        
        serializer = PostCreateUpdateSerializer(instance=post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Post updated")
    
    def delete(self, request, pk):
        post = Post.objects.filter(pk=pk).first()
        if not post:
            return error_response(message="Post not found", status_code=404)
        self.check_object_permissions(request, post)
        
        post.delete()
        
        return success_response(message="Post deleted")
    
    
class PostDetailAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, slug):
        post = Post.objects.filter(slug=slug).first()
        if not post:
            return error_response(message="Post not found", status_code=404)
        cache_key = f"post_view:{post.pk}:{self._viewer_key(request)}"
        if cache.add(cache_key, True, timeout=60 * 30):  # 30 min window
            Post.objects.filter(pk=post.pk).update(views_count=F('views_count') + 1)        
        
        serializer = PostDetailSerializer(post, context={'user':request.user})
        return success_response(message="Post detail", data=serializer.data)
    
    def _viewer_key(self, request):
        if request.user.is_authenticated:
            return f"user:{request.user.id}"
        return f"ip:{request.META.get('REMOTE_ADDR', 'unknown')}"
    
class FilteredPostsAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        search = request.query_params.get('search')
        
        posts = Post.objects.filter(Q(title__icontains=search) | Q(excerpt__icontains=search) | Q(body__icontains=search))
        
        paginator = CoursePagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = PostListSerializer(page, many=True, context={'user': request.user})
        return paginator.get_paginated_response(serializer.data)
    
    
class FeedPostsAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        posts = Post.objects.filter(status='PUBLISHED').order_by('-created_at')[:18]
        
        paginator = CoursePagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = PostListSerializer(page, many=True, context={'user': request.user})
        return paginator.get_paginated_response(serializer.data)
    
class InstructorPostsAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, pk):
        posts = Post.objects.filter(instructor__pk=pk).order_by('-created_at')
        
        paginator = CoursePagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = PostListSerializer(page, many=True, context={'user': request.user})
        return paginator.get_paginated_response(serializer.data)
    
            
class LikePostAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        post = Post.objects.filter(pk=pk, status="PUBLISHED").first()  
        if not post:
            return error_response(message="Post not found", status_code=404)
        like, created = PostLike.objects.get_or_create(user=request.user, post=post)
        if not created:
            like.delete()
            Post.objects.filter(pk=pk).update(likes_count=F('likes_count')-1)
            return success_response(message="Post unliked")
        Post.objects.filter(pk=pk).update(likes_count=F('likes_count')+1)
        return success_response(message="Post liked")
    
    def get(self, request, pk):
        post = Post.objects.filter(pk=pk, status="PUBLISHED").first()  
        if not post:
            return error_response(message="Post not found", status_code=404)
        
        likes = PostLike.objects.filter(post=post).order_by('-created_at')
        
        paginator = LikePagination()
        page = paginator.paginate_queryset(likes, request)
        serializer = LikeInPostSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
        
        
class GetMyLikesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        likes = PostLike.objects.filter(user=request.user).order_by('-created_at')
        paginator = LikePagination()
        
        page = paginator.paginate_queryset(likes, request)
        serializer = LikeInUserSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

class PostCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        post = Post.objects.filter(pk=pk, status="PUBLISHED").first()
        if not post:
            return error_response(message="Post not found", status_code=404)
        serializer = CommentCreateUpdateSerializer(data=request.data, context={'user': request.user, 'post': post})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        Post.objects.filter(pk=pk).update(comments_count=F('comments_count')+1)
        
        return success_response(message="Comment created", data=serializer.data, status_code=201)
    
    def get(self, request, pk):
        post = Post.objects.filter(pk=pk, status="PUBLISHED").first()
        if not post:
            return error_response(message="Post not found", status_code=404)
        comments = PostComment.objects.filter(post=post).order_by('-created_at')

        paginator = CommentPagination()
        page = paginator.paginate_queryset(comments, request)
        serializer = CommentsInPostSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
class CommentUpdateDeleteAPIView(APIView):
    permission_classes = [IsOwner]
    def patch(self, request, pk):
        comment = PostComment.objects.filter(pk=pk).first()
        if not comment:
            return error_response(message="Comment not found", status_code=404)
        self.check_object_permissions(request, comment)
        
        serializer = CommentCreateUpdateSerializer(instance=comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Comment updated", data=serializer.data)
        
    def delete(self, request, pk):
        comment = PostComment.objects.filter(pk=pk).first()
        if not comment:
            return error_response(message="Comment not found", status_code=404)
        self.check_object_permissions(request, comment)
        
        comment.delete()
        Post.objects.filter(pk=pk).update(comments_count=F('comments_count')-1)
        
        return success_response(message="Comment deleted")

class MyCommentsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        comments = PostComment.objects.filter(user=request.user).order_by('-created_at')

        paginator = CommentPagination()
        page = paginator.paginate_queryset(comments, request)
        serializer = CommentsInUserSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    

    