import subprocess

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import DateForm
from checker_kpi.models import Company
from . import models
from django.contrib import messages
from checker_kpi.checker_emails import CheckerEmails
import pickle
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@login_required
def main(request, company_name=None):
    if company_name is None:
        company_name = Company.objects.get(id=1).name
    return redirect('company_emails',  company_name)



@login_required
def company_emails(request, company_name, department='emails'):
    dispatchers_email = None
    if request.method == "POST":
        form = DateForm(request.POST)
        if form.is_valid():
            date_dict = form.cleaned_data

            #достаем все екземпляры моделей с емейлами
            company_to_check = models.Company.objects.get(name=company_name)
            emails_to_check = models.Emails.objects.filter(company=company_to_check)
            # если емейла для проверок нет - выводим на екран
            if len(emails_to_check) == 0:
                messages.error(request, f'There is no emails for the company "{company_name}"')
                return render(request, 'company.html', {'main_nav_element': company_name,
                                                        'second_nav_element': department,
                                                        'form': form})
            # если не для всех емейлов есть креды
            emails_to_check_with_creds =[]
            for email in emails_to_check:
                if email.creds == b"":
                    messages.error(request, f"{email.email} hasn't been checked because we don't have credentials for this email")
                else:
                    emails_to_check_with_creds.append(email)

            # достаем диспетчеров которые работают в данной компании
            # и для каждого емейла который подкреплен к этой компании вызываем проверку
            dispatchers_models = models.OperationsUsers.objects.filter(company=company_to_check)
            dispatchers_email = [{'nick': dispatcher.nick_name, 'amount': 0} for dispatcher in dispatchers_models]
            for email in emails_to_check_with_creds:
                creds = pickle.loads(email.creds)
                checker = CheckerEmails(creds, email.email)
                checker.check_emails_by_dispatchers(dispatchers_email, date_dict)



    else:
        form = DateForm()
    return render(request, 'company.html', {'main_nav_element': company_name,
                                            'second_nav_element': department,
                                            'form': form,
                                            'dispatchers_email': dispatchers_email})

@login_required
def company_sylectus(request, company_name, department='sylectus'):
    dispatchers_sylectus = None
    if request.method == "POST":
        form = DateForm(request.POST)
        if form.is_valid():
            date_dict = form.cleaned_data
            company_model = models.Company.objects.get(name=company_name)

            corporate_id = company_model.corporate_id
            login_name = company_model.login_name
            login_pass = company_model.login_pass
            start = date_dict['start'].strftime('%m/%d/%Y')
            end = date_dict['end'].strftime('%m/%d/%Y')

            directory = os.path.join(BASE_DIR, 'sylectus_spider', 'sylectus_spider', 'spiders')
            pipe = subprocess.call(
                ["scrapy", "crawl", "sylectus_spider", "-a", f"date_start={start}", "-a", f"date_end={end}", "-a",
                 f"corporate_id={corporate_id}",
                 "-a", f"user_name={login_name}", "-a", f"user_pass={login_pass}"], cwd=directory)

            print(pipe)

            file_path = os.path.join(directory, "actions.pkl")
            with open(file_path, 'rb') as file:
                result = pickle.load(file)
            company_to_check = models.Company.objects.get(name=company_name)


            dispatchers = models.SylectusUsers.objects.filter(company=company_to_check)
            dispatchers = [dispatcher.name for dispatcher in dispatchers]

            dispatchers_sylectus = [{'nick': dispatcher, 'actions': result.get(dispatcher, None)} for dispatcher in dispatchers]



    else:
        form = DateForm()

    return render(request, 'company.html', {'main_nav_element': company_name,
                                            'second_nav_element': department,
                                            'form': form,
                                            'dispatchers_sylectus': dispatchers_sylectus})
@login_required
def settings(request):
    return render(request, 'settings.html', {'main_nav_element': 'Settings'})


def test(request):
    form = DateForm()
    return render(request, 'test.html', {'form': form})

