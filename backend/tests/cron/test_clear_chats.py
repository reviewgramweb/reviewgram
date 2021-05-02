#test clear_chats.py
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
import json
import os
import pymysql
import traceback
import time
import sys
import re
import subprocess

path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(path + "/../../cron")
sys.path.append(path + "/../../")

from clear_chats import clear_chats
from reviewgramdb import connect_to_db, execute_insert, select_and_fetch_first_column

def test_clear_chats():
    timestamp = int(time.time())
    clear_chats()
    cleanupTime = int(os.getenv("CHAT_CACHE_TOKEN_SECONDS"))
    assert cleanupTime != 0
    con = connect_to_db()
    with con:
        execute_insert(con, "INSERT `token_to_chat_id`(`ID`,`TOKEN`, `CHAT_ID`,`TSTAMP`) VALUES (0, '111', 9999, 0)" , [])
    clear_chats()
    con = connect_to_db()
    with con:
        cnt = select_and_fetch_first_column(con, "SELECT COUNT(*) FROM `token_to_chat_id` WHERE  " + str(timestamp) + " - TSTAMP >= " + str(cleanupTime) + "", [])
        assert cnt == 0