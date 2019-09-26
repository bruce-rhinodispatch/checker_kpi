from django import template

register = template.Library()
@register.inclusion_tag('dummy.html')
def render_sample(**kwargs):
    dict_with_variables = {}
    for key in kwargs:
        dict_with_variables[key] = kwargs[key]
    return dict_with_variables
