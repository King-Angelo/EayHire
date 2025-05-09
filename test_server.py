import os
import sys
import subprocess
import requests
from django.core.management import execute_from_command_line
from django.conf import settings
from django.db import connection
from django.core.management.commands import check

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("Checking dependencies...")
    try:
        import django
        import djangorestframework
        import django_filters
        import djangorestframework_simplejwt
        import django_allauth
        import django_crispy_forms
        import crispy_bootstrap5
        import Pillow
        import psycopg2
        import gunicorn
        import whitenoise
        import django_storages
        import boto3
        import django_cors_headers
        import drf_yasg
        import django_redis
        import redis
        import celery
        import django_celery_beat
        import django_celery_results
        print("✓ All dependencies are installed")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        sys.exit(1)

def check_database():
    """Check database connection and migrations"""
    print("\nChecking database...")
    try:
        # Check if database is accessible
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✓ Database connection successful")

        # Check for pending migrations
        from django.core.management.commands import makemigrations
        result = subprocess.run(
            ['python', 'manage.py', 'makemigrations', '--dry-run'],
            capture_output=True,
            text=True
        )
        if "No changes detected" not in result.stdout:
            print("✗ There are pending migrations. Run 'python manage.py makemigrations'")
            sys.exit(1)
        print("✓ No pending migrations")

        # Check if migrations have been applied
        result = subprocess.run(
            ['python', 'manage.py', 'showmigrations'],
            capture_output=True,
            text=True
        )
        if "[ ]" in result.stdout:
            print("✗ Some migrations are not applied. Run 'python manage.py migrate'")
            sys.exit(1)
        print("✓ All migrations are applied")

    except Exception as e:
        print(f"✗ Database error: {e}")
        sys.exit(1)

def check_settings():
    """Check Django settings configuration"""
    print("\nChecking settings...")
    try:
        # Check if settings are properly configured
        if not settings.SECRET_KEY:
            print("✗ SECRET_KEY is not set")
            sys.exit(1)
        print("✓ SECRET_KEY is configured")

        if settings.DEBUG:
            print("! DEBUG is True - not recommended for production")

        # Check if database is configured
        if not settings.DATABASES:
            print("✗ Database configuration is missing")
            sys.exit(1)
        print("✓ Database is configured")

        # Check if static files are configured
        if not settings.STATIC_ROOT:
            print("! STATIC_ROOT is not set")
        else:
            print("✓ STATIC_ROOT is configured")

        # Check if media files are configured
        if not settings.MEDIA_ROOT:
            print("! MEDIA_ROOT is not set")
        else:
            print("✓ MEDIA_ROOT is configured")

    except Exception as e:
        print(f"✗ Settings error: {e}")
        sys.exit(1)

def check_api_endpoints():
    """Check if API endpoints are accessible"""
    print("\nChecking API endpoints...")
    try:
        # Start the development server in a separate process
        server = subprocess.Popen(
            ['python', 'manage.py', 'runserver', '8000'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for server to start
        import time
        time.sleep(2)

        # Test API endpoints
        base_url = 'http://localhost:8000/api'
        endpoints = [
            '/token/',
            '/job-categories/',
            '/skills/',
            '/benefits/',
            '/companies/',
            '/job-postings/',
            '/job-metrics/',
            '/job-seekers/',
            '/employers/',
            '/applications/',
            '/saved-jobs/',
            '/job-alerts/',
            '/notifications/',
            '/job-matches/',
            '/saved-searches/',
            '/application-history/'
        ]

        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}")
                if response.status_code == 200:
                    print(f"✓ {endpoint} is accessible")
                else:
                    print(f"✗ {endpoint} returned status code {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"✗ {endpoint} error: {e}")

        # Stop the server
        server.terminate()
        server.wait()

    except Exception as e:
        print(f"✗ API testing error: {e}")
        sys.exit(1)

def check_celery():
    """Check if Celery is properly configured"""
    print("\nChecking Celery configuration...")
    try:
        from celery import Celery
        app = Celery('django_social_login_allauth')
        app.config_from_object('django.conf:settings', namespace='CELERY')
        app.autodiscover_tasks()
        print("✓ Celery is properly configured")
    except Exception as e:
        print(f"✗ Celery configuration error: {e}")
        sys.exit(1)

def main():
    """Run all checks"""
    print("Starting server health check...\n")
    
    check_dependencies()
    check_database()
    check_settings()
    check_api_endpoints()
    check_celery()
    
    print("\nAll checks completed successfully!")
    print("Server is ready to run. Start with: python manage.py runserver")

if __name__ == "__main__":
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_social_login_allauth.settings')
    main() 