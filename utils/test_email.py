from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext as _

def test_email_configuration():
    """Test the email configuration by sending a test email"""
    try:
        subject = _('Test Email - Django Social Login')
        html_message = render_to_string('email/test_email.html', {
            'message': 'This is a test email to verify your email configuration.'
        })
        
        send_mail(
            subject=subject,
            message='',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],
            html_message=html_message,
        )
        print("✅ Test email sent successfully!")
        return True
    except Exception as e:
        print("❌ Error sending test email:")
        print(f"Error details: {str(e)}")
        return False

if __name__ == '__main__':
    test_email_configuration() 