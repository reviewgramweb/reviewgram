from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, request, jsonify, abort
from dotenv import load_dotenv, find_dotenv
from datetime import datetime

from Crypto import Random
from Crypto.Cipher import AES

import struct
import logging
import json
import os
import pymysql
import base64
import traceback
import requests
import time
import tempfile
import subprocess
import re
import jedi

load_dotenv(find_dotenv())

bot_webhook_token = os.getenv("BOT_WEBHOOK_TOKEN")
bot_api_token  = os.getenv("BOT_API_TOKEN")

app = Flask(__name__)


# Класс для шифрования данных
class AESCipher(object):
    def __init__(self):
        self.bs = AES.block_size
        self.key = os.getenv("AES_SECRET_KEY")

    def _pad(self, s):
        return s.decode("utf-8") + (self.bs - len(s) % self.bs) * '0'

    def encrypt(self, raw):
        raw_size = len(raw)
        raw_bytes = self._pad(raw)
        raw_size_bytes = struct.pack('<i', raw_size)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + raw_size_bytes + cipher.encrypt(raw_bytes))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:self.bs]
        raw_size = struct.unpack('<i', enc[self.bs:self.bs + 4])[0]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        raw_bytes = cipher.decrypt(enc[self.bs + 4:])
        raw = raw_bytes[:raw_size].decode('utf_8')
        return raw

# Формирует имя папки репозитория
def repo_folder_name(repoUserName, repoName, branchId):
    return repoUserName + "_" + repoName + "_" + re.sub(r"[^0-9a-zA-Z_]", "__", branchId)


# существует ли папка репозитория
def is_repo_folder_exists(repoUserName, repoName, branchId):
    folderName = repo_folder_name(repoUserName, repoName, branchId)
    path = os.path.dirname(os.path.abspath(__file__))
    fullPath = path + "/repos/" + folderName + "/.git/"
    return os.path.isdir(fullPath)

# полная папка репозитория
def full_repo_folder_name(repoUserName, repoName, branchId):
    folderName = repo_folder_name(repoUserName, repoName, branchId)
    path = os.path.dirname(os.path.abspath(__file__))
    fullPath = path + "/repos/" + folderName + "/"
    return fullPath

# Пытается вставить задачу на клонирование репозитория
def try_insert_cloning_repo_task(con, repoSite, repoUserName, repoSameName, branchId):
    result = select_and_fetch_one(con, "SELECT * FROM `repository_cache_storage_table` WHERE `REPO_SITE` = %s AND `REPO_USER_NAME` = %s  AND `REPO_SAME_NAME` = %s  AND `BRANCH_ID` = %s LIMIT 1" , [repoSite, repoUserName, repoSameName, branchId])
    if (result is None):
        execute_update(con, "INSERT INTO `repository_cache_storage_table`(REPO_SITE, REPO_USER_NAME, REPO_SAME_NAME, BRANCH_ID, TSTAMP) VALUES (%s, %s, %s, %s, 0)", [repoSite, repoUserName, repoSameName, branchId])


#  Делает автодополнение через jedi, используя даннные папки и содержимое
def jedi_try_autocomplete_with_folder(content, line, position, folderName):
    result = []
    try:
        script = jedi.Script(content, line, position, folderName)
        completions = script.completions()
    except jedi.NotFoundError:
        completions = []
    for completion in completions:
        result.append({
            'append_type': 'no_space'
            'complete': completion.complete, # What to add
            'name_with_symbols': completion.name_with_symbols # A displayable name
        })
    return result

# Пытается сделать автодополнение через jedi,  добавляя репозиторий на клонирование в процессе
def jedi_try_autocomplete(con, chatId, branchId, content, line, position):
    try:
        result = select_and_fetch_one(con, "SELECT REPO_SITE, REPO_USER_NAME, REPO_SAME_NAME FROM `repository_settings` WHERE `CHAT_ID` = " + str(chatId) + " LIMIT 1"  ,[])
        if (result is not None):
            repoSite = result[0]
            repoUserName = result[1]
            repoSameName = result[2]
            result = []
            if (is_repo_folder_exists(repoUserName, repoSameName, branchId)):
                folderName = full_repo_folder_name(repoUserName, repoSameName, branchId)
                result = jedi_try_autocomplete_with_folder(content, line, position, folderName)
            else:
                try_insert_cloning_repo_task(con, repoSite, repoUserName, repoSameName, branchId)
                result =  jedi_try_autocomplete_with_folder(content, line, position, ".")
            return result
        else:
            return []
    except Exception as e:
        print(traceback.format_exc())
        append_to_log("/reviewgram/jedi_try_autocomplete: Exception " + traceback.format_exc())
        return []

# Получение вложенных данных из словаря
def safe_get_key(dict, keys):
    tmp = dict
    for key in keys:
        if key in tmp:
            tmp = tmp[key]
        else:
            return None
    return tmp

# Соединение с БД
def connect_to_db():
    return pymysql.connect(os.getenv("MYSQL_HOST"), os.getenv("MYSQL_USER"), os.getenv("MYSQL_PASSWORD"), os.getenv("MYSQL_DB"))

# Получение первой строки по запросу из БД
def select_and_fetch_one(con, query, params):
    cur = con.cursor()
    cur.execute(query, params)
    result = cur.fetchone()
    cur.close()
    return result

# Получение первой колонки и строки по запросу из БД
def select_and_fetch_first_column(con, query, params):
    row  = select_and_fetch_one(con, query, params)
    if (row is None):
        return None
    else:
        return row[0]

# Выполнение запроса к БД
def execute_update(con, query, params):
    cur = con.cursor()
    cur.execute(query, params)
    con.commit()
    cur.close()

# Запись данных в лог
def append_to_log(text):
    date_time_now = datetime.now()
    str_date_time = date_time_now.strftime("%d-%m-%Y (%H:%M:%S)")
    text_file = open(os.getenv("APP_FOLDER") + "/log.txt", "a")
    text_file.write("["  + str_date_time + "]" + text + "\n")
    text_file.close()

# Вставляет или обновляет соотношение токена с чатом
def  insert_or_update_token_to_chat(con, chatId, uuid):
    query = "SELECT COUNT(*) AS CNT FROM `token_to_chat_id` WHERE `TOKEN` = %s AND `CHAT_ID` = %s"
    countRows = select_and_fetch_first_column(con, query, [uuid, chatId])
    if (countRows > 0):
        execute_update(con, "UPDATE `token_to_chat_id` SET TSTAMP = UNIX_TIMESTAMP(NOW()) WHERE TOKEN = %s AND CHAT_ID = %s", [uuid, chatId])
    else:
        execute_update(con, "INSERT INTO `token_to_chat_id`(TOKEN, CHAT_ID, TSTAMP) VALUES (%s, %s, UNIX_TIMESTAMP(NOW()))", [uuid, chatId])


def  insert_or_update_repo_lock(con, chatId, uuid):
    query = "SELECT COUNT(*) AS CNT FROM `repo_locks` WHERE `CHAT_ID` = %s"
    countRows = select_and_fetch_first_column(con, query, [chatId])
    if (countRows > 0):
        execute_update(con, "UPDATE `repo_locks` SET TSTAMP = UNIX_TIMESTAMP(NOW()), TOKEN = %s WHERE CHAT_ID = %s", [uuid, chatId])
    else:
        execute_update(con, "INSERT INTO `repo_locks`(TOKEN, CHAT_ID, TSTAMP) VALUES (%s, %s, UNIX_TIMESTAMP(NOW()))", [uuid, chatId])

# Находится ли пользователь в чате и все связанные с этим проверки
def is_user_in_chat(uuid, chatId):
    try:
        if ((chatId is not None) and (uuid is not None)):
            chatId = int(chatId)
            con = connect_to_db()
            with con:
                timestamp = int(time.time())
                tokenCleanupTime = int(os.getenv("TOKEN_CLEANUP_TIME")) * 60
                chatCleanupTime = int(os.getenv("CHAT_CACHE_TOKEN_SECONDS"))
                query = "SELECT USER_ID FROM `token_to_user_id` WHERE `TOKEN` = %s AND " + str(timestamp) + " - TSTAMP <= " + str(tokenCleanupTime) + " LIMIT 1"
                userId = select_and_fetch_first_column(con, query, [uuid])
                if (userId is not None):
                    query = "SELECT ID FROM `token_to_chat_id` WHERE `TOKEN` = %s AND `CHAT_ID` = %s AND " + str(timestamp) + " - TSTAMP <= " + str(chatCleanupTime) + " LIMIT 1"
                    row = select_and_fetch_first_column(con, query, [uuid, chatId])
                    if (row is None):
                        url = "https://api.telegram.org/bot" + os.getenv("BOT_API_TOKEN") + "/getChatMember"
                        append_to_log("/reviewgram/register_chat_id_for_token/: " + url)
                        params = {'user_id': userId,  'chat_id' : chatId}
                        response = requests.get(url, params=params)
                        json_response = response.json()
                        if (json_response is None):
                            append_to_log("/reviewgram/register_chat_id_for_token/: unable to parse response")
                            return False
                        else:
                            if (json_response["ok"] is True):
                                insert_or_update_token_to_chat(con, chatId, uuid)
                                return True
                            else:
                                append_to_log("/reviewgram/register_chat_id_for_token/: TG API reported that user is not in chat")
                                return False
                    else:
                        return True
                else:
                    append_to_log("/reviewgram/register_chat_id_for_token/: user token not found")
                    return False
                return True
        else:
            append_to_log("/reviewgram/register_chat_id_for_token/: no data")
            return False
    except Exception as e:
        append_to_log("/reviewgram/register_chat_id_for_token/: Exception " + traceback.format_exc())
        return False


# Группирует ошибки из pyflakes в кортежи (строка, список ошибок)
def build_error_line_groups(fileName, errorContent):
    errorContentLines = errorContent.split("\n")
    errorsByLines = []
    for line in errorContentLines:
        if (line.startswith(fileName)):
            lineWithoutName = line[(len(fileName)+1):]
            secondColonPos = lineWithoutName.index(":")
            numberAsString = lineWithoutName[:secondColonPos]
            lineNo = int(numberAsString)
            tuple = (lineNo, [line])
            errorsByLines.append(tuple)
        else:
            if (len(errorsByLines) != 0):
                errorsByLines[len(errorsByLines) - 1][1].append(line)
    return errorsByLines

# Запускает PyFlakes
def run_pyflakes(name, content, start, end):
    with tempfile.NamedTemporaryFile() as temp:
        temp.write(content.encode("UTF-8"))
        temp.flush()
        fileName = temp.name
        result = subprocess.run(['pyflakes', fileName], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        errorContent = result.stderr.decode("UTF-8")
        errors = build_error_line_groups(fileName, errorContent)
        ownErrors = [error for error in errors if ((error[0] >= start) and (error[0] <= end))]
        ownErrors = list(map(lambda x:"\n".join(x[1]), ownErrors))
        ownErrors = "\n".join(ownErrors).replace(fileName, name)
        return ownErrors

@app.route('/')
def index():
    return 'OK'


@app.route('/reviewgram/')
def reviewgram():
    return 'OK'

@app.route('/reviewgram/bot_username/')
def bot_username():
    return os.getenv("BOT_USERNAME")

@app.route('/reviewgram/bot/', methods=['POST', 'GET'])
def bot_api():
    if request.args.get('token') != bot_webhook_token:
        abort(404)
    data = request.json
    if data is None:
        abort(404)
    try:
        userId = safe_get_key(data, ["message", "from", "id"])
        message = safe_get_key(data, ["message", "text"])
        if ((userId is not None) and (message is not None)):
            decoded = base64.b64decode(message)
            con = connect_to_db()
            with con:
                countRows = select_and_fetch_first_column(con, "SELECT COUNT(*) AS CNT FROM `token_to_user_id` WHERE `TOKEN` = %s", [decoded])
                if (countRows > 0):
                    execute_update(con, "UPDATE `token_to_user_id` SET USER_ID = %s, TSTAMP = UNIX_TIMESTAMP(NOW()) WHERE TOKEN = %s", [userId, decoded])
                else:
                    execute_update(con, "INSERT INTO `token_to_user_id`(USER_ID, TOKEN, TSTAMP) VALUES (%s, %s, UNIX_TIMESTAMP(NOW()))", [userId, decoded])
        else:
            append_to_log("/reviewgram/bot: no data")
            abort(404)
    except Exception as e:
        append_to_log("/reviewgram/bot: Exception " + traceback.format_exc())
        abort(404)
    return 'OK'


@app.route('/reviewgram/register_chat_id_for_token/', methods=['POST'])
def register_chat_id_for_token():
    chatId = request.values.get("chatId")
    uuid = request.values.get("uuid")
    if (is_user_in_chat(uuid, chatId)):
        return 'OK'
    else:
        abort(404)


@app.route('/reviewgram/get_repo_settings/')
def get_repo_settings():
    chatId = request.values.get("chatId")
    uuid = request.values.get("uuid")
    if (is_user_in_chat(uuid, chatId)):
        con = connect_to_db()
        with con:
            row = select_and_fetch_one(con, "SELECT REPO_SITE, REPO_USER_NAME, REPO_SAME_NAME, USER, PASSWORD FROM `repository_settings` WHERE `CHAT_ID` = %s LIMIT 1", [chatId])
            if (row is not None):
                password = ""
                if (len(row[4]) > 0):
                    c = AESCipher()
                    password = c.decrypt(row[4])
                return jsonify({"site": row[0], "repo_user_name": row[1], "repo_same_name": row[2], "user": row[3], "password": base64.b64encode(password.encode('UTF-8')).decode('UTF-8')})
            else:
                return jsonify({"site": "", "repo_user_name" : "", "repo_same_name": "", "user": "", "password": ""})
    else:
        abort(404)


@app.route('/reviewgram/set_repo_settings/', methods=['POST'])
def set_repo_settings():
    chatId = request.values.get("chatId")
    uuid = request.values.get("uuid")
    repoUserName = request.values.get("repoUserName")
    repoSameName = request.values.get("repoSameName")
    user = request.values.get("user")
    password = request.values.get("password")
    if (is_user_in_chat(uuid, chatId)):

        if (repoUserName is None):
            return jsonify({"error": "Не указано имя собственника репозитория"})
        else:
            repoUserName = repoUserName.strip()
            if (len(repoUserName) == 0):
                return jsonify({"error": "Не указано имя собственника репозитория"})

        if (repoSameName is None):
            return jsonify({"error": "Не указано имя репозитория"})
        else:
            repoSameName = repoSameName.strip()
            if (len(repoSameName) == 0):
                return jsonify({"error": "Не указано имя репозитория"})

        if (user is None):
            return jsonify({"error": "Не указано имя пользователя"})
        else:
            user = user.strip()
            if (len(user) == 0):
                return jsonify({"error": "Не указано имя пользователя"})

        if (password is None):
            return jsonify({"error": "Не указан пароль"})
        else:
            try:
                password = base64.b64decode(password).strip()
                if (len(password) == 0):
                    return jsonify({"error": "Не указан пароль"})
            except Exception as e:
                return jsonify({"error": "Не указан пароль"})

        c = AESCipher()
        password = c.encrypt(password)
        con = connect_to_db()
        with con:
            row = select_and_fetch_one(con, "SELECT * FROM `repository_settings` WHERE `CHAT_ID` = %s LIMIT 1", [chatId])
            if (row is not None):
                execute_update(con, "UPDATE `repository_settings` SET REPO_SITE = %s, REPO_USER_NAME = %s, REPO_SAME_NAME = %s, USER = %s, PASSWORD = %s WHERE CHAT_ID = %s", ['github.com', repoUserName, repoSameName, user, password, chatId])
            else:
                execute_update(con, "INSERT INTO `repository_settings`(CHAT_ID, REPO_SITE, REPO_USER_NAME, REPO_SAME_NAME, USER, PASSWORD) VALUES (%s, %s, %s, %s, %s, %s)", [chatId, 'github.com', repoUserName, repoSameName, user, password])
            return jsonify({"error": ""})
    else:
        abort(404)

@app.route('/reviewgram/try_lock/')
def try_lock():
    chatId = request.values.get("chatId")
    uuid = request.values.get("uuid")
    if (is_user_in_chat(uuid, chatId)):
        con = connect_to_db()
        lockTime = int(os.getenv("LOCK_TIME"))
        timestamp = int(time.time())
        with con:
            row = select_and_fetch_one(con, "SELECT * FROM `repo_locks` WHERE `TOKEN` <> %s AND `CHAT_ID` = %s AND " + str(timestamp) + " - TSTAMP <= " + str(lockTime) + " LIMIT 1", [uuid, chatId])
            if (row is not None):
                return jsonify({"locked": True})
            else:
                insert_or_update_repo_lock(con, chatId, uuid)
                return jsonify({"locked": False})
    else:
        abort(404)

@app.route('/reviewgram/check_syntax/', methods=['POST', 'GET'])
def check_syntax():
    data = request.json
    if data is None:
        return jsonify({"errors": ""})
    try:
        fileName = safe_get_key(data, ["filename"])
        content = safe_get_key(data, ["content"])
        start = safe_get_key(data, ["start"])
        end = safe_get_key(data, ["end"])
        if ((fileName is not None) and (content is not None) and (start is not None) and (end is not None)):
            fileContent = base64.b64decode(content)
            errors = run_pyflakes(fileName, fileContent.decode('UTF-8'), start, end)
            errors = base64.b64encode(errors.encode('UTF-8')).decode('UTF-8')
            return jsonify({"errors": errors})
    except Exception as e:
        append_to_log("/reviewgram/check_syntax: Exception " + traceback.format_exc())
    return jsonify({"errors": ""})


if __name__ == '__main__':
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    app.run(debug=True, host='0.0.0.0')
