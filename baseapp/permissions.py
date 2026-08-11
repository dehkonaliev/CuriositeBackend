from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsInstructorOrAdmin(BasePermission):
    # Only SUPERUSERs and INSTRUCTORs can see and change
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.user_role == 'INSTRUCTOR' or request.user.user_role == "SUPERUSER")
        )
        
    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user == obj.instructor or request.user.user_role == "SUPERUSER")
        )
        
class IsAdminOrReadOnly(BasePermission):
    # Only SUPERUSERs can change, but everybody can see
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True    
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.user_role == "SUPERUSER"
        )
        
class IsInstructorAndOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.user_role == "INSTRUCTOR"
        )
        
    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user == obj.instructor
        )
        
class IsStudentAndOwner(BasePermission):
    # Only STUDENTs can get in and see
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.user_role == 'STUDENT'
        )
        
    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user == obj.student
        )
    
        
class IsInstructorOrAdmin(BasePermission):
    # On INSTRUCTORs can get
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.user_role == 'INSTRUCTOR' or request.user.is_staff)
        )
        
    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user == obj.instructor or request.user.is_staff)
        )
        
class IsAdminOrOwnerOrReadOnlyPublished(BasePermission):
    def has_permission(self, request, view):
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS and obj.status == "PUBLISHED":
            return True

        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user == obj.instructor or request.user.is_superuser)
        )
        
        
class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(
            request.user.is_authenticated and
            request.user == obj.user
        )