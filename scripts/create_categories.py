import os
import django
import json
from django.core.exceptions import ValidationError
from django.db import transaction
from myapp.models import JobCategory

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

# List of common job categories
categories = [
    {
        'name': 'Information Technology',
        'description': 'Jobs in software development, IT support, and technology services'
    },
    {
        'name': 'Healthcare',
        'description': 'Jobs in medical, nursing, and healthcare services'
    },
    {
        'name': 'Finance',
        'description': 'Jobs in banking, accounting, and financial services'
    },
    {
        'name': 'Education',
        'description': 'Jobs in teaching, training, and educational services'
    },
    {
        'name': 'Sales & Marketing',
        'description': 'Jobs in sales, marketing, and customer service'
    },
    {
        'name': 'Engineering',
        'description': 'Jobs in various engineering fields'
    },
    {
        'name': 'Administrative',
        'description': 'Jobs in office administration and clerical work'
    },
    {
        'name': 'Manufacturing',
        'description': 'Jobs in production, manufacturing, and industrial work'
    },
    {
        'name': 'Retail',
        'description': 'Jobs in retail sales and store management'
    },
    {
        'name': 'Other',
        'description': 'Other job categories not listed above'
    }
]

# Create categories
for category in categories:
    JobCategory.objects.get_or_create(
        name=category['name'],
        defaults={'description': category['description']}
    )
    print(f"Created category: {category['name']}")

print("\nAll categories have been created successfully!") 