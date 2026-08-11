from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_verification_code(user_email, code):
    subject = "Your verification code!"
    
    html_content = render_to_string('emails/verification_code.html', {'code': code})
    
    text_content = strip_tags(html_content) 

    msg = EmailMultiAlternatives(subject, text_content, None, [user_email])
    
    msg.attach_alternative(html_content, "text/html")
    msg.send()
    
def send_password_reset_link(user_email, link):
    subject = "Your password reset link!"
    
    html_content = render_to_string('emails/password_reset.html', {'link': link})
    
    text_content = strip_tags(html_content) 

    msg = EmailMultiAlternatives(subject, text_content, None, [user_email])
    
    msg.attach_alternative(html_content, "text/html")
    msg.send()
    
def send_notification(user_email, message, data=None):
    subject = message
    
    html_content = render_to_string('emails/notification.html', {'data': data})
    
    text_content = strip_tags(html_content) 

    msg = EmailMultiAlternatives(subject, text_content, None, [user_email])
    
    msg.attach_alternative(html_content, "text/html")
    msg.send()