from rest_framework import serializers
from .models import Post, PostImage, PostComment, PostLike
from .sanitize import sanitize_html
from authentication.models import CustomUser
from baseapp.utils import field_error

class AuthorMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'thumbnail', 'user_role']
        
        
class PostImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ['id', 'image', 'post']
        read_only_fields = ['id']


class PostListSerializer(serializers.ModelSerializer):
    instructor = AuthorMiniSerializer()
    reading_time_minutes = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'cover_image', 'excerpt', 'instructor', 'reading_time_minutes',
            'published_at', 'views_count', 'status', 'is_liked', 'likes_count', 'comments_count'
        ]
        
    def get_is_liked(self, obj):
        user = self.context.get('user')
        if user.is_authenticated:
            return obj.likes.filter(user=user).exists()
        return False

class PostDetailSerializer(serializers.ModelSerializer):
    instructor = AuthorMiniSerializer()
    reading_time_minutes = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    liked_by = serializers.SerializerMethodField()
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'cover_image', 'excerpt', 'instructor', 'reading_time_minutes',
            'published_at', 'views_count', 'status', 'body', 'is_liked', 'likes_count', 'comments_count', 'liked_by'
        ]
        read_only_fields = ['id', 'slug']
        
    def get_is_liked(self, obj):
        user = self.context.get('user')
        if user.is_authenticated:
            return obj.likes.filter(user=user).exists()
        return False
    
    def get_liked_by(self, obj):
        last_like = obj.likes.select_related('user').order_by('-created_at').first()
        if last_like:
            return AuthorMiniSerializer(last_like.user).data
        return None
        

class PostCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'cover_image', 'excerpt', 'status', 'body'
        ]
        read_only_fields = ['id']
        
    def validate_body(self, body):
        return sanitize_html(body)
    
    def create(self, validated_data):
        validated_data['instructor'] = self.context.get('instructor')
        return super().create(validated_data)
    

class CommentCreateUpdateSerializer(serializers.ModelSerializer):
    user = AuthorMiniSerializer(read_only=True)
    created_at = serializers.ReadOnlyField()
    class Meta:
        model = PostComment
        fields = ['id', 'comment', 'user', 'created_at']
        read_only_fields = ['id']
        
    def validate_comment(self, comment):
        comment = comment.strip()
        if len(comment) > 2000:
            return field_error("comment", "Comment cannot exceed from 2000 charaters")
        if len(comment) < 2:
            return field_error("comment", "Comment must be at least 2 characters long")
        return comment
    
    def create(self, validated_data):
        validated_data['user'] = self.context.get('user')
        validated_data['post'] = self.context.get('post')
        return super().create(validated_data)
    
    
class LikeInPostSerializer(serializers.ModelSerializer):
    user = AuthorMiniSerializer()
    class Meta:
        model = PostLike
        fields = ['id', 'user']
        
        
class PostMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'excerpt']
        
class LikeInUserSerializer(serializers.ModelSerializer):
    post = PostMiniSerializer()
    class Meta:
        model = PostLike
        fields = ['id', 'post']
        
class CommentsInPostSerializer(serializers.ModelSerializer):
    user = AuthorMiniSerializer()
    class Meta:
        model = PostComment
        fields = ['id', 'user', 'comment', 'created_at']
        
class CommentsInUserSerializer(serializers.ModelSerializer):
    post = PostMiniSerializer()
    class Meta:
        model = PostComment
        fields = ['id', 'post', 'comment', 'created_at']
        
        
    