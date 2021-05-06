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
import base64

path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(path + "/..")

from repoutils import *
from reviewgramdb import *
from reviewgramlog import *
from reviewgram import *
from werkzeug.exceptions import NotFound

request = {}

class DictWrap:
    def __init__(self, o):
        self.o = o
    
    def get(self, a):
        if a in self.o:
            return self.o[a]
        else:
            return None

class JSONWithArgs:
    def __init__(self, json, args):
        self.json = json
        self.args = args

class RequestValues:
    def __init__(self, o):
        self.values = o


class MockFile:
    def __init__(self, size):
        self.size = size

    def seek(self, a1, a2):
        return

    def tell(self):
        return self.size

    def save(self, filename):
        fileObject = open(filename, 'wb')
        fileObject.close()
        
class FormWithFiles:
    def __init__(self, values, file):
        self.form = DictWrap(values)
        self.files = DictWrap({"record": file})

def test_index():
    assert index() == 'OK'
    
def test_reviewgram():
    assert reviewgram() == 'OK'
    
def test_bot_username():
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    assert bot_username() == os.getenv("BOT_USERNAME")


def test_bot_api():
    global request
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    try:
        request = JSONWithArgs(None, DictWrap({}))
        result = imp_bot_api(request)
        assert False
    except NotFound:
        assert True
    try:
        request = JSONWithArgs(None, DictWrap({'token':  os.getenv("BOT_WEBHOOK_TOKEN")}))
        result = imp_bot_api(request)
        assert False
    except NotFound:
        assert True
    try:
        request = JSONWithArgs({}, DictWrap({'token':  os.getenv("BOT_WEBHOOK_TOKEN")}))
        result = imp_bot_api(request)
        assert result == 'ERROR'
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({"message": {"from": {"id": 2}, "text": "/start"}}, DictWrap({'token':  os.getenv("BOT_WEBHOOK_TOKEN")}))
        result = imp_bot_api(request)
        assert result == "OK"
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({"message": {"from": {"id": 100}, "text": "/info"}}, DictWrap({'token':  os.getenv("BOT_WEBHOOK_TOKEN")}))
        result = imp_bot_api(request)
        assert result == "ERROR"
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({"message": {"from": {"id": 100}, "text": base64.b64encode("MYTOK".encode("UTF-8"))}}, DictWrap({'token':  os.getenv("BOT_WEBHOOK_TOKEN")}))
        result = imp_bot_api(request)
        assert result == "OK"
        con = connect_to_db()
        with con:
            execute_update(con, "DELETE FROM `token_to_user_id` WHERE `TOKEN` = 'MYTOK'", [])
            execute_update(con, "DELETE FROM `token_to_chat_id` WHERE `TOKEN` = 'MYTOK'", [])
    except NotFound:
        assert False


def test_register_chat_id_for_token():
    global request
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    try:
        request = RequestValues(DictWrap({}))
        result = imp_register_chat_id_for_token(request)
        assert False
    except NotFound:
        assert True
    try:
        request = RequestValues(DictWrap({"chatId": -40, "uuid": "NOTEXISTS"}))
        result = imp_register_chat_id_for_token(request)
        assert False
    except NotFound:
        assert True
    try: 
        userId = 260912228
        chatId = -485373794
        request = JSONWithArgs({"message": {"from": {"id": userId}, "text": base64.b64encode("MYTOK".encode("UTF-8"))}}, DictWrap({'token':  os.getenv("BOT_WEBHOOK_TOKEN")}))
        result = imp_bot_api(request)
        result = imp_bot_api(request)        
        request = RequestValues(DictWrap({"chatId": chatId, "uuid": "MYTOK"}))
        result = imp_register_chat_id_for_token(request)
        assert result == "OK"
        con = connect_to_db()
        with con:
            execute_update(con, "DELETE FROM `token_to_user_id` WHERE `TOKEN` = 'MYTOK'", [])
            execute_update(con, "DELETE FROM `token_to_chat_id` WHERE `TOKEN` = 'MYTOK'", [])        
    except NotFound:
        assert True
        
def test_set_repo_settings():
    global request
    toggle_nowrap()
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    con = connect_to_db()
    with con:
        timestamp = int(time.time())
        execute_update(con, "DELETE FROM `token_to_user_id` WHERE `TOKEN` = 'MYTOK'", [])
        execute_update(con, "DELETE FROM `token_to_chat_id` WHERE `TOKEN` = 'MYTOK'", [])
        execute_insert(con, "INSERT `token_to_user_id`(`ID`,`TOKEN`, `USER_ID`,`TSTAMP`) VALUES (0, 'MYTOK', 500, " + str(timestamp) +")" , [])
        execute_insert(con, "INSERT `token_to_chat_id`(`ID`,`TOKEN`, `CHAT_ID`,`TSTAMP`) VALUES (0, 'MYTOK', -500, " + str(timestamp) +")" , [])
    try:
        request = JSONWithArgs({}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert False
    except NotFound:
        assert True
    try:
        request = JSONWithArgs({'chatId': -501, 'uuid': 'UNKNOWN'}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert False
    except NotFound:
        assert True
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK'}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) != 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK', "repoUserName": ""}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) != 0
    except NotFound:
        assert False        
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK', "repoUserName": "test"}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) != 0
    except NotFound:
        assert False      
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK', "repoUserName": "test", "repoSameName": ""}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) != 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK', "repoUserName": "test", "repoSameName": "item"}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) != 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK', "repoUserName": "test", "repoSameName": "item", "user": ""}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) != 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK', "repoUserName": "test", "repoSameName": "item", "user": "ddd"}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) != 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK', "repoUserName": "test", "repoSameName": "item", "user": "ddd", "password": ""}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) != 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK', "repoUserName": "test", "repoSameName": "item", "user": "ddd", "password": "kfc"}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) != 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK', "repoUserName": "test", "repoSameName": "item", "user": "ddd", "password": base64.b64encode("MYTOK".encode("UTF-8"))}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) != 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK', "repoUserName": "test", "repoSameName": "item", "user": "ddd", "password": base64.b64encode("MYTOK".encode("UTF-8")), "table": {}}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) != 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK', "repoUserName": "test", "repoSameName": "item", "user": "ddd", "password": base64.b64encode("MYTOK".encode("UTF-8")), "table": []}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) != 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK', "repoUserName": "test", "repoSameName": "item", "user": "ddd", "password": base64.b64encode("MYTOK".encode("UTF-8")), "table": ["ddd"]}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) != 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK', "repoUserName": "test", "repoSameName": "item", "user": "ddd", "password": base64.b64encode("MYTOK".encode("UTF-8")), "table": [], "langId": "ebc"}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) != 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK', "repoUserName": "test", "repoSameName": "item", "user": "ddd", "password": base64.b64encode("MYTOK".encode("UTF-8")), "table": [], "langId": "14"}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) != 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK', "repoUserName": "test", "repoSameName": "item", "user": "ddd", "password": base64.b64encode("MYTOK".encode("UTF-8")), "table": [], "langId": "1"}, DictWrap({}))
        result = imp_set_repo_settings(request)
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) == 0
    except NotFound:
        assert False
    con = connect_to_db()
    with con:
        execute_update(con, "DELETE FROM `token_to_user_id` WHERE `TOKEN` = 'MYTOK'", [])
        execute_update(con, "DELETE FROM `token_to_chat_id` WHERE `TOKEN` = 'MYTOK'", [])
        execute_update(con, "DELETE FROM `repository_settings` WHERE `REPO_USER_NAME` = 'test' AND `USER` = 'ddd'", [])
        
def test_get_repo_settings():
    global request
    toggle_nowrap()
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    con = connect_to_db()
    with con:
        timestamp = int(time.time())
        execute_update(con, "DELETE FROM `token_to_user_id` WHERE `TOKEN` = 'MYTOK'", [])
        execute_update(con, "DELETE FROM `token_to_chat_id` WHERE `TOKEN` = 'MYTOK'", [])
        execute_insert(con, "INSERT `token_to_user_id`(`ID`,`TOKEN`, `USER_ID`,`TSTAMP`) VALUES (0, 'MYTOK', 500, " + str(timestamp) +")" , [])
        execute_insert(con, "INSERT `token_to_chat_id`(`ID`,`TOKEN`, `CHAT_ID`,`TSTAMP`) VALUES (0, 'MYTOK', -500, " + str(timestamp) +")" , [])
    try:
        request = RequestValues(DictWrap({"chatId": -501, "uuid": "UNKNOWN"}))
        result = imp_get_repo_settings(request)
        assert False
    except NotFound:
        assert True
    try:
        request = RequestValues(DictWrap({"chatId": -500, "uuid": "MYTOK", "withTable": "Y"}))
        result = imp_get_repo_settings(request)
        assert len(result["site"]) == 0
        assert len(result["repo_user_name"]) == 0
        assert len(result["repo_same_name"]) == 0
        assert len(result["user"]) == 0
        assert len(result["password"]) == 0
        assert result["langId"] == 1
        assert result["id"] == 0
        assert len(result["table"]) == 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({'chatId': -500, 'uuid': 'MYTOK', "repoUserName": "test", "repoSameName": "item", "user": "ddd", "password": base64.b64encode("MYTOK".encode("UTF-8")), "table": [["puu", "pex"]], "langId": "1"}, DictWrap({}))
        result = imp_set_repo_settings(request)
        assert not (result["error"] is  None)
        assert len(result["error"]) == 0
    except NotFound:
        assert False
    try:
        request = RequestValues(DictWrap({"chatId": -500, "uuid": "MYTOK"}))
        result = imp_get_repo_settings(request)
        assert len(result["site"]) != 0
        assert len(result["repo_user_name"]) != 0
        assert len(result["repo_same_name"]) != 0
        assert len(result["user"]) != 0
        assert len(result["password"]) != 0
        assert result["langId"] == 1
        assert result["id"] != 0
        assert len(result["table"]) == 0
    except NotFound:
        assert False
    try:
        request = RequestValues(DictWrap({"chatId": -500, "uuid": "MYTOK", "withTable": "Y"}))
        result = imp_get_repo_settings(request)
        assert len(result["site"]) != 0
        assert len(result["repo_user_name"]) != 0
        assert len(result["repo_same_name"]) != 0
        assert len(result["user"]) != 0
        assert len(result["password"]) != 0
        assert result["langId"] == 1
        assert result["id"] != 0
        assert len(result["table"]) != 0
    except NotFound:
        assert False
    con = connect_to_db()
    with con:
        execute_update(con, "DELETE FROM `token_to_user_id` WHERE `TOKEN` = 'MYTOK'", [])
        execute_update(con, "DELETE FROM `token_to_chat_id` WHERE `TOKEN` = 'MYTOK'", [])
        execute_update(con, "DELETE FROM `repository_settings` WHERE `REPO_USER_NAME` = 'test' AND `USER` = 'ddd'", [])
        
def test_try_lock():
    global request
    toggle_nowrap()
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    con = connect_to_db()
    with con:
        timestamp = int(time.time())
        execute_update(con, "DELETE FROM `token_to_user_id` WHERE `TOKEN` = 'MYTOK'", [])
        execute_update(con, "DELETE FROM `token_to_chat_id` WHERE `TOKEN` = 'MYTOK'", [])
        execute_insert(con, "INSERT `token_to_user_id`(`ID`,`TOKEN`, `USER_ID`,`TSTAMP`) VALUES (0, 'MYTOK', 500, " + str(timestamp) +")" , [])
        execute_insert(con, "INSERT `token_to_chat_id`(`ID`,`TOKEN`, `CHAT_ID`,`TSTAMP`) VALUES (0, 'MYTOK', -500, " + str(timestamp) +")" , [])
        execute_insert(con, "INSERT `token_to_user_id`(`ID`,`TOKEN`, `USER_ID`,`TSTAMP`) VALUES (0, 'PITOK', 501, " + str(timestamp) +")" , [])
        execute_insert(con, "INSERT `token_to_chat_id`(`ID`,`TOKEN`, `CHAT_ID`,`TSTAMP`) VALUES (0, 'PITOK', -500, " + str(timestamp) +")" , [])

    try:
        request = RequestValues(DictWrap({"chatId": -501, "uuid": "UNKNOWN"}))
        result = imp_try_lock(request)
        assert False
    except NotFound:
        assert True
    try:
        request = RequestValues(DictWrap({"chatId": -500, "uuid": "MYTOK"}))
        result = imp_try_lock(request)
        assert result["locked"] == False
    except NotFound:
        assert True
    try:
        request = RequestValues(DictWrap({"chatId": -500, "uuid": "PITOK"}))
        result = imp_try_lock(request)
        assert result["locked"] == True
    except NotFound:
        assert True
    con = connect_to_db()
    with con:
        execute_update(con, "DELETE FROM `token_to_user_id` WHERE `TOKEN` = 'MYTOK'", [])
        execute_update(con, "DELETE FROM `token_to_chat_id` WHERE `TOKEN` = 'MYTOK'", [])
        execute_update(con, "DELETE FROM `token_to_user_id` WHERE `TOKEN` = 'PITOK'", [])
        execute_update(con, "DELETE FROM `token_to_chat_id` WHERE `TOKEN` = 'PITOK'", [])        
        execute_update(con, "DELETE FROM `repo_locks` WHERE `TOKEN` = 'MYTOK'", [])
        execute_update(con, "DELETE FROM `repo_locks` WHERE `TOKEN` = 'PITOK'", [])


def test_check_syntax():
    global request
    toggle_nowrap()
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    try:
        request = JSONWithArgs(None, DictWrap({}))
        result = imp_check_syntax(request)
        assert not (result["errors"] is  None)
        assert len(result["errors"]) == 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({}, DictWrap({}))
        result = imp_check_syntax(request)
        assert not (result["errors"] is  None)
        assert len(result["errors"]) == 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({"filename": "a.py", "content": "aaaa", "start": 0, "end": 1, "langId": 15}, DictWrap({}))
        result = imp_check_syntax(request)
        assert not (result["errors"] is  None)
        assert len(result["errors"]) == 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({"filename": "a.py", "content": base64.b64encode("a = a + 1".encode("UTF-8")), "start": 0, "end": 1, "langId": 15}, DictWrap({}))
        result = imp_check_syntax(request)
        assert not (result["errors"] is  None)
        assert len(result["errors"]) == 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({"filename": "a.py", "content": base64.b64encode("a = a +".encode("UTF-8")), "start": 0, "end": 1, "langId": 1}, DictWrap({}))
        result = imp_check_syntax(request)
        assert not (result["errors"] is  None)
        assert len(result["errors"]) != 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({"filename": "a.py", "content": base64.b64encode("a = 2 + 2".encode("UTF-8")), "start": 0, "end": 1, "langId": 1}, DictWrap({}))
        result = imp_check_syntax(request)
        assert not (result["errors"] is  None)
        assert len(result["errors"]) == 0
    except NotFound:
        assert False
        
def test_get_autocompletions():
    global request
    toggle_nowrap()
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    try:
        request = JSONWithArgs(None, DictWrap({}))
        result = imp_get_autocompletions(request)
        assert len(result) == 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({}, DictWrap({}))
        result = imp_get_autocompletions(request)
        assert len(result) == 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({"tokens": {}, "content": "55", "line": 1, "position": 1, "chatId":  -485373794, "branchId": "master", "langId": 15}, DictWrap({}))
        result = imp_get_autocompletions(request)
        assert len(result) == 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({"tokens": [], "content": "55", "line": 1, "position": 1,"chatId":  -485373794, "branchId": "master", "langId": 15}, DictWrap({}))
        result = imp_get_autocompletions(request)
        assert len(result) == 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({"tokens": [], "content": base64.b64encode("a = 2 + 2".encode("UTF-8")), "line": 1, "position": 1,"chatId":  -485373794, "branchId": "master", "langId": 15}, DictWrap({}))
        result = imp_get_autocompletions(request)
        assert len(result) == 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({"tokens": ["import"], "content": base64.b64encode("import ".encode("UTF-8")), "line": 1, "position": 7,"chatId":  -485373794, "branchId": "master", "langId": 1}, DictWrap({}))
        result = imp_get_autocompletions(request)
        assert len(result) != 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({"tokens": ["import", "o"], "content": base64.b64encode("import o".encode("UTF-8")), "line": 1, "position": 9, "chatId":  -485373794, "branchId": "master", "langId": 1}, DictWrap({}))
        result = imp_get_autocompletions(request)
        assert len(result) != 0
    except NotFound:
        assert False
    try:
        request = JSONWithArgs({"tokens": ["import", "dee", ".", "doo"], "content": base64.b64encode("import dee.doo".encode("UTF-8")), "line": 1,"position": 12, "chatId":  -485373794, "branchId": "master", "langId": 1}, DictWrap({}))
        result = imp_get_autocompletions(request)
        assert len(result) == 0
    except NotFound:
        assert False


def test_start_recognizing():
    global request
    toggle_nowrap()
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    repoId = 0;        
    try:
        request = FormWithFiles({}, None)
        result = imp_start_recognizing(request)
        assert not ("id" in result)
    except NotFound:
        assert False
    try:
        request = FormWithFiles({"repoId": "errr"}, None)
        result = imp_start_recognizing(request)
        assert not ("id" in result)
    except NotFound:
        assert False
    try:
        request = FormWithFiles({"repoId": 0, "content": None}, None)
        result = imp_start_recognizing(request)
        assert not ("id" in result)
    except NotFound:
        assert False
    try:
        request = FormWithFiles({"repoId": 0, "content": "222", "langId": "1"}, None)
        result = imp_start_recognizing(request)
        assert not ("id" in result)
    except NotFound:
        assert False
    try:
        request = FormWithFiles({"repoId": 0, "content": "222", "langId": "1"}, MockFile(500 * 1024 * 1024))
        result = imp_start_recognizing(request)
        assert not ("id" in result)
    except NotFound:
        assert False
    try:
        request = FormWithFiles({"repoId": 0, "content": "222", "langId": None}, MockFile(1024))
        result = imp_start_recognizing(request)
        assert result["id"] > 0
        print(result)
        ddd = imp_recognizing_status(RequestValues(DictWrap(result)))
        assert "status" in ddd
        time.sleep(3)
        con = connect_to_db()
        with con:
            execute_update(con, "DELETE FROM `recognize_tasks` WHERE `ID` = " + str(result["id"]), [])
    except NotFound:
        assert False
    try:
        request = FormWithFiles({"repoId": 0, "content": "222", "langId": "1"}, MockFile(1024))
        result = imp_start_recognizing(request)
        assert result["id"] > 0
        print(result)
        ddd = imp_recognizing_status(RequestValues(DictWrap(result)))
        assert "status" in ddd
        time.sleep(3)
        con = connect_to_db()
        with con:
            execute_update(con, "DELETE FROM `recognize_tasks` WHERE `ID` = " + str(result["id"]), [])
    except NotFound:
        assert False
        
def test_recognizing_status():
    global request
    toggle_nowrap()
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    try:
        r = imp_recognizing_status(RequestValues(DictWrap({})))
        assert r["status"] == "pending"
    except NotFound:
        assert False
    try:
        r = imp_recognizing_status(RequestValues(DictWrap({"id": "er"})))
        assert r["status"] == "pending"
    except NotFound:
        assert False
    try:
        r = imp_recognizing_status(RequestValues(DictWrap({"id": "5000000000"})))
        assert r["status"] == "pending"
    except NotFound:
        assert False
