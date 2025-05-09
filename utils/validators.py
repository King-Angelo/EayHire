from django.core.exceptions import ValidationError

def validate_file_size(file):
    max_size = 5242880  # 5MB
    if file.size > max_size:
        raise ValidationError('File size must be under 5MB')

def validate_file_type(file):
    allowed_types = ['application/pdf', 'application/msword', 
                     'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    if file.content_type not in allowed_types:
        raise ValidationError('Invalid file type') 