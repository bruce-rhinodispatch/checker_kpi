from django import template
from checker_kpi.models import Company

register = template.Library()
@register.inclusion_tag('navigation_companies.html')
def navigation_companies(main_nav_element_selected=None):
    return {
        'main_nav_elements': Company.objects.all(),
        'main_nav_element_selected': main_nav_element_selected,

    }