import base64
import pickle
import os
import re
import sys
from checker_kpi import models
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pprint import pprint
import datetime


def get_creds():
    scopes = ['https://www.googleapis.com/auth/gmail.readonly']
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', scopes)
    creds = flow.run_local_server(port=0)
    service = build('gmail', 'v1', credentials=creds)
    email = service.users().getProfile(userId='me').execute()['emailAddress']
    model = models.Emails.objects.filter(email=email).first()
    model.creds = pickle.dumps(creds)
    model.save()
    print(f"We added creds to {email}")


class CheckerEmails:
    def __init__(self, creds, email):
        self._service = build('gmail', 'v1', credentials=creds)

        # проверка на соотвествие кредов
        email_creds = self._service.users().getProfile(userId='me').execute()['emailAddress']
        if email != email_creds:
            raise Exception(f"Credentials are for {email_creds} but expected for {email}")
        self._labels_not_to_check = ['CHAT']
        self._regexp = re.compile(r"(On [A-Z][a-z]{2}, [A-Z][a-z]{2} (\d){1,2}, (\d){4} at (\d){1,2}:\d\d (AM|PM) (.|\s)+wrote)")

    @staticmethod
    def get_body_from_part(part):
        if part['mimeType'] == 'text/plain' or part['mimeType'] == 'multipart/alternative':
            if part['body']['size'] != 0:
                encoded_body = part['body']['data']
                decoded_body = base64.urlsafe_b64decode(encoded_body).decode()
                return decoded_body
        return ''

    def check_emails_by_dispatchers(self, dispatchers, dates):
        query = f"from:me -label:({' OR '.join(self._labels_not_to_check)}) " \
                f"after:{dates['start'].strftime('%Y/%m/%d/')} before:{dates['end'].strftime('%Y/%m/%d/')}"
        mails_raw = self._service.users().messages().list(userId='me', q=query).execute()
        # если ничего не нашло
        if mails_raw['resultSizeEstimate'] == 0:
            return dispatchers

        # и теперь в цыкле достаем из списка писем котороые подходят по query ид каждого письма
        # и посылаем запрос что бы получить всю информацию по нужному письму
        while True:
            for mail_raw in mails_raw['messages']:
                mail_id = mail_raw['id']
                message = self._service.users().messages().get(userId='me', id=mail_id, format='full').execute()

                # TODO: убрать, сейчас для получения ид письма на котором все рухнуло
                for header in message['payload']['headers']:
                    if header['name'] == 'Message-ID':
                        message_id_for_gui = header['value']

                body = ""
                # если часть в письме 1
                if 'parts' not in message['payload']:
                    body = self.get_body_from_part(message['payload'])
                # если много частей в письме
                else:
                    for part in message['payload']['parts']:
                        if 'parts' not in part:
                            partial_body = self.get_body_from_part(part)
                            body += partial_body

                        # если и у частей есть части : собираем все декодируем и собираем в кучу
                        else:
                            for sub_part in part['parts']:
                                partial_body = self.get_body_from_part(sub_part)
                                body += partial_body


                if body != "":
                    cleared_body = ""
                    # херня какая-то, если не читстить руками перед регекспом - думает пол дня
                    for line in body.split('\r\n'):
                        if len(line) != 0:
                            if line[0] != '>':
                                cleared_body += line+"\r\n"

                    # убираем цитату в теле письма
                    reg_exp_obj = self._regexp.search(cleared_body)
                    if reg_exp_obj is not None:
                        start_of_quote = reg_exp_obj.start()
                        cleared_body = cleared_body[:start_of_quote]
                    # тут у нас уже есть текст письма, который отправил диспетчер
                    # и проверяем
                    for dispatcher in dispatchers:
                        if dispatcher['nick'] in cleared_body:
                            dispatcher['amount'] += 1
            # если больше нет листов для проверки - на выход
            if 'nextPageToken' not in mails_raw:
                break
            # если есть - потворяем
            page_token = mails_raw['nextPageToken']
            mails_raw = self._service.users().messages().list(userId='me', pageToken=page_token).execute()









if __name__ == "__main__":
    from django.conf import settings
    settings.configure(DEBUG=True)

    company_to_check = 1
    email = "bruce@rhinodispatch.com"
    email_model = models.Emails.objects.filter(email=email).first()
    if email_model is None:
        raise Exception(f"We don't have email: {email} in our data base")
    creds = pickle.loads(email_model.creds)
    if not creds:
        get_creds()
    if creds.expired:
        creds.refresh(Request())
        email_model.creds = pickle.dumps(creds)
        email_model.save()

    dispatchers_models = models.OperationsUsers.objects.filter(company=company_to_check)
    dispatchers = [{'dispatcher': dispatcher.nick_name, 'amount': 0} for dispatcher in dispatchers_models]
    checker = CheckerEmails(creds, email)
    now = datetime.datetime.now()
    dates = {'start': now-datetime.timedelta(days=2), 'end': now}
    checker.check_emails_by_dispatchers(dispatchers, dates)







