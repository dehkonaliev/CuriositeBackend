from django.contrib import admin
from .models import InstructorProfile, StudentProfile, FriendRequest, FriendShip

admin.site.register(StudentProfile)
admin.site.register(InstructorProfile)
admin.site.register(FriendShip)
admin.site.register(FriendRequest)
