from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def before_colon(value):
    """Returns the part of the string before the first colon."""
    if not isinstance(value, str):
        return value
    return value.split(":")[0]
