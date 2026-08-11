from django.urls import path
from .views import GetCertificateAPIView, MyCertificatesAPIView

urlpatterns = [
    path('my-certificates', MyCertificatesAPIView.as_view()),
    path('student-certificate/<uuid:pk>', GetCertificateAPIView.as_view())
]