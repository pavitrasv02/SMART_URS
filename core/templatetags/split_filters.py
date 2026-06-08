from django import template

register = template.Library()

@register.filter
def split_by(value, delimiter='||'):
    if value is None:
        return []
    return value.split(delimiter) 