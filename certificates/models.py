from django.db import models
from baseapp.models import BaseModel
from enrollments.models import Enrollment
import uuid


class Certificate(BaseModel):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, related_name="certificate")
    student = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE, related_name='my_certificates')
    course_title = models.CharField(max_length=300)
    total_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    assignment_score = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    pdf_file = models.FileField(upload_to="certificates/", blank=True, null=True)