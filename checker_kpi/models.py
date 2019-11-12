from django.db import models

# Create your models here.
from django.urls import reverse


class Company(models.Model):
    name = models.CharField(max_length=35, blank=False, unique=True)
    corporate_id = models.SmallIntegerField(blank=False, unique=True)
    login_name = models.CharField(max_length=35, blank=False)
    login_pass = models.CharField(max_length=35, blank=False)

    def get_absolute_url(self):
        return reverse('company_without_department', kwargs={'company_name': self.name})

    def __str__(self):
        return self.name


class SylectusUsers(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    name = models.CharField(max_length=35, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['company', 'name'], name="uniq user"),
        ]


class Emails(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    email = models.CharField(max_length=40, blank=False, unique=True)
    check_for_this_email = models.BooleanField(blank=False, default=True)
    token = models.CharField(default="", max_length=70)
    refresh_token = models.CharField(default="", max_length=70)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['company', 'email'], name="uniq user"),
        ]


class OperationsUsers(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    nick_name = models.CharField(max_length=40, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['company', 'nick_name'], name="uniq user"),
        ]

