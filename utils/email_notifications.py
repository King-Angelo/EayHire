from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.utils.translation import gettext as _
import requests
import json

def get_location_from_ip(ip_address):
    """Get location information from IP address using ip-api.com"""
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}')
        data = response.json()
        if data['status'] == 'success':
            return f"{data['city']}, {data['country']}"
    except:
        pass
    return "Unknown location"

def send_2fa_setup_notification(user):
    """Send email notification when 2FA is set up"""
    subject = _('Two-Factor Authentication Setup Confirmation')
    html_message = render_to_string('email/2fa_setup_notification.html', {
        'user': user,
    })
    
    send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
    )

def send_2fa_login_notification(user, request):
    """Send email notification for new 2FA login"""
    subject = _('New Login with Two-Factor Authentication')
    
    # Get IP address and location
    ip_address = request.META.get('REMOTE_ADDR')
    location = get_location_from_ip(ip_address)
    
    html_message = render_to_string('email/2fa_login_notification.html', {
        'user': user,
        'login_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ip_address': ip_address,
        'location': location,
    })
    
    send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
    )

def send_2fa_backup_codes_notification(user, backup_codes):
    """Send email notification for new backup codes"""
    subject = _('New Two-Factor Authentication Backup Codes')
    
    html_message = render_to_string('email/2fa_backup_codes_notification.html', {
        'user': user,
        'backup_codes': backup_codes,
    })
    
    send_mail(
        subject=subject,
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
    ) 