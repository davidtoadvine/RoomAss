from django import template
from datetime import datetime

register = template.Library()

@register.filter(name='split_at_comma')
def split_at_comma(value):
    """Returns the part of the string up to the first comma."""
    if isinstance(value, str):
        return value.split(',')[0]
    elif isinstance(value, datetime):
        # Convert datetime to string and then split
        return value.strftime('%B %d, %Y').split(',')[0]
    return value