from django.contrib import admin
from . import models
# Register your models here.


class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'corporate_id', 'login_name', 'login_pass')


class EmailsAdmin(admin.ModelAdmin):
    list_display = ('company', 'email', 'check_for_this_email', 'creds')


class OperationsUsersAdmin(admin.ModelAdmin):
    list_display = ('company', 'nick_name')


class SylectusUsersAdmin(admin.ModelAdmin):
    list_display = ('company', 'name')


admin.site.register(models.Company, CompanyAdmin)
admin.site.register(models.Emails, EmailsAdmin)
admin.site.register(models.OperationsUsers, OperationsUsersAdmin)
admin.site.register(models.SylectusUsers, SylectusUsersAdmin)
