#test clear_tokens.py
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

from clear_tokens import clear_tokens
from reviewgramdb import connect_to_db, execute_insert,select_and_fetch_first_column

def test_clear_tokens():
    timestamp = int(time.time())
    clear_tokens()
    cleanupTime = int(os.getenv("TOKEN_CLEANUP_TIME"))
    assert cleanupTime != 0
    con = connect_to_db()
    with con:
        execute_insert(con, "INSERT `token_to_chat_id`(`ID`,`TOKEN`, `CHAT_ID`,`TSTAMP`) VALUES (0, '111', 9999, 0)" , [])
        execute_insert(con, "INSERT `token_to_user_id`(`ID`,`TOKEN`, `USER_ID`,`TSTAMP`) VALUES (0, '111', 9999, 0)" , [])
    clear_tokens()
    con = connect_to_db()
    with con:
        cnt = select_and_fetch_first_column(con, "SELECT COUNT(*) FROM `token_to_chat_id` WHERE `TOKEN` IN (SELECT `TOKEN` FROM `token_to_user_id` WHERE " + str(timestamp) + " - TSTAMP >= " + str(cleanupTime) + ")", [])
        assert cnt == 0
        cnt = select_and_fetch_first_column(con, "SELECT COUNT(*) FROM `token_to_user_id` WHERE " + str(timestamp) + " - TSTAMP >= " + str(cleanupTime), [])
        assert cnt == 0
