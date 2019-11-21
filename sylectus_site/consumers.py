import asyncio
import datetime
import json
import time
import _thread as thread
from google.oauth2.credentials import Credentials
from channels.consumer import AsyncConsumer, SyncConsumer
from checker_kpi.models import Company, Emails, OperationsUsers
from checker_kpi.checker_emails import CheckerEmails
from sylectus_site.config import google_config


class EmailsConsumer(SyncConsumer):
    def websocket_connect(self, event):
        print('coneced')
        self.send({
            "type": "websocket.accept"
        })

    def websocket_receive(self, event):
        path = self.scope['path']
        front_response = event.get('text', None)
        print(front_response)
        if front_response is not None:
            front_response = json.loads(front_response)
            if front_response['type'] == 'start_script_emails':
                partial_company = path[path.find('company/')+8:]
                company_name = partial_company[:partial_company.find('/')]
                print(front_response['start'])
                dates = {'start': datetime.datetime.strptime(front_response['start'], "%m/%d/%Y"),
                         'end': datetime.datetime.strptime(front_response['end'], "%m/%d/%Y")}
                company = Company.objects.get(name=company_name)
                info = self.start_script(company, dates)

                # постоянно отправляем данные на фронт, пока все не проверим
                while True:
                    self.send({
                        'type': 'websocket.send',
                        'text': json.dumps({'type': 'checker of emails',
                                            'data': info})
                    })

                    if info['state'] == "finish":
                        break
                    time.sleep(1)
                self.send({
                    'type': 'websocket.send',
                    'text': json.dumps({'type': 'checker of emails',
                                        'data': info})
                })

    def start_script(self, company, dates):
        emails__models_to_check = Emails.objects.filter(company=company)
        checker = EmailApi(company, dates)
        info = checker.get_info()
        thread.start_new_thread(checker.check, (emails__models_to_check,))
        return info

    def websocket_disconnect(self, event):
        pass
        # front_response = event.get('text', None)


class EmailApi:
    def __init__(self, company_to_check, dates):
        self._company_to_check = company_to_check
        self._dates = dates
        self.info = {'current_message': 'Start checking',
                     'state': "in_progress",
                     'current_box_number': 1,
                     'boxes_to_check': None,
                     'already_checked_emails': 0,
                     'total_to_check_emails': None,
                     'total_checked_emails': 0}

    def get_info(self):
        return self.info

    def check(self, emails_models_to_check):
        dispatchers_models = OperationsUsers.objects.filter(company=self._company_to_check)
        dispatchers_email = [{'nick': dispatcher.nick_name, 'amount': 0} for dispatcher in dispatchers_models]
        self.info['boxes_to_check'] = len(emails_models_to_check)
        current_box = 0
        print(f"boxes to check {emails_models_to_check}")
        for email_model in emails_models_to_check:
            current_box += 1
            self.info['current_box_number'] = current_box
            self.info['current_message'] = f"Checking {email_model.email}"
            creds = Credentials(token=email_model.token,
                                refresh_token=email_model.refresh_token,
                                token_uri=google_config['token_uri'],
                                client_id=google_config['client_id'],
                                client_secret=google_config['client_secret'],
                                scopes=['https://www.googleapis.com/auth/spreadsheets'])
            checker = CheckerEmails(creds, email_model.email, self.info)
            checker.check_emails_by_dispatchers(dispatchers_email, self._dates)

        self.info['dispatchers'] = dispatchers_email
        self.info['state'] = "finish"

        print('finish')




