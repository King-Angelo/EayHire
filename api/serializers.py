from rest_framework import serializers
from django.contrib.auth import get_user_model
from myapp.models import (
    JobCategory, Skill, Benefit, Company, JobPosting, JobMetrics,
    JobSeeker, Employer, JobApplication, SavedJob, JobAlert, Notification,
    JobMatch, SavedSearch, ApplicationHistory
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class JobCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCategory
        fields = '__all__'

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'

class BenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Benefit
        fields = '__all__'

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class JobPostingSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company',
        write_only=True
    )
    category = JobCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=JobCategory.objects.all(),
        source='category',
        write_only=True
    )
    required_skills = SkillSerializer(many=True, read_only=True)
    required_skills_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        source='required_skills',
        many=True,
        write_only=True
    )
    preferred_skills = SkillSerializer(many=True, read_only=True)
    preferred_skills_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        source='preferred_skills',
        many=True,
        write_only=True
    )
    benefits = BenefitSerializer(many=True, read_only=True)
    benefits_ids = serializers.PrimaryKeyRelatedField(
        queryset=Benefit.objects.all(),
        source='benefits',
        many=True,
        write_only=True
    )

    class Meta:
        model = JobPosting
        fields = '__all__'

class JobMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobMetrics
        fields = '__all__'

class JobSeekerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    skills_ids = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        source='skills',
        many=True,
        write_only=True
    )

    class Meta:
        model = JobSeeker
        fields = '__all__'

class EmployerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    company = CompanySerializer(read_only=True)
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company',
        write_only=True
    )

    class Meta:
        model = Employer
        fields = '__all__'

class JobApplicationSerializer(serializers.ModelSerializer):
    job = JobPostingSerializer(read_only=True)
    job_id = serializers.PrimaryKeyRelatedField(
        queryset=JobPosting.objects.all(),
        source='job',
        write_only=True
    )
    applicant = JobSeekerSerializer(read_only=True)
    applicant_id = serializers.PrimaryKeyRelatedField(
        queryset=JobSeeker.objects.all(),
        source='applicant',
        write_only=True
    )

    class Meta:
        model = JobApplication
        fields = '__all__'

class SavedJobSerializer(serializers.ModelSerializer):
    job = JobPostingSerializer(read_only=True)
    job_id = serializers.PrimaryKeyRelatedField(
        queryset=JobPosting.objects.all(),
        source='job',
        write_only=True
    )
    job_seeker = JobSeekerSerializer(read_only=True)
    job_seeker_id = serializers.PrimaryKeyRelatedField(
        queryset=JobSeeker.objects.all(),
        source='job_seeker',
        write_only=True
    )

    class Meta:
        model = SavedJob
        fields = '__all__'

class JobAlertSerializer(serializers.ModelSerializer):
    job_seeker = JobSeekerSerializer(read_only=True)
    job_seeker_id = serializers.PrimaryKeyRelatedField(
        queryset=JobSeeker.objects.all(),
        source='job_seeker',
        write_only=True
    )
    category = JobCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=JobCategory.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = JobAlert
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )

    class Meta:
        model = Notification
        fields = '__all__'

class JobMatchSerializer(serializers.ModelSerializer):
    job = JobPostingSerializer(read_only=True)
    job_id = serializers.PrimaryKeyRelatedField(
        queryset=JobPosting.objects.all(),
        source='job',
        write_only=True
    )
    jobseeker = JobSeekerSerializer(read_only=True)
    jobseeker_id = serializers.PrimaryKeyRelatedField(
        queryset=JobSeeker.objects.all(),
        source='jobseeker',
        write_only=True
    )

    class Meta:
        model = JobMatch
        fields = '__all__'

class SavedSearchSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )

    class Meta:
        model = SavedSearch
        fields = '__all__'

class ApplicationHistorySerializer(serializers.ModelSerializer):
    application = JobApplicationSerializer(read_only=True)
    application_id = serializers.PrimaryKeyRelatedField(
        queryset=JobApplication.objects.all(),
        source='application',
        write_only=True
    )
    created_by = UserSerializer(read_only=True)
    created_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='created_by',
        write_only=True
    )

    class Meta:
        model = ApplicationHistory
        fields = '__all__'