from django.urls import path, include
from . import views

urlpatterns = [

    path('company/<company_name>/sylectus', views.company_sylectus, name='company_sylectus'),
    path('company/<company_name>/emails', views.company_emails, name='company_emails'),
    path('company/<company_name>', views.main, name='company_without_department'),
    path('settings', views.settings, name='settings'),
    path('test/', views.test,),
    path('', views.main, ),
]