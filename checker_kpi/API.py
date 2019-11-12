import datetime
import os
import pickle
from google.auth.transport.requests import Request
from checker_kpi import models
import httplib2
from checker_kpi.checker_emails import CheckerEmails
from checker_kpi.models import Company
from sylectus_site.config import google_config
from google.oauth2.credentials import Credentials
from sylectus_site.settings import BASE_DIR

class ApiEmails:
    def __init__(self, company_to_check, dates, info_from_thread):
        self._company_to_check = company_to_check
        self._dates = dates
        self._info_from_thread = info_from_thread

    def run_checker(self):
        # достаем все екземпляры моделей с емейлами
        print(self._company_to_check)

        # если емейла для проверок нет - выводим на екран

        if len(emails_to_check) == 0:
            self._info_from_thread['current_message'] = f'There is no emails for the company "{self._company_to_check}"'
            self._info_from_thread['state'] = 'finish'
            return

        # достаем диспетчеров которые работают в данной компании
        # и для каждого емейла который подкреплен к этой компании вызываем проверку
        dispatchers_models = models.OperationsUsers.objects.filter(company=self._company_to_check)
        dispatchers_email = [{'nick': dispatcher.nick_name, 'amount': 0} for dispatcher in dispatchers_models]
        for email_model in emails_to_check:
            print(f"checking for {email_model.email}")
            creds = Credentials(token=email_model.token,
                                refresh_token=email_model.refresh_token,
                                token_uri=google_config['token_uri'],
                                client_id=google_config['client_id'],
                                client_secret=google_config['client_secret'],
                                scopes=['https://www.googleapis.com/auth/spreadsheets'])

            checker = CheckerEmails(creds, email_model.email)
            checker.check_emails_by_dispatchers(dispatchers_email, self._dates)


