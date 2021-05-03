#test update_repos.py
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

from update_repos import try_print_error,execute_updating_repos
from reviewgramdb import connect_to_db, execute_insert,execute_update,select_and_fetch_first_column

class MockProcessResult:
    def __init__(self, so, se):
        self.stdout = so.encode("UTF-8")
        self.stderr = se.encode("UTF-8")

def test_try_print_error():
    buf = []
    try_print_error(MockProcessResult("1111", "4444"), buf)
    assert len(buf) == 0
    try_print_error(MockProcessResult("error: eggog", "ошибка: треш"), buf)
    assert len(buf) == 1
    assert buf[0] == "ошибка: треш"
    buf = []
    try_print_error(MockProcessResult("error: eggog", ""), buf)
    assert len(buf) == 1
    assert buf[0] == "error: eggog"

def test_update_repos():
    cwd = os.getcwd()
    con = connect_to_db()
    cache_data_id = 0
    with con:
        execute_insert(con, "INSERT INTO `repository_settings`(`ID`, `CHAT_ID`, `REPO_SITE`, `REPO_USER_NAME`, `REPO_SAME_NAME`, `USER`, `PASSWORD`, `LANG_ID`) VALUES (0, 1, 'github.com', 'reviewgramweb', 'reviewgram_tokenize', '', '', 1)" , [])
        cache_data_id = execute_insert(con, "INSERT INTO `repository_cache_storage_table`(`ID`, `REPO_SITE`, `REPO_USER_NAME`, `REPO_SAME_NAME`, `BRANCH_ID`, `TSTAMP`) VALUES (0, 'github.com', 'reviewgramweb', 'reviewgram_tokenize', 'test_cron', 0)" , [])
    assert cache_data_id != 0
    execute_updating_repos()
    con = connect_to_db()
    with con:
        tstamp = select_and_fetch_first_column(con, "SELECT TSTAMP FROM `repository_cache_storage_table` WHERE `ID` = " + str(cache_data_id) + "", []);
        assert tstamp > 0
        execute_update(con, "UPDATE `repository_cache_storage_table` SET `TSTAMP` = 0 WHERE `ID` = " + str(cache_data_id) + "", [])
    execute_updating_repos()
    assert os.path.isdir("reviewgramweb_reviewgram_tokenize_test_cron")
    os.chdir("reviewgramweb_reviewgram_tokenize_test_cron")
    result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = result.stdout.decode("UTF-8").replace("\n", "").replace("\r", "")
    assert out == "test_cron"
    result = subprocess.run(['git', 'rev-parse', '--verify', 'HEAD'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = result.stdout.decode("UTF-8").replace("\n", "").replace("\r", "")
    assert out == "6299476ecd1b39c4b48392a8afee766bc0085e58"
    os.chdir("..")
    if (os.path.isdir("reviewgramweb_reviewgram_tokenize_test_cron")):
        shutil.rmtree("reviewgramweb_reviewgram_tokenize_test_cron")
    con = connect_to_db()
    with con:
        execute_update(con, "DELETE FROM `repository_settings` WHERE `CHAT_ID` = 1", []);
        execute_update(con, "DELETE FROM `repository_cache_storage_table` WHERE `ID` = " + str(cache_data_id) + "", []);

    os.chdir(cwd)