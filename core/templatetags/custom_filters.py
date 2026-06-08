from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter(name='firstword')
def firstword(value):
    """Returns the first word of a string."""
    return value.split()[0] if value else ''

@register.filter
def split_by(value, delimiter='||'):
    if value is None:
        return []
    return value.split(delimiter)

@register.filter
def index(List, i):
    try:
        return List[int(i)]
    except:
        return '' 