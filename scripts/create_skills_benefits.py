import os
import django
import json
from django.core.exceptions import ValidationError
from django.db import transaction
from myapp.models import Skill, Benefit

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

# List of common skills
skills = [
    'Python', 'JavaScript', 'Java', 'C++', 'SQL',
    'Project Management', 'Agile', 'Scrum',
    'Communication', 'Leadership', 'Problem Solving',
    'Microsoft Office', 'Excel', 'Word', 'PowerPoint',
    'Customer Service', 'Sales', 'Marketing',
    'Data Analysis', 'Machine Learning', 'AI',
    'Web Development', 'Mobile Development',
    'UI/UX Design', 'Graphic Design',
    'Network Administration', 'System Administration',
    'Cloud Computing', 'AWS', 'Azure',
    'DevOps', 'CI/CD', 'Docker', 'Kubernetes',
    'Cybersecurity', 'Information Security',
    'Business Analysis', 'Financial Analysis',
    'Teaching', 'Training', 'Mentoring',
    'Research', 'Analytics', 'Statistics'
]

# List of common benefits
benefits = [
    'Health Insurance',
    'Dental Insurance',
    'Vision Insurance',
    'Life Insurance',
    '401(k)',
    'Paid Time Off',
    'Sick Leave',
    'Parental Leave',
    'Flexible Hours',
    'Remote Work',
    'Professional Development',
    'Training & Education',
    'Gym Membership',
    'Employee Discounts',
    'Stock Options',
    'Annual Bonus',
    'Performance Bonus',
    'Relocation Assistance',
    'Commuting Benefits',
    'Work-Life Balance'
]

# Create skills
for skill_name in skills:
    Skill.objects.get_or_create(name=skill_name)
    print(f"Created skill: {skill_name}")

# Create benefits
for benefit_name in benefits:
    Benefit.objects.get_or_create(name=benefit_name)
    print(f"Created benefit: {benefit_name}")

print("\nAll skills and benefits have been created successfully!") 