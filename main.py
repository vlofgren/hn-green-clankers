from bs4 import BeautifulSoup

import requests
import sqlite3
import time
import statistics
import os.path
import re

def scrape_comments(link: str, depth: int):

    ret = []
    for i in range(0, depth):

        if link is None:
            break

        req = requests.get(link)
        soup = BeautifulSoup(req.text, 'html.parser')

        for comment in soup.find_all(class_='athing'):

            commtext = comment.find(class_='commtext')
            hnuser = comment.find(class_='hnuser')
            age = comment.find(class_='age')
            onstory = comment.find(class_='onstory')

            if commtext is not None:
                ret.append((comment['id'], onstory.find('a').text, age['title'], hnuser.text, commtext.text))

        link = 'https://news.ycombinator.com/'+soup.find(class_='morelink')['href']
        print(link)
        time.sleep(2)

    return ret

def fetch():

    con = sqlite3.connect("hncomments.db")
    cur = con.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS comments(source, id not null primary key, story, date, user, text)")

    cur.executemany("INSERT OR IGNORE INTO comments VALUES(?,?,?,?,?,?)",
        [("noob",)+data for data in scrape_comments('https://news.ycombinator.com/noobcomments', 25)])
    cur.executemany("INSERT OR IGNORE INTO comments VALUES(?,?,?,?,?,?)",
        [("new",)+data for data in scrape_comments('https://news.ycombinator.com/newcomments', 25)])
    con.commit()
    con.close()



if not os.path.isfile('hncomments.db'):
    fetch()

con = sqlite3.connect("hncomments.db")
cur = con.cursor()

cnt={"new": 0, "noob": 0}

aimarkers=['—', '•', '→',  '↔']
aiwords=['ai', 'llm', 'llms']

found_aimarkers={"new": 0, "noob": 0}
found_aiwords={"new": 0, "noob": 0}

comments = cur.execute("SELECT source, text, date FROM comments ORDER BY DATE desc").fetchall()

for (source,text,date) in comments:
    cnt[source]+=1

    for marker in aimarkers:
        if marker in text:
            found_aimarkers[source]+=1
            break

    words = set([word.lower() for word in re.split('[ ,.]+', text)])

    for word in aiwords:
        if word in words:
            found_aiwords[source]+=1
            break

print("AI or LLM mentions:")
for (source, count) in found_aiwords.items():
    print(f"{source}: {round(10000*count/cnt[source])/100}%") 

print("EM-dashes, arrows, similar:")
for (source, count) in found_aimarkers.items():
    print(f"{source}: {round(10000*count/cnt[source])/100}%") 
