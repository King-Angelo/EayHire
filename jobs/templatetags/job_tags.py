from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name='has_attr')
def has_attr(user, attr):
    return hasattr(user, attr)

@register.filter
@stringfilter
def split_skills(value):
    """Split a string of skills into a list, handling various delimiters."""
    if not value:
        return []
    # Remove extra spaces and split by comma or space
    skills = [s.strip() for s in value.replace(',', ' ').split()]
    return [s for s in skills if s]  # Remove empty strings 