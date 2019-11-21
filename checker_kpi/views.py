import subprocess
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from .forms import DateForm
from checker_kpi.models import Company, Emails
from . import models
from django.urls import reverse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from checker_kpi.checker_emails import CheckerEmails
from django.http import HttpResponseRedirect, HttpResponse
from sylectus_site import config_private
from sylectus_site.config import google_config
import os
from googleapiclient.discovery import build
import pickle
from google.auth.transport.requests import Request
import requests
from django.contrib import messages
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@login_required
def main(request, company_name=None):
    if company_name is None:
        company_name = Company.objects.filter(id=1)
        print(company_name)
        if len(company_name) != 0:
            company_name = company_name.name
        else:
            company_name = None
    return redirect('company_sylectus',  company_name)



@login_required
def company_emails(request, company_name, department='emails'):
    dispatchers_email = None
    # проверяем если все норм с кредами
    company_to_check = models.Company.objects.get(name=company_name)
    emails_to_check = Emails.objects.filter(company=company_to_check)
    # проверяем есть ли креды
    for email_model in emails_to_check:
        creds = Credentials(token=email_model.token,
                            refresh_token=email_model.refresh_token,
                            token_uri=google_config['token_uri'],
                            client_id=google_config['client_id'],
                            client_secret=google_config['client_secret'],
                            scopes=['https://www.googleapis.com/auth/spreadsheets'])
        #проверяем все ли ок с кердами, если нет - выводим линк для получения кредов
        try:
            if not creds.valid or creds.token == "" or creds.refresh_token == "":
                raise Exception('not valid or empty creds')
            if creds.expired:
                creds.refresh(Request())
                email_model.token = creds.token
                email_model.save()
        except Exception:
            # если проблема с кредами - редиректим на страницу где есть линк на разрешить доступ и
            # название емейла для кого
            return render(request, "settings.html", {'main_nav_element': 'Settings',
                                                     "redirect_for": email_model.email})

    form = DateForm()

    return render(request, 'company.html', {'main_nav_element': company_name,
                                    'second_nav_element': department,
                                    'form': form,
                                    'dispatchers_email': dispatchers_email})


@login_required
def company_sylectus(request, company_name, department='sylectus'):
    dispatchers_sylectus = None
    company_to_check = models.Company.objects.get(name=company_name)
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
            JSON_OBJ = {
                "request": {
                    "url": "https://www.sylectus.com/Login.aspx",
                    "meta": {
                        "corporate_id": str(corporate_id),
                        "user_name": str(login_name),
                        "date_start": start,
                        "date_end": end,
                        "user_pass": str(login_pass)
                    }
                },
                "spider_name": "sylectus_spider"
            }
            response = requests.post("http://localhost:9080/crawl.json", json=JSON_OBJ)
            dict_from_scrapy = response.json()['items'][0]
            if 'Error' not in dict_from_scrapy:
                dispatchers = models.SylectusUsers.objects.filter(company=company_to_check)
                dispatchers = [dispatcher.name for dispatcher in dispatchers]
                dispatchers_sylectus = [{'nick': dispatcher, 'actions': dict_from_scrapy.get(dispatcher, None)}
                                        for dispatcher in dispatchers]
            else:
                print('error')
                messages.error(request, dict_from_scrapy['Error'])

    else:
        form = DateForm()

    return render(request, 'company.html', {'main_nav_element': company_name,
                                            'second_nav_element': department,
                                            'form': form,
                                            'dispatchers_sylectus': dispatchers_sylectus})
@login_required
def settings(request):
    return render(request, 'settings.html', {'main_nav_element': 'Settings'})


@login_required
def set_creds(request, ):
    print(f'setting creds ')

    dir_name = os.path.join(os.path.dirname(__file__))
    flow = Flow.from_client_secrets_file(
        os.path.join(dir_name, 'credentials.json'), google_config['scopes'])
    flow.redirect_uri = f'{config_private.hostname}/catch_creds'
    authorization_url, state = flow.authorization_url(access_type='offline',
                                                      include_granted_scopes='true')
    request.session['code_verifier'] = flow.code_verifier
    request.session['state'] = state
    print(f" set creds - state:{state}, code:{flow.code_verifier}")
    return HttpResponseRedirect(authorization_url)

@login_required
def catch_creds(request):
    dir_name = os.path.join(os.path.dirname(__file__))
    state = request.session['state']
    code_verifier = request.session['code_verifier']
    print(f" catch creds - state:{state}, code:{code_verifier}")
    flow = Flow.from_client_secrets_file(
        os.path.join(dir_name,  'credentials.json'),
        scopes=google_config['scopes'],
        state=state)
    flow.redirect_uri = f'{config_private.hostname}/catch_creds'
    flow.code_verifier = code_verifier
    authorization_response = request.build_absolute_uri()
    flow.fetch_token(authorization_response=authorization_response)
    creds = flow.credentials
    service = build('gmail', 'v1', credentials=creds, cache_discovery=False)
    email_from_creds = service.users().getProfile(userId='me').execute()['emailAddress']

    email_model = Emails.objects.get(email=email_from_creds)

    email_model.refresh_token = creds.refresh_token
    email_model.token = creds.token
    email_model.save()
    return HttpResponseRedirect(reverse('main'))

def test(request):
    data = {'aa': 11, "bb": 22}
    return JsonResponse(data, safe=False)

