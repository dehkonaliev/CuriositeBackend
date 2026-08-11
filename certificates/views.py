from django.shortcuts import render
from .models import Certificate
from rest_framework.permissions import AllowAny
from baseapp.permissions import IsStudentAndOwner
from baseapp.utils import success_response, error_response
from rest_framework.views import APIView
from .serializers import CertificateSerializer


class MyCertificatesAPIView(APIView):
    permission_classes = [IsStudentAndOwner]
    def get(self, request):
        certificates = Certificate.objects.filter(student=request.user)
        serializer = CertificateSerializer(certificates, many=True)
        
        return success_response(message="Your certificates", data=serializer.data)
    
    
class GetCertificateAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, pk):
        certificate = Certificate.objects.filter(pk=pk).first()
        serializer = CertificateSerializer(certificate)
        
        return success_response(message="Student certificate", data=serializer.data)
    
        