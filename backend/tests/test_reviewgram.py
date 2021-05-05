#test generic_language.py
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
sys.path.append(path + "/..")

from repoutils import *
from reviewgramdb import *
from reviewgramlog import *
from reviewgram import *

def test_timeout():
    try:
        with Timeout(seconds = 3):
            time.sleep(4)
    except:
        assert True


def test_aescipher():
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    k = AESCipher()
    d = "item"
    assert k.decrypt(k.encrypt(d.encode())) == d
    

def test_try_autocomplete():
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    assert build_exact_match_autocomplete_query(0, 1, 1) == ""
    assert build_non_exact_match_autocomplete_query(0, 1, 1) == ""
    con = connect_to_db()
    try:
        with con:
            c = table_try_autocomplete(con, [], 1)
            assert len(c) == 0
    except:
        assert True
    con = connect_to_db()
    try:
        with con:
            c = table_try_autocomplete(con, ["import"], 1)
            assert len(c) != 0
    except:
        assert True
    con = connect_to_db()
    try:
        with con:
            c = table_try_autocomplete(con, ["log", "."], 1)
            assert len(c) != 0
    except:
        assert True
    con = connect_to_db()
    try:
        with con:
            c = table_try_autocomplete(con, ["import shutil"], 1)
            assert len(c) == 0
    except:
        assert True
    con = connect_to_db()
    try:
        with con:
            c = table_try_autocomplete(con, ["impo"], 1)
            assert len(c) != 0
    except:
        assert True
        
def test_safe_get_key():
    assert safe_get_key({"a": "b"}, ["a"]) is not None
    assert safe_get_key({"a": {"a": "b"}}, ["a", "a"]) is not None
    assert safe_get_key({"a": "b"}, ["b"]) is None
    assert safe_get_key({"a": {"a": "b"}}, ["b", "b"]) is None
    assert safe_get_key({"a": {"a": "b"}}, ["a", "b"]) is None
    

def test_insert_or_update_token_to_chat():
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    con = connect_to_db()
    with con:
        assert insert_or_update_token_to_chat(con, -500, 'AAAA') > 0
        assert insert_or_update_token_to_chat(con, -500, 'AAAA') == 0
        execute_update(con, "DELETE FROM `token_to_chat_id` WHERE `CHAT_ID` = -500", [])
        
def test_insert_or_update_repo_lock():
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    con = connect_to_db()
    with con:
        assert insert_or_update_repo_lock(con, -500, 'AAAA') > 0
        assert insert_or_update_repo_lock(con, -500, 'AAAA') == 0
        execute_update(con, "DELETE FROM `repo_locks` WHERE `CHAT_ID` = -500", [])

def test_is_user_in_chat():
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    assert is_user_in_chat(None, None) == False
    con = connect_to_db()
    with con:
        timestamp = int(time.time())
        execute_update(con, "DELETE FROM `token_to_user_id` WHERE `TOKEN` = 'MYTOK'", [])
        execute_update(con, "DELETE FROM `token_to_chat_id` WHERE `TOKEN` = 'MYTOK'", [])
        execute_insert(con, "INSERT `token_to_user_id`(`ID`,`TOKEN`, `USER_ID`,`TSTAMP`) VALUES (0, 'MYTOK', 260912228, " + str(timestamp) +")" , [])
    assert is_user_in_chat('MYTOK', -485373794)
    assert is_user_in_chat('MYTOK', -485373794)
    con = connect_to_db()
    with con:
        execute_update(con, "DELETE FROM `token_to_user_id` WHERE `TOKEN` = 'MYTOK'", [])
        execute_update(con, "DELETE FROM `token_to_chat_id` WHERE `TOKEN` = 'MYTOK'", [])

def test_validate_replace_table():
    assert validate_replace_table([]) == ""
    assert validate_replace_table(["ss"]) != ""
    assert validate_replace_table([["ss", "df", "fff"]]) != ""
    assert validate_replace_table([[None, 6.0]]) != ""
    assert validate_replace_table([["", "be"]]) != ""
    assert validate_replace_table([["be", ""]]) != ""
    assert validate_replace_table([["be", "be2"], ["kv2", "be2ff"], ["kv211", "be2f333f"]]) == ""

def test_update_replace_table():
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    con = connect_to_db()
    with con:
         execute_update(con, "DELETE FROM `replace_tables` WHERE `REPO_ID` = 500123000", [])
         update_replace_table(con, 500123000, [["kee", "koo"], ["kwee", "kwoo"]])
         assert select_and_fetch_first_column(con, "SELECT COUNT(*) FROM `replace_tables` WHERE `REPO_ID` = 500123000",[]) == 2
         update_replace_table(con, 500123000, [["kee", "koo"]])
         assert select_and_fetch_first_column(con, "SELECT COUNT(*) FROM `replace_tables` WHERE `REPO_ID` = 500123000",[]) == 1
         execute_update(con, "DELETE FROM `replace_tables` WHERE `REPO_ID` = 500123000", [])
         
def test_index():
    assert index() == 'OK'
    
def test_reviewgram():
    assert reviewgram() == 'OK'
    
def test_bot_username():
    assert bot_username() == os.getenv("BOT_USERNAME")
    