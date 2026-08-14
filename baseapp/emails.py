import resend
from core.settings import RESEND_API_KEY
from django.template.loader import render_to_string
from jinja2 import Template

resend.api_key = RESEND_API_KEY


def send_verification_code(user_email, code):
    html_content = render_to_string("emails/verification_code.html", {
        "user_email": user_email,
        "code": code,
    })

    params: resend.Emails.SendParams = {
        "from": "Curiosite <noreply@curiosite.uz>",
        "to": [user_email],
        "subject": "Verification code",
        "html": html_content
    }

    email = resend.Emails.send(params)
    print(email)
    
def send_password_reset_link(user_email, link):
    params: resend.Emails.SendParams = {
    "from": "Curiosite",
    "to": [user_email],
    "subject": link,
    "html": "<p>it works!</p>"
    }

    email = resend.Emails.send(params)
    print(email)
    
    
def send_notification(user_email, message, data=None):
    params: resend.Emails.SendParams = {
    "from": "Curiosite",
    "to": [user_email],
    "subject": message,
    "html": "<p>it works!</p>"
    }

    email = resend.Emails.send(params)
    print(email)