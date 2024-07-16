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

@register.filter(name='split_at_second_comma')
def split_at_second_comma(value):
    """Returns the part of the string up to the second comma."""
    if isinstance(value, str):
        parts = value.split(',')
        if len(parts) > 2:
            return ','.join(parts[:2])
        else:
            return value  # If there are less than 2 commas, return the original string
    elif isinstance(value, datetime):
        # Convert datetime to string and then split
        date_str = value.strftime('%B %d, %Y, %H:%M:%S')
        parts = date_str.split(',')
        if len(parts) > 2:
            return ','.join(parts[:2])
        else:
            return date_str  # If there are less than 2 commas, return the formatted date string
    return value
