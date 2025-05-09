from django.db import migrations

def add_default_categories(apps, schema_editor):
    JobCategory = apps.get_model('myapp', 'JobCategory')
    categories = [
        {'name': 'Information Technology', 'description': 'Software development, IT infrastructure, cybersecurity, and other tech roles'},
        {'name': 'Healthcare', 'description': 'Medical, nursing, healthcare administration, and related positions'},
        {'name': 'Finance', 'description': 'Banking, accounting, financial analysis, and investment roles'},
        {'name': 'Education', 'description': 'Teaching, training, and educational administration positions'},
        {'name': 'Sales & Marketing', 'description': 'Sales, marketing, advertising, and public relations roles'},
        {'name': 'Engineering', 'description': 'Various engineering disciplines and technical roles'},
        {'name': 'Administrative', 'description': 'Office administration, clerical, and support positions'},
        {'name': 'Customer Service', 'description': 'Customer support, service, and experience roles'},
        {'name': 'Human Resources', 'description': 'HR management, recruitment, and personnel administration'},
        {'name': 'Manufacturing', 'description': 'Production, assembly, and manufacturing roles'},
        {'name': 'Creative & Design', 'description': 'Graphic design, UX/UI, content creation, and artistic roles'},
        {'name': 'Legal', 'description': 'Legal services, compliance, and regulatory positions'},
        {'name': 'Hospitality', 'description': 'Hotels, restaurants, tourism, and service industry roles'},
        {'name': 'Construction', 'description': 'Building, construction, and skilled trades positions'},
        {'name': 'Transportation', 'description': 'Logistics, shipping, and transportation roles'},
    ]
    
    for category in categories:
        JobCategory.objects.create(**category)

def remove_default_categories(apps, schema_editor):
    JobCategory = apps.get_model('myapp', 'JobCategory')
    JobCategory.objects.all().delete()

class Migration(migrations.Migration):
    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_default_categories, remove_default_categories),
    ] 