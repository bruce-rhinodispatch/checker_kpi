from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def if_none_set_0(value):
    if value == "":
        return "0"
    else:
        return value

