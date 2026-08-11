from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from xhtml2pdf import pisa
from django.db.models import Avg
import io
from decimal import Decimal
from baseapp.utils import error_response
from enrollments.models import Enrollment
from .models import Certificate


def generate_certificate(enrollment: Enrollment) -> Certificate:
    student = enrollment.student
    course = enrollment.course
    attempts = student.quiz_attempts.filter(quiz__lesson__module__course=course)
    total_score = Decimal(attempts.aggregate(avg=Avg('score'))['avg'])
    assignment_score = attempts.filter(quiz__lesson__lesson_type="ASSIGNMENT").first().score
    
    certificate, created = Certificate.objects.get_or_create(
        student=student,
        course_title=course.title,
        defaults={"enrollment": enrollment},
        assignment_score=assignment_score,
        total_score=total_score
    )

    if not created and certificate.pdf_file:
        # already generated, don't regenerate
        return certificate

    html_string = render_to_string("certificates/certificate.html", {
        "student_name": student.get_full_name() or student.username,
        "course_title": course.title,
        "issued_at": certificate.created_at,
        "total_score": total_score,
        "assignment_score": assignment_score,
        "certificate_id": certificate.id,
    })

    buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html_string, dest=buffer)

    if pisa_status.err:
        return error_response(message=f"Failed to generate certificate PDF for enrollment {enrollment.pk}")

    buffer.seek(0)
    certificate.pdf_file.save(
        f"certificate_{certificate.id}.pdf",
        ContentFile(buffer.getvalue()),
        save=True,
    )

    return certificate