import resend
from django.template.loader import render_to_string
from core.settings import RESEND_API_KEY

resend.api_key = RESEND_API_KEY


def send_verification_code(user_email, code):
    html = render_to_string('emails/verification_code.html', {
        'user_email': user_email,
        'code': code,
    })

    params: resend.Emails.SendParams = {
    "from": "Curiosite <noreply@curiosite.uz>",
    "to": [user_email],
    "subject": "Verification code",
    "html": html
    }

    email = resend.Emails.send(params)


def send_password_reset_link(user_email, link):
    html = render_to_string('emails/password_reset.html', {
        'user_email': user_email,
        'link': link,
    })

    params: resend.Emails.SendParams = {
    "from": "Curiosite <noreply@curiosite.uz>",
    "to": [user_email],
    "subject": "Reset your password",
    "html": html
    }

    email = resend.Emails.send(params)


def send_notification(user_email, message, data=None):
    html = render_to_string('emails/notification.html', {
        'user_email': user_email,
        'message': message,
        'data': data,
    })

    params: resend.Emails.SendParams = {
    "from": "Curiosite <noreply@curiosite.uz>",
    "to": [user_email],
    "subject": message,
    "html": html
    }

    email = resend.Emails.send(params)
