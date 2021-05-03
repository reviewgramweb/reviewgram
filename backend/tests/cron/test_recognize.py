#test recognize.py
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
import shutil

path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(path + "/../../cron")
sys.path.append(path + "/../../")

from recognize import select_and_perform_task,pid_exists
from reviewgramdb import connect_to_db, execute_insert,execute_update,select_and_fetch_first_column


def test_pid_exists():
    assert pid_exists(1)
    assert not pid_exists(2000000)

def test_recognize():
    timestamp = int(time.time())
    con = connect_to_db()
    rowId1 = 0
    rowId2 = 0
    with con:
        fileName = "/root/reviewgram/records/5b5d33a5-d8f1-4dea-b0a7-7167ff62a37a-1615124541.669079.ogg"
        langId = 1
        content = ''
        repoId = 1
        rowId1 = execute_insert(con, "INSERT INTO `recognize_tasks`(FILENAME, LANG_ID, CONTENT, REPO_ID) VALUES (%s, %s, %s, %s)", [fileName, langId, content, repoId])
        fileName = "/root/reviewgram/records/63ac4191-083f-4e37-a7c5-e8509a696530-1614002679.8371766.ogg"
        langId = 0
        content = ''
        repoId = 1
        rowId2 = execute_insert(con, "INSERT INTO `recognize_tasks`(FILENAME, LANG_ID, CONTENT, REPO_ID) VALUES (%s, %s, %s, %s)", [fileName, langId, content, repoId])
    assert rowId1 != 0
    assert rowId2 != 0
    select_and_perform_task()
    select_and_perform_task()
    select_and_perform_task()
    select_and_perform_task()
    con = connect_to_db()
    with con:
        data = select_and_fetch_first_column(con, "SELECT `RES` FROM `recognize_tasks` WHERE `ID` =" + str(rowId1), [])
        data = data.strip().replace("\r", "").replace("\n", "")
        assert data == "import os"
        data = select_and_fetch_first_column(con, "SELECT `RES` FROM `recognize_tasks` WHERE `ID` =" + str(rowId2), [])
        data = data.strip().replace("\r", "").replace("\n", "")
        assert data == "http"
