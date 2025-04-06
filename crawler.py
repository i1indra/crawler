from configparser import ConfigParser
import mysql.connector.pooling
from multiprocessing import Queue
import hashlib
import requests
import xmltodict
import threading
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import time


config = ConfigParser()
config.read("config.yml")


mydb = config["database"]


q = Queue()


connectionpool = (mysql.connector.pooling.MySQLConnectionPool(pool_name="example_pool",
                                                             pool_size=20,
                                                             autocommit=True,
                                                             **mydb))


def parser(owner):
    connect = connectionpool.get_connection()
    cursor = connect.cursor()
    cursor.execute("SELECT site_name, url FROM sites_list WHERE owner=" + '"' + owner + '"')
    sites = {}
    [sites.update({k: v}) for k, v in cursor.fetchall()]

    for kk, vv in sites.items():
        articles = xmltodict.parse(requests.get(vv).text)
        articles_today = xmltodict.parse(requests.get(articles["sitemapindex"]["sitemap"][0]["loc"]).text)
        int1 = 0
        for x, y in articles_today.items():
            int1 += 1
            for i in y['url']:
                retvals = {}
                retvals[kk] = i['loc']
                q.put(retvals)
            if int1 == 1:
                break


# parser("batman")


def data_share(username):
    connect = connectionpool.get_connection()
    cursor = connect.cursor()

    cursor.execute("SELECT tg_chat, tg_id FROM users WHERE username=" + '"' + username + '"')
    info = cursor.fetchall()

    cursor.execute("SELECT keywords from keywords WHERE owner=" + '"' + username + '"')
    kwd = [''.join(i) for i in cursor.fetchall()]

    while not q.empty():
        value = q.get()
        print(q.qsize(), threading.current_thread().name)
        for k, v in value.items():
            header = urlparse(v).netloc
            for words in kwd:
                hashed_url = hashlib.md5(v.encode('utf-8')).hexdigest()
                if str(v).lower().__contains__(words):
                    html = requests.get(v).text
                    soup = BeautifulSoup(html, features="html.parser")
                    for script in soup(["script", "style"]):
                        script.extract()
                    text = soup.get_text()
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = '\n'.join(chunk for chunk in chunks if chunk)
                    cursor.execute("SELECT hashed_url FROM data WHERE hashed_url = " + '"' + hashed_url + '"')
                    result = cursor.fetchall()
                    if len(result) == 0:
                        sql = ("INSERT INTO data (owner, site_name, hashed_url, keywords, url)"
                               "VALUES (%s, %s, %s, %s, %s)")
                        val = (username, header, hashed_url, words, v)
                        cursor.execute(sql, val)
                        body = 'parse_mode=HTML&chat_id=' + info[0][1] + '&text=' + v
                        resp = requests.post('https://api.telegram.org/bot' + info[0][0] + '/sendMessage', params=body)


threads = []
mythreads = 5


start = time.time()


if __name__ == '__main__':
    for i in range(mythreads):
        t1 = threading.Thread(target=data_share, args=('batman', ), daemon=True)
        t1.start()
        threads.append(t1)
    for tr in threads:
        tr.join()


end = time.time()
print(end - start)
