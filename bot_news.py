import requests
import pandas as pd
import datetime
from bs4 import BeautifulSoup
import requests
import telebot
import copy
import time

TOKEN = ''

bot = telebot.TeleBot(TOKEN)



def send_message(title, body, site, times, df):
    dicts = df.to_dict('records')
    tb = telebot.TeleBot(TOKEN)
    for step in dicts:
        CHAT_ID = step['id']
        markdown = f"""
        *{title}*
        [ ]({site})
{body}
        """
        try:
            ret_msg = tb.send_message(CHAT_ID, markdown, parse_mode="Markdown")
            assert ret_msg.message_id
        except:
            pass
headers = {
    'authority': 'vc.ru',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'sec-fetch-site': 'none',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-user': '?1',
    'sec-fetch-dest': 'document',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'cookie': 'osnova-aid=CvQJgGIo75CQWQAIByLhAg==; is_webp_supported=1; _gid=GA1.2.24394999.1646849950; fingerprint=t4OYgKwHfbEOHjgwdicyQEX7hdHBn5cd8m5TQT7H; an-data={"segues":["/popular"]}; _ga_EL542L5X4J=GS1.1.1646849944.1.1.1646849971.0; _ga=GA1.2.893310984.1646849950; adblock-state=1',
}

def replace_title(string):
    string = string.replace('  ', '')
    string = string.replace('\\', '')
    string = string.replace('<span class="content-title__last-', '')
    return string


def replace_body(string):
    string = string.split('<')
    try:
        string = string[0] + string[-1][5:]
    except:
        pass
    return string

class Main:
    def load_users():
        response = requests.get(f'https://api.telegram.org/bot{TOKEN}/getUpdates')
        data = pd.DataFrame()
        try:
            for step in response.json()['result']:
                id_ = step['message']['from']['id']
                name = step['message']['from']['first_name']
                curr_user = [[id_, name]]
                curr_user = pd.DataFrame(curr_user, columns=['id', 'Name'])
                data = pd.concat([data, curr_user], axis=0)
                return data
        except:
            return data

    def get_new_users():
        try:
            old_user = pd.read_csv('users.csv')
            old_user.columns = ['id', 'Name']
            data = Main.load_users()
            if data.shape[0] != 0:
                all_users = pd.concat([old_user, data], axis = 0)
                all_users = all_users.drop_duplicates(subset=['id', 'Name'], keep='last')
                all_users.to_csv('users.csv', index = False)
                return all_users
            else:
                return old_user
        except:
            data = Main.load_users()
            data.to_csv('users.csv', index = False)
            return data

    def download():
        response = requests.get('https://vc.ru/new', headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        title, body, time, site = [], [], [], []
        alls = soup.find_all("div", {"class": "content content--short"})
        for step in alls:
            step.find_all("div", {"class": "l-island-a"})
            try:
                titl = str(step.find_all("div", {"class": "l-island-a"})[0]).split('>')[1][1:-5]
                titl = replace_title(titl)
            except:
                titl = ''
            title.append(titl)
            try:
                curr_body = str(step.find_all("div", {"class": "l-island-a"})[1]).split('<p>')[1][:-11]
                curr_body = replace_body(curr_body)
            except:
                curr_body = ''
            body.append(curr_body)

        for t in soup.find_all("time", {"class": "time"}):
            time.append(str(t).split('title="')[1][:19])

        for step in range(0, len(alls)):
            for a in alls[step].find_all("a", {"class": "content-link"}):
                site.append(a['href'])

        df = pd.DataFrame(list(zip(title, body, site, time)),
                          columns=['title', 'body', 'site', 'time'])
        df['time'] = df.apply(lambda x: datetime.datetime.strptime(str(x['time']), '%d.%m.%Y %H:%M:%S'), axis=1)
        df['time'] = pd.to_datetime(df['time'])
        return df

    def polling():
        all_users = Main.get_new_users()
        all_users = all_users.drop_duplicates(subset=['id', 'Name'], keep='last')
        df = Main.download()

        old_df = pd.read_csv('news.csv')
        old_df['time'] = old_df.apply(lambda x: datetime.datetime.strptime(str(x['time']), '%Y-%m-%d %H:%M:%S'), axis=1)
        date_old = old_df['time'][0]
        to_send = df.query("@date_old < time")
        to_send = to_send.sort_values(by='time')
        to_send = to_send.to_dict('records')

        for step in to_send:
            title = step['title'].split(' ')
            title = ' '.join(str(e) for e in title)
            body = step['body'].split(' ')
            body = ' '.join(str(e) for e in body)
            send_message(title, body, step['site'], step['time'], all_users)
            print(title)
        if len(to_send) != 0:
            print(f'Обновление произошло в: {datetime.datetime.now()}')
            df.to_csv('news.csv', index=False)
            # print('Конец итерации')
        time.sleep(60)

while True:
    try:
        Main.polling()
    except:
        time.sleep(60)
