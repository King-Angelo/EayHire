from django.db import migrations
from django.utils import timezone

def add_default_skills_and_benefits(apps, schema_editor):
    JobCategory = apps.get_model('myapp', 'JobCategory')
    Skill = apps.get_model('myapp', 'Skill')
    Benefit = apps.get_model('myapp', 'Benefit')
    
    # First, create the categories
    categories = {
        'Programming Languages': 'Programming and scripting languages',
        'Web Development': 'Web development technologies and frameworks',
        'Cloud & DevOps': 'Cloud computing and DevOps tools',
        'Data Science': 'Data science and analytics skills',
        'Project Management': 'Project management methodologies and tools',
        'Design': 'Design tools and methodologies',
        'Business Skills': 'Business and professional skills',
        'Soft Skills': 'Interpersonal and communication skills'
    }
    
    created_categories = {}
    for name, description in categories.items():
        category, _ = JobCategory.objects.get_or_create(
            name=name,
            defaults={'description': description}
        )
        created_categories[name] = category

    # Now create skills with proper category references
    skills_data = [
        # Programming Languages
        {'name': 'Python', 'description': 'Python programming language', 'category': created_categories['Programming Languages']},
        {'name': 'JavaScript', 'description': 'JavaScript programming language', 'category': created_categories['Programming Languages']},
        {'name': 'Java', 'description': 'Java programming language', 'category': created_categories['Programming Languages']},
        
        # Web Development
        {'name': 'React.js', 'description': 'React JavaScript library', 'category': created_categories['Web Development']},
        {'name': 'Django', 'description': 'Django web framework', 'category': created_categories['Web Development']},
        {'name': 'HTML5/CSS3', 'description': 'Web markup and styling', 'category': created_categories['Web Development']},
        
        # Cloud & DevOps
        {'name': 'AWS', 'description': 'Amazon Web Services', 'category': created_categories['Cloud & DevOps']},
        {'name': 'Docker', 'description': 'Containerization platform', 'category': created_categories['Cloud & DevOps']},
        {'name': 'Kubernetes', 'description': 'Container orchestration', 'category': created_categories['Cloud & DevOps']},
        
        # Data Science
        {'name': 'Machine Learning', 'description': 'Machine learning and AI', 'category': created_categories['Data Science']},
        {'name': 'SQL', 'description': 'Database querying language', 'category': created_categories['Data Science']},
        {'name': 'Data Analysis', 'description': 'Data analysis and visualization', 'category': created_categories['Data Science']},
        
        # Project Management
        {'name': 'Agile', 'description': 'Agile methodology', 'category': created_categories['Project Management']},
        {'name': 'Scrum', 'description': 'Scrum framework', 'category': created_categories['Project Management']},
        {'name': 'JIRA', 'description': 'Project management tool', 'category': created_categories['Project Management']},
        
        # Design
        {'name': 'UI/UX Design', 'description': 'User interface and experience design', 'category': created_categories['Design']},
        {'name': 'Figma', 'description': 'Design tool', 'category': created_categories['Design']},
        {'name': 'Adobe Creative Suite', 'description': 'Design software suite', 'category': created_categories['Design']},
        
        # Business Skills
        {'name': 'Business Analysis', 'description': 'Business analysis skills', 'category': created_categories['Business Skills']},
        {'name': 'Strategic Planning', 'description': 'Strategic planning and execution', 'category': created_categories['Business Skills']},
        {'name': 'Market Research', 'description': 'Market research and analysis', 'category': created_categories['Business Skills']},
        
        # Soft Skills
        {'name': 'Communication', 'description': 'Effective communication', 'category': created_categories['Soft Skills']},
        {'name': 'Leadership', 'description': 'Leadership skills', 'category': created_categories['Soft Skills']},
        {'name': 'Problem Solving', 'description': 'Problem-solving abilities', 'category': created_categories['Soft Skills']}
    ]

    current_time = timezone.now()
    for skill_data in skills_data:
        Skill.objects.get_or_create(
            name=skill_data['name'],
            defaults={
                'description': skill_data['description'],
                'category': skill_data['category'],
                'created_at': current_time,
                'updated_at': current_time
            }
        )

    # Create default benefits
    benefits_data = [
        # Healthcare
        {'name': 'Health Insurance', 'description': 'Comprehensive health insurance coverage'},
        {'name': 'Dental Coverage', 'description': 'Dental insurance coverage'},
        {'name': 'Vision Coverage', 'description': 'Vision insurance coverage'},
        
        # Leave Benefits
        {'name': 'Paid Time Off', 'description': 'Paid vacation and personal days'},
        {'name': 'Sick Leave', 'description': 'Paid sick leave'},
        {'name': 'Parental Leave', 'description': 'Maternity and paternity leave'},
        
        # Work Arrangement
        {'name': 'Remote Work', 'description': 'Option to work remotely'},
        {'name': 'Flexible Hours', 'description': 'Flexible working hours'},
        {'name': 'Hybrid Work', 'description': 'Mix of remote and office work'},
        
        # Financial Benefits
        {'name': '401(k)', 'description': 'Retirement savings plan'},
        {'name': 'Performance Bonus', 'description': 'Performance-based bonuses'},
        {'name': 'Stock Options', 'description': 'Company stock options'},
        
        # Career Growth
        {'name': 'Professional Development', 'description': 'Professional development opportunities'},
        {'name': 'Training Programs', 'description': 'Training and skill development programs'},
        {'name': 'Career Advancement', 'description': 'Career advancement opportunities'},
        
        # Wellness
        {'name': 'Gym Membership', 'description': 'Gym membership or fitness allowance'},
        {'name': 'Mental Health Support', 'description': 'Mental health resources and support'},
        {'name': 'Wellness Programs', 'description': 'Wellness and health programs'}
    ]

    for benefit_data in benefits_data:
        Benefit.objects.get_or_create(
            name=benefit_data['name'],
            defaults={
                'description': benefit_data['description'],
                'created_at': current_time,
                'updated_at': current_time
            }
        )

class Migration(migrations.Migration):
    dependencies = [
        ('myapp', '0010_merge_20250420_2129'),
    ]

    operations = [
        migrations.RunPython(add_default_skills_and_benefits),
    ] 