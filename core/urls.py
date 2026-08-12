"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
import os
from django.http import JsonResponse


def _media_debug(request):
    files = []
    for root, _dirs, names in os.walk(settings.MEDIA_ROOT):
        for n in names:
            files.append(os.path.relpath(os.path.join(root, n), settings.MEDIA_ROOT))
    return JsonResponse({
        "MEDIA_ROOT": str(settings.MEDIA_ROOT),
        "total_files": len(files),
        "files": sorted(files)[:50],
        "78806700_exists": os.path.exists(os.path.join(settings.MEDIA_ROOT, "users", "78806700.jpg")),
    })

urlpatterns = [
    path('admin/', admin.site.urls),
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
    path('__media_debug__', _media_debug),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

