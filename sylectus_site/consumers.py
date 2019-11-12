import asyncio
import datetime
import json
import time
import _thread as thread
from google.oauth2.credentials import Credentials
from channels.consumer import AsyncConsumer, SyncConsumer
from channels.db import database_sync_to_async
from checker_kpi.models import Company, Emails, OperationsUsers
from checker_kpi.API import ApiEmails
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
                                            'current_message': info['current_message'],
                                            'already_checked_boxes': info['already_checked_boxes'],
                                            'boxes_to_check': info['boxes_to_check'],
                                            'already_checked_emails': info["already_checked_emails"],
                                            'total_to_check_emails': info['total_to_check_emails'],
                                            'state': info['state'],
                                            })
                    })

                    if info['state'] == "finish":
                        break
                    time.sleep(1)

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
                     'already_checked_boxes': 1,
                     'boxes_to_check': None,
                     'already_checked_emails': 0,
                     'total_to_check_emails': None}

    def get_info(self):
        return self.info

    def check(self, emails_models_to_check):
        dispatchers_models = OperationsUsers.objects.filter(company=self._company_to_check)
        dispatchers_email = [{'nick': dispatcher.nick_name, 'amount': 0} for dispatcher in dispatchers_models]
        self.info['boxes_to_check'] = len(emails_models_to_check)
        checked_boxes = 1
        for email_model in emails_models_to_check:
            self.info['current_message'] = f"Checking {email_model.email}"
            creds = Credentials(token=email_model.token,
                                refresh_token=email_model.refresh_token,
                                token_uri=google_config['token_uri'],
                                client_id=google_config['client_id'],
                                client_secret=google_config['client_secret'],
                                scopes=['https://www.googleapis.com/auth/spreadsheets'])
            checker = CheckerEmails(creds, email_model.email, self.info)
            checker.check_emails_by_dispatchers(dispatchers_email, self._dates)
            checked_boxes += 1
            self.info['already_checked_boxes'] = checked_boxes
        self.info['state'] = "finish"
        print('finish')




