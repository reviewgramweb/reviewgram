# encoding=UTF-8
# Очищает истекшие ссылки на чаты, удаляя их ищ БД
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
import json
import os
import pymysql
import traceback
import time
import sys

path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(path + "/../")

from reviewgramdb import connect_to_db


def clear_locks():
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    timestamp = int(time.time())
    cleanupTime = int(os.getenv("LOCK_TIME"))
    con = connect_to_db()
    with con:
        cur = con.cursor()
        cur.execute("DELETE FROM `repo_locks` WHERE  " + str(timestamp) + " - TSTAMP >= " + str(cleanupTime) + "")
        con.commit()
        cur.close()


if __name__== "__main__":
    clear_locks()