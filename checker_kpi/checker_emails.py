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
global_emails_from_batch = []
global_ids_emails_to_request_again = []
global_checked_errors = []


def check_message(request_id, response, exception):
    global global_emails_from_batch, global_ids_emails_to_request_again
    if exception is None:
        global_emails_from_batch.append({'response': response, 'id': request_id})
    else:
        print(f"catch error: {exception}")
        global_ids_emails_to_request_again.append(request_id)


def check_errors(request_id, response, exception):
    global global_checked_errors
    if exception is None:
        global_checked_errors.append({'response': response, 'id': request_id})
    else:
        print('not catched error')
        print(request_id)
        print(exception)


def get_body_from_part(part):
    if part['mimeType'] == 'text/plain' or part['mimeType'] == 'multipart/alternative':
        if part['body']['size'] != 0:
            encoded_body = part['body']['data']
            decoded_body = base64.urlsafe_b64decode(encoded_body).decode()
            return decoded_body
    return ''


class CheckerEmails:
    def __init__(self, creds, email, info_from_thread):
        self._service = build('gmail', 'v1', credentials=creds)
        self._email = email
        self._info_from_thread = info_from_thread
        self._labels_not_to_check = ['CHAT']
        self._regexp = re.compile(r"(On [A-Z][a-z]{2}, [A-Z][a-z]{2} \d{1,2}, \d{4} at \d{1,2}:\d{2} (AM|PM) (.|\s){0,70}@(.|\s){0,70}wrote:)|([А-я]{2}, \d{1,2} [А-я]+\.? \d{4} г\.,? в? ?\d{1,2}:\d{1,2},? (.|\s){0,70}@.+\.)|(---------- Forwarded message ---------)")

    @staticmethod
    def _get_body_from_part(part):
        if part['mimeType'] == 'text/plain' or part['mimeType'] == 'multipart/alternative':
            if part['body']['size'] != 0:
                encoded_body = part['body']['data']
                decoded_body = base64.urlsafe_b64decode(encoded_body).decode()
                return decoded_body
        return ''

    def _get_cleared_body_from_payload(self, payload):
        body = ""
        # если часть в письме 1
        if 'parts' not in payload:
            body = self._get_body_from_part(payload)
        # если много частей в письме
        else:
            for part in payload['parts']:
                if 'parts' not in part:
                    partial_body = self._get_body_from_part(part)
                    body += partial_body

                # если и у частей есть части : собираем все декодируем и собираем в кучу
                else:
                    for sub_part in part['parts']:
                        partial_body = self._get_body_from_part(sub_part)
                        body += partial_body
        if body != "":
            # можно ловить дебагером нужные емейлы
            # if message['id'] == '16b8f1a147345d49':
            #     print('gotcha')

            # убираем цитату в теле письма
            reg_exp_obj = self._regexp.search(body)
            if reg_exp_obj is not None:
                start_of_quote = reg_exp_obj.start()
                cleared_body = body[:start_of_quote]
            else:
                cleared_body = body
        else:
            cleared_body = body
        return cleared_body

    def check_emails_by_dispatchers(self, dispatchers, dates):
        global global_emails_from_batch, global_ids_emails_to_request_again, global_checked_errors
        query = f"from:me -label:({' OR '.join(self._labels_not_to_check)}) " \
                f"after:{dates['start'].strftime('%Y/%m/%d/')} before:{dates['end'].strftime('%Y/%m/%d/')}"
        mails_raw = self._service.users().messages().list(userId='me', q=query).execute()
        # если ничего не нашло
        if mails_raw['resultSizeEstimate'] == 0:
            print(f'nothing for {self._email}')
            return
        estimate_emails = mails_raw["resultSizeEstimate"]
        self._info_from_thread['total_to_check_emails'] = estimate_emails
        checked = 0
        # и теперь в цыкле достаем из списка писем котороые подходят по query ид каждого письма
        # и посылаем запрос что бы получить всю информацию по нужному письму
        while True:
            batch = self._service.new_batch_http_request(callback=check_message)
            for mail_raw in mails_raw['messages']:
                mail_id = mail_raw['id']
                mail = self._service.users().messages().get(userId='me', id=mail_id, format='full')
                batch.add(request=mail, request_id=mail_id)
            # изменяет global_emails_from_batch и global_ids_emails_to_request_again через global
            batch.execute()

            # если были ошибки, проходимся по ним еще раз
            if len(global_ids_emails_to_request_again) != 0:
                sleep(2)
                batch = self._service.new_batch_http_request(callback=check_errors)
                for mail_id in global_ids_emails_to_request_again:
                    mail = self._service.users().messages().get(userId='me', id=mail_id, format='full')
                    batch.add(request=mail, request_id=mail_id)

                # изменяет global_checked_errors через global
                batch.execute()
            total_messages_from_batch = global_emails_from_batch + global_checked_errors
            # проверяем каждое письмо из батчей
            for message in total_messages_from_batch:
                cleared_body = self._get_cleared_body_from_payload(message['response']['payload'])
                # по диспетчерам
                for dispatcher in dispatchers:
                    if dispatcher['nick'] in cleared_body:
                        dispatcher['amount'] += 1
            checked += len(mails_raw['messages'])
            global_emails_from_batch = []
            global_checked_errors = []
            global_ids_emails_to_request_again = []
            self._info_from_thread['already_checked_emails'] = checked
            print(f"checked {checked} from {estimate_emails}")
            # если больше нет листов для проверки - на выход
            if 'nextPageToken' not in mails_raw:
                break
            # если есть - повторяем
            page_token = mails_raw['nextPageToken']
            mails_raw = self._service.users().messages().list(userId='me', pageToken=page_token, q=query).execute()
        self._info_from_thread['total_checked_emails'] += checked

