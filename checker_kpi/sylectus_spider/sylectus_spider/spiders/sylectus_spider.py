import datetime
import pickle
import pprint

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import FormRequest


class SylectusSpider(scrapy.Spider):
    def __init__(self, date_start, date_end, corporate_id, user_name, user_pass):
        self._corporate_id = corporate_id
        self._user_name = user_name
        self._user_pass = user_pass
        self._date_start = date_start
        self._date_end = date_end
        scrapy.Spider.__init__(self)

    name = "sylectus_spider"
    start_urls = [
        'https://www.sylectus.com/Login.aspx'
    ]
    def parse(self, response):

        viewstate = response.css('[id="__VIEWSTATE"]::attr(value)').extract_first()
        viewstategenerator = response.css('[id="__VIEWSTATEGENERATOR"]::attr(value)').extract_first()
        eventvalidation = response.css('[id="__EVENTVALIDATION"]::attr(value)').extract_first()
        return FormRequest.from_response(response, formdata={
            "ctl00$bodyPlaceholder$corporateIdField": self._corporate_id,
            "__EVENTTARGET": "ctl00$bodyPlaceholder$corpLoginButton",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation

        }, callback=self.second_login)

    def second_login(self, response):
        user_ids = response.css('[id="ctl00_bodyPlaceholder_userList"] > option::attr(value)').extract()
        user_names = response.css('[id="ctl00_bodyPlaceholder_userList"] > option::text').extract()
        if len(user_names) != len(user_ids):
            raise Exception("We have unequal amount of users and their ids")
        users = {}
        for i in range(len(user_names)):
            users[user_names[i]] = user_ids[i]

        user_id = users.get(self._user_name, None)
        if user_id is None:
            raise Exception("Check the user name")

        viewstate = response.css('[id="__VIEWSTATE"]::attr(value)').extract_first()
        viewstategenerator = response.css('[id="__VIEWSTATEGENERATOR"]::attr(value)').extract_first()
        eventvalidation = response.css('[id="__EVENTVALIDATION"]::attr(value)').extract_first()
        return FormRequest.from_response(response, formdata={
            "ctl00$bodyPlaceholder$userList": user_id,
            "ctl00$bodyPlaceholder$userPasswordField": self._user_pass,
            "__EVENTTARGET": "ctl00$bodyPlaceholder$userLoginButton",
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewstategenerator,
            "__EVENTVALIDATION": eventvalidation
        }, callback=self.logged_in)

    def logged_in(self, response):
        title = response.css('title::text').extract_first().strip()
        if title != "Sylectus - Trucking's Most Powerful Network":
            raise Exception("Something is wrong, probably ID and password combination is invalid")
        self._server_url = response.url.split('/sylectus.asp')[0]
        return FormRequest(self._server_url+"/II05_translogs.asp", method="POST",
                                         callback=self.trans_log,
                                         formdata={
                                             'fromdate': self._date_start,
                                             'todate': self._date_end,
                                         }, )

    @staticmethod
    def trans_log(response):
        rows = response.css('[action="II05_translogs.asp"]>center>table[width="100%"][cellpadding="1"]>tr')
        actions_by_user = {}
        for row in rows:
            user = row.css('td:nth-child(3)::text').extract_first()
            if user is not None:
                user = user.strip()
            action = row.css('td:nth-child(8)::text').extract_first()
            if action is not None:
                action = action.strip().replace(" ", "_")
            actions = actions_by_user.get(user, None)
            if actions is None:
                actions_by_user[user] = {}
            amount = actions_by_user[user].get(action, None)
            if amount is None:
                actions_by_user[user][action] = 0
                amount = 0
            total = actions_by_user[user].get('Total', None)
            if total is None:
                actions_by_user[user]['Total'] = 0
                total = 0
            actions_by_user[user]['Total'] = total + 1
            actions_by_user[user][action] = amount + 1
        with open('actions.pkl', 'wb') as file:
            pickle.dump(actions_by_user, file)

    # @staticmethod
    # def write_to_html(response):
    #     with open('response.html', 'w') as file:
    #         file.write(response.text)

if __name__ == "__main__":
    import subprocess
    # (self, date_start, date_end, corporate_id, user_name, user_pass):
    dates = {'start': datetime.datetime.now() - datetime.timedelta(days=30), 'end': datetime.datetime.now()}
    start = dates['start'].strftime('%m/%d/%Y')
    end = dates['end'].strftime('%m/%d/%Y')
    corporate_id = "26140"
    user_name = 'UUpdat'
    user_pass = "Del2029"
    direcotry = "C:\\Users\\Dispatcher\\Python\\sylectus_site\\checker_kpi\\sylectus_spider\\sylectus_spider\\spiders"
    pipe = subprocess.call(["scrapy", "crawl", "sylectus_spider", "-a", f"date_start={start}", "-a", f"date_end={end}", "-a", f"corporate_id={corporate_id}",
                           "-a", f"user_name={user_name}", "-a", f"user_pass={user_pass}"], cwd=direcotry)

    with open('actions.pkl', 'rb') as file:
        result = pickle.load(file)
