#test clear_locks.py
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

from clear_locks import clear_locks
from reviewgramdb import connect_to_db, execute_insert, select_and_fetch_first_column

def test_clear_locks():
    timestamp = int(time.time())
    clear_locks()
    cleanupTime = int(os.getenv("LOCK_TIME"))
    assert cleanupTime != 0
    con = connect_to_db()
    with con:
        execute_insert(con, "INSERT `repo_locks`(`ID`,`TOKEN`, `CHAT_ID`,`TSTAMP`) VALUES (0, '111', 9999, 0)" , [])
    clear_locks()
    con = connect_to_db()
    with con:
        cnt = select_and_fetch_first_column(con, "SELECT COUNT(*) FROM `repo_locks` WHERE  " + str(timestamp) + " - TSTAMP >= " + str(cleanupTime) + "", [])
        assert cnt == 0