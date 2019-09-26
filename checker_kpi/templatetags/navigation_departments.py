from django import template
from checker_kpi.models import Company

register = template.Library()
@register.inclusion_tag('navigation_departments.html')
def navigation_departments(company_name, department_selected=None,):
    return {
        'company': Company.objects.get(name=company_name),
        'navigation_departments': ['emails', 'sylectus'],
        'department_selected': department_selected,

    }