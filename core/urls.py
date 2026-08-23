
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from django.views.static import serve
from django.urls import re_path

urlpatterns = [
    path('admin-secure-code4303/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/profile/', include('profiles.urls')),
    path('api/courses/', include('courses.urls')),
    path('api/enrollments/', include('enrollments.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/quizzes/', include('quizzes.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/certificates/', include('certificates.urls')),
    path('api/leaderboard/', include('leaders.urls')),
    path('api/posts/', include('posts.urls')),
    path('api/chat/', include('chat.urls')),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

