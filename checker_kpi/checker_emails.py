import base64
import pickle
import os
import re
from time import sleep

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from pprint import pprint
import datetime
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
global_variable_for_emails = []
global_variable_for_errors = []

def check_message(request_id, response, exception):
    global global_variable_for_emails
    if exception is None:
        global_variable_for_emails.append({'response': response, 'id': request_id})
    else:
        print(request_id)
        print(exception)


def get_body_from_part(part):
    if part['mimeType'] == 'text/plain' or part['mimeType'] == 'multipart/alternative':
        if part['body']['size'] != 0:
            encoded_body = part['body']['data']
            decoded_body = base64.urlsafe_b64decode(encoded_body).decode()
            return decoded_body
    return ''


def get_creds():
    scopes = ['https://www.googleapis.com/auth/gmail.readonly']
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', scopes)
    creds = flow.run_local_server(port=0)
    service = build('gmail', 'v1', credentials=creds)
    email = service.users().getProfile(userId='me').execute()['emailAddress']
    with open('creds.pickle', 'rb') as token:
        creds_pickl = pickle.load(token)
    creds_pickl[email] = creds
    with open('creds.pickle', 'wb') as token:
        pickle.dump(creds_pickl, token)
    print(f"We added creds for {email}")


class CheckerEmails:
    def __init__(self, creds, email):
        self._service = build('gmail', 'v1', credentials=creds)

        # проверка на соотвествие кредов
        email_creds = self._service.users().getProfile(userId='me').execute()['emailAddress']
        if email != email_creds:
            raise Exception(f"Credentials are for {email_creds} but expected for {email}")
        self._email = email
        self._labels_not_to_check = ['CHAT']
        self._regexp = re.compile(r"(On [A-Z][a-z]{2}, [A-Z][a-z]{2} \d{1,2}, \d{4} at \d{1,2}:\d{2} (AM|PM) (.|\s){0,70}@(.|\s){0,70}wrote:)|([А-я]{2}, \d{1,2} [А-я]+\.? \d{4} г\.,? в? ?\d{1,2}:\d{1,2},? (.|\s){0,70}@.+\.)|(---------- Forwarded message ---------)")

    @staticmethod
    def get_body_from_part(part):
        if part['mimeType'] == 'text/plain' or part['mimeType'] == 'multipart/alternative':
            if part['body']['size'] != 0:
                encoded_body = part['body']['data']
                decoded_body = base64.urlsafe_b64decode(encoded_body).decode()
                return decoded_body
        return ''


    def check_emails_by_dispatchers(self, dispatchers, dates):
        global global_variable_for_emails
        query = f"from:me -label:({' OR '.join(self._labels_not_to_check)}) " \
                f"after:{dates['start'].strftime('%Y/%m/%d/')} before:{dates['end'].strftime('%Y/%m/%d/')}"
        mails_raw = self._service.users().messages().list(userId='me', q=query).execute()
        # если ничего не нашло
        if mails_raw['resultSizeEstimate'] == 0:
            print(f'nothing for {self._email}')
            return dispatchers
        estimate_emails = mails_raw["resultSizeEstimate"]
        checked = 0
        # и теперь в цыкле достаем из списка писем котороые подходят по query ид каждого письма
        # и посылаем запрос что бы получить всю информацию по нужному письму
        while True:
            batch = self._service.new_batch_http_request(callback=check_message)
            for mail_raw in mails_raw['messages']:
                mail_id = mail_raw['id']
                mail = self._service.users().messages().get(userId='me', id=mail_id, format='full')
                batch.add(request=mail, request_id=mail_id)

            # изменяет mails через nonlocal
            batch.execute()

            # проверяем каждое письмо в батче
            for message in global_variable_for_emails:
                # TODO: убрать, сейчас для получения ид письма на котором все рухнуло
                for header in message['response']['payload']['headers']:
                    if header['name'] == 'Message-ID':
                        message_id_for_gui = header['value']
                if message_id_for_gui is None:
                    raise Exception(f'message without message_id_for_gui:{message}')

                # проверяю если емейл был отправлен с нужной мне почты
                for header in message['response']['payload']['headers']:
                    if header['name'] == 'From':
                        try:
                            email_from = header['value'].split('<')[1].split('>')[0]
                        except:
                            print(f"message_id_for_gui {message_id_for_gui}")
                            print(f"header {header['value']}")

                if email_from != self._email:
                    continue
                body = ""
                # если часть в письме 1
                if 'parts' not in message['response']['payload']:
                    body = self.get_body_from_part(message['response']['payload'])
                # если много частей в письме
                else:
                    for part in message['response']['payload']['parts']:
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
                    #херня какая-то, если не читстить руками перед регекспом - думает пол дня (решил)
                    # for line in body.split('\r\n'):
                    #     if len(line) != 0:
                    #         if line[0] != '>':
                    #             cleared_body += line + "\r\n"
                    cleared_body = body
                    # if message['id'] == '16b8f1a147345d49':
                    #     print('gotcha')
                    # убираем цитату в теле письма
                    reg_exp_obj = self._regexp.search(cleared_body)
                    if reg_exp_obj is not None:
                        start_of_quote = reg_exp_obj.start()
                        cleared_body = cleared_body[:start_of_quote]
                    # тут у нас уже есть текст письма, который отправил диспетчер
                    # print("===" * 25)
                    # print(f"message_id_for_gui {message_id_for_gui}")
                    # print(f'message id gmail api {message["id"]}')
                    # print(cleared_body)

                    # и проверяем
                    for dispatcher in dispatchers:
                        if dispatcher['nick'] in cleared_body:
                            dispatcher['amount'] += 1
            print(dispatchers)
            checked += len(mails_raw['messages'])
            global_variable_for_emails = []
            print(f"checked {checked} from {estimate_emails}")
            # если больше нет листов для проверки - на выход
            if 'nextPageToken' not in mails_raw:
                break
            # если есть - повторяем
            page_token = mails_raw['nextPageToken']
            mails_raw = self._service.users().messages().list(userId='me', pageToken=page_token, q=query).execute()








if __name__ == "__main__":
    with open('creds.pickle', 'rb') as token:
        creds_pickl = pickle.load(token)
    creds = creds_pickl['tracking1@deltaexpressinc.com']
    checker = CheckerEmails(creds, 'tracking1@deltaexpressinc.com')
    names = ["Nick", "Bruce", "Craig"]
    dispatchers = [{'nick': dispatcher, 'amount': 0} for dispatcher in names]
    dates = {'start': datetime.datetime.now()-datetime.timedelta(days=2), "end": datetime.datetime.now()+datetime.timedelta(days=1)}
    checker.check_emails_by_dispatchers(dispatchers, dates)
    # service = build('gmail', 'v1', credentials=creds)
    # mail_id = '16b8f1a147345d49'
    # mail = service.users().messages().get(userId='me', id=mail_id, format='full').execute()
    #
    # body = ""
    # # если часть в письме 1
    # if 'parts' not in mail['payload']:
    #     body = get_body_from_part(mail['payload'])
    # # если много частей в письме
    # else:
    #     for part in mail['payload']['parts']:
    #         if 'parts' not in part:
    #             partial_body = get_body_from_part(part)
    #             body += partial_body
    #
    #         # если и у частей есть части : собираем все декодируем и собираем в кучу
    #         else:
    #             for sub_part in part['parts']:
    #                 partial_body = get_body_from_part(sub_part)
    #                 body += partial_body