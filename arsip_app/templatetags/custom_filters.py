from django import template

register = template.Library()

@register.filter
def get_display_jenis(value):
    if isinstance(value, str):
        return value.replace('_', ' ').title()
    return value
