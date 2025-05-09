from django import template

register = template.Library()

@register.simple_tag
def unread_notifications_count(user):
    if not user.is_authenticated:
        return 0
    return user.notifications.filter(is_read=False).count()

@register.simple_tag
def has_unread_notifications(user):
    if not user.is_authenticated:
        return False
    return user.notifications.filter(is_read=False).exists() 