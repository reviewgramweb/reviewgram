# encoding=UTF-8
# Очищает истекшие ссылки на чаты, удаляя их ищ БД
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
import json
import os
import pymysql
import traceback
import time

path = os.path.dirname(os.path.abspath(__file__))
env_path = Path(path + "/../") / '.env'
load_dotenv(dotenv_path=env_path)
timestamp = int(time.time())
cleanupTime = int(os.getenv("CHAT_CACHE_TOKEN_SECONDS"))
con = pymysql.connect(os.getenv("MYSQL_HOST"), os.getenv("MYSQL_USER"), os.getenv("MYSQL_PASSWORD"), os.getenv("MYSQL_DB"))
with con:
    cur = con.cursor()
    cur.execute("DELETE FROM `token_to_chat_id` WHERE  " + str(timestamp) + " - TSTAMP >= " + str(cleanupTime) + "")
    con.commit()
    cur.close()
