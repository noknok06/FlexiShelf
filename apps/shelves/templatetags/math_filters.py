from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """value * arg を返す"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''
