from django.core.management.base import BaseCommand
from utils.test_email import test_email_configuration

class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def handle(self, *args, **options):
        self.stdout.write('Testing email configuration...')
        if test_email_configuration():
            self.stdout.write(self.style.SUCCESS('Email configuration test successful!'))
        else:
            self.stdout.write(self.style.ERROR('Email configuration test failed!')) 