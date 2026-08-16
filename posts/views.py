from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from .permissions import IsInstructor, IsOwnerOrReadOnly
from baseapp.permissions import IsOwner
from .serializers import (PostListSerializer, PostDetailSerializer, PostImageUploadSerializer, PostCreateUpdateSerializer,
    CommentCreateUpdateSerializer, LikeInPostSerializer, LikeInUserSerializer, CommentsInPostSerializer, CommentsInUserSerializer,
                           
)
from baseapp.utils import success_response, error_response
from .models import Post, PostImage, PostLike, PostComment
from baseapp.pagination import CoursePagination
from django.db.models import Q


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
    def get(self, request, pk):
        post = Post.objects.filter(pk=pk).first()
        if not post:
            return error_response(message="Post not found", status_code=404)
        
        serializer = PostDetailSerializer(post, context={'user':request.user})
        
        return success_response(message="Post detail", data=serializer.data)
    
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
            return success_response(message="Post unliked")
        return success_response(message="Post liked")
    
    def get(self, request, pk):
        post = Post.objects.filter(pk=pk, status="PUBLISHED").first()  
        if not post:
            return error_response(message="Post not found", status_code=404)
        
        likes = PostLike.objects.filter(post=post).order_by('-created_at')
        
        serializer = LikeInPostSerializer(likes, many=True)
        return success_response(message="Post likes", data=serializer.data)
        
        
class GetMyLikesAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        likes = PostLike.objects.filter(user=request.user).order_by('-created_at')
        seriazlizer = LikeInUserSerializer(likes, many=True)
        return success_response(message="My likes", data=seriazlizer.data)

class PostCommentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        post = Post.objects.filter(pk=pk, status="PUBLISHED").first()
        if not post:
            return error_response(message="Post not found", status_code=404)
        serializer = CommentCreateUpdateSerializer(data=request.data, context={'user': request.user, 'post': post})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message="Comment created", data=serializer.data, status_code=201)
    
    def get(self, request, pk):
        post = Post.objects.filter(pk=pk, status="PUBLISHED").first()
        if not post:
            return error_response(message="Post not found", status_code=404)
        comments = PostComment.objects.filter(post=post).order_by('-created_at')
        serializer = CommentsInPostSerializer(comments, many=True)
        
        return success_response(message="Post comments", data=serializer.data)
    
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
        
        return success_response(message="Comment deleted")

class MyCommentsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        comments = PostComment.objects.filter(user=request.user).order_by('-created_at')
        serializer = CommentsInUserSerializer(comments, many=True)
        
        return success_response(message="My comments", data=serializer.data)
    

    