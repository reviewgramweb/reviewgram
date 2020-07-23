from __future__ import (absolute_import, division, print_function, unicode_literals)
from flask import Flask, request, jsonify, abort
from dotenv import load_dotenv, find_dotenv
from datetime import datetime
from reviewgramdb import *
from repoutils import *
from languagefactory import LanguageFactory

from Crypto import Random
from Crypto.Cipher import AES
from functools import wraps

import struct
import logging
import json
import os
import pymysql
import base64
import traceback
import requests
import time
import math
import re
import jedi
import errno
import signal
import uuid

load_dotenv(find_dotenv())

bot_webhook_token = os.getenv("BOT_WEBHOOK_TOKEN")
bot_api_token  = os.getenv("BOT_API_TOKEN")

app = Flask(__name__)

# Исключение для таймаута
class TimeoutError(Exception):
    pass

# Декоратор для таймаута
class Timeout:
    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message
    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)
    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    def __exit__(self, type, value, traceback):
        signal.alarm(0)

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
        cipher = AES.new(self.key.encode("utf8"), AES.MODE_CBC, iv)
        return base64.b64encode(iv + raw_size_bytes + cipher.encrypt(raw_bytes.encode("utf8")))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:self.bs]
        raw_size = struct.unpack('<i', enc[self.bs:self.bs + 4])[0]
        cipher = AES.new(self.key.encode("utf8"), AES.MODE_CBC, iv)
        raw_bytes = cipher.decrypt(enc[self.bs + 4:])
        raw = raw_bytes[:raw_size].decode('utf_8')
        return raw

# Строит запрос для автодополнения из таблицы по полному совпадению
def build_exact_match_autocomplete_query(amount, limit, langId):
	if (amount == 0):
		return ""
	if (amount == 1):
		return "SELECT DISTINCT(r2.TEXT) " \
				"FROM" \
				"	`repository_autocompletion_lexemes` AS r1, " \
				"	`repository_autocompletion_lexemes` AS r2  " \
				"WHERE " \
				"	r1.LEXEME_ID = 0 AND r1.`TEXT` = %s " \
				"AND r2.LEXEME_ID = 1 " \
				"AND r1.ROW_ID = r2.ROW_ID " \
				"AND r1.`LANG_ID` = " + str(langId) + " LIMIT " + str(limit)
	result = "SELECT DISTINCT(r" + str(amount + 1) +".TEXT) "
	result += " FROM "
	i = 1
	while (i <= amount):
		result += "    `repository_autocompletion_lexemes` AS r" + str(i) + ", "
		i = i + 1
	result += "    `repository_autocompletion_lexemes` AS r" + str(amount + 1) + "  "
	result += " WHERE "
	result += "        r1.LEXEME_ID = 0 AND r1.`TEXT` = %s  "
	i = 2
	while (i <= amount):
		result += "    AND r" + str(i) +  ".LEXEME_ID = " + str(i - 1) + " AND r" + str(i) +  ".`TEXT` = %s "
		i = i + 1
	result += "    AND r" +  str(amount + 1) +".LEXEME_ID = "  + str(amount) + " "
	i = 0
	while (i < amount):
		result += "    AND r1.ROW_ID = r" + str(i + 2) + ".ROW_ID "
		i = i + 1
	result += " AND r1.`LANG_ID` = " + str(langId)
	result += " LIMIT " + str(limit)
	return result

# Строит запрос для автодополнения  из таблицы по неполному совпадению
def build_non_exact_match_autocomplete_query(amount, limit, langId):
	if (amount == 0):
		return ""
	if (amount == 1):
		return "SELECT DISTINCT(r1.`TEXT`) " \
			   "FROM "                       \
			   "  `repository_autocompletion_lexemes` AS r1 " \
			   "WHERE " \
			   "r1.`LEXEME_ID` = 0 AND levenshtein(r1.`TEXT`, %s) <= CHAR_LENGTH(r1.`TEXT`) / 2  " \
			   "AND r1.`LANG_ID` = " + str(langId) + " LIMIT " + str(limit)
	result = "SELECT DISTINCT(r" + str(amount) +".TEXT) "
	result += " FROM "
	i = 1
	while (i < amount):
		result += "    `repository_autocompletion_lexemes` AS r" + str(i) + ", "
		i = i + 1
	result += "    `repository_autocompletion_lexemes` AS r" + str(amount) + "  "
	result += " WHERE "
	result += " r1.LEXEME_ID = 0 AND r1.`TEXT` = %s "
	i = 2
	while (i < amount):
		result += " AND r" + str(i) + ".LEXEME_ID = " + str(i - 1) + " AND r" + str(i) + ".`TEXT` = %s "
		i = i + 1
	result += " AND r" + str(amount)  + ".LEXEME_ID = " + str(amount - 1)  + " AND levenshtein(r" + str(amount)  + ".`TEXT`, %s) <= CHAR_LENGTH(r" + str(amount)  + ".`TEXT`) / 2 "
	i = 2
	while (i <= amount):
		result += "AND r1.ROW_ID = r"  + str(i) + ".ROW_ID "
		i = i + 1
	result += " AND r1.`LANG_ID` = " + str(langId)
	result += " LIMIT " + str(limit)
	return result

# Пытается сделать автодополнение через таблицу
def table_try_autocomplete_with_max_amount(con, lexemes, maxAmount, langId):
    if (len(lexemes) == 0):
        return []
    exactLimit = math.ceil(maxAmount / 2)
    exactQuery = build_exact_match_autocomplete_query(len(lexemes), exactLimit, langId)
    exactRows = []
    try:
        with Timeout(seconds = 3):
            exactRows = select_and_fetch_all(con, exactQuery, lexemes)
    except:
        try:
            con.close()
        except:
            append_to_log("/reviewgram/table_autocomplete/: Unable to close connection")
        con = connect_to_db()
        append_to_log("/reviewgram/table_autocomplete/: " + traceback.format_exc())
        append_to_log("/reviewgram/table_autocomplete/: Timeout for fetching autocompletion")
    result = []
    for row in exactRows:
        appendType = 'space'
        firstChar = row[0][0].lower()
        if ((not re.match("^[a-zA-Z]$", firstChar)) and (firstChar != "\"") and (firstChar != "'")):
            appendType = 'no_space'
        result.append({
            'append_type': appendType,
            'complete': row[0],
            'name_with_symbols': row[0]
        })
    nonExactLimit = maxAmount - len(result)
    nonExactQuery = build_non_exact_match_autocomplete_query(len(lexemes), nonExactLimit, langId)
    nonExactRows = []
    try:
        with Timeout(seconds = 3):
            nonExactRows = select_and_fetch_all(con, nonExactQuery, lexemes)
    except:
        try:
            con.close()
        except:
            append_to_log("/reviewgram/table_autocomplete/: Unable to close connection")
        con = connect_to_db()
        append_to_log("/reviewgram/table_autocomplete/: " + traceback.format_exc())
        append_to_log("/reviewgram/table_autocomplete/: Timeout for fetching autocompletion")
    for row in nonExactRows:
        if (row[0].startswith(lexemes[-1])):
            completePart = row[0][len(lexemes[-1]):]
            if (len(completePart) != 0):
                result.append({
                    'append_type': 'no_space',
                    'complete': completePart,
                    'name_with_symbols': row[0]
                })
    if (len(result) < maxAmount):
        result  = result + table_try_autocomplete_with_max_amount(con, lexemes[1:], maxAmount - len(result))
    return result


# Пытается сделать автодополнение через таблицу
def table_try_autocomplete(con, lexemes, langId):
    if (len(lexemes) == 0):
        return []
    maxAmount = int(os.getenv("AUTOCOMPLETE_MAX_AMOUNT"))
    return table_try_autocomplete_with_max_amount(con, lexemes, maxAmount, langId)

# Получение вложенных данных из словаря
def safe_get_key(dict, keys):
    tmp = dict
    for key in keys:
        if key in tmp:
            tmp = tmp[key]
        else:
            return None
    return tmp

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
            row = select_and_fetch_one(con, "SELECT REPO_SITE, REPO_USER_NAME, REPO_SAME_NAME, USER, PASSWORD, LANG_ID FROM `repository_settings` WHERE `CHAT_ID` = %s LIMIT 1", [chatId])
            if (row is not None):
                password = ""
                if (len(row[4]) > 0):
                    c = AESCipher()
                    password = c.decrypt(row[4])
                return jsonify({"site": row[0], "repo_user_name": row[1], "repo_same_name": row[2], "user": row[3], "password": base64.b64encode(password.encode('UTF-8')).decode('UTF-8'), "langId" : row[5] })
            else:
                return jsonify({"site": "", "repo_user_name" : "", "repo_same_name": "", "user": "", "password": "", "langId": 1})
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
    langId = request.values.get("langId")
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
        
        con = connect_to_db()
        if (langId is None):
            return jsonify({"error": "Не указан ID языка"})
        else:
            try:
                langId = int(langId)
                row = select_and_fetch_one(con, "SELECT * FROM `languages` WHERE `ID` = %s LIMIT 1", [langId])
                if (row is None):
                    return jsonify({"error": "Не найден язык"})
            except Exception as e:
                return jsonify({"error": "Не распарсен язык"})

        c = AESCipher()
        password = c.encrypt(password)
        with con:
            row = select_and_fetch_one(con, "SELECT * FROM `repository_settings` WHERE `CHAT_ID` = %s LIMIT 1", [chatId])
            if (row is not None):
                execute_update(con, "UPDATE `repository_settings` SET REPO_SITE = %s, REPO_USER_NAME = %s, REPO_SAME_NAME = %s, USER = %s, PASSWORD = %s, LANG_ID = %s WHERE CHAT_ID = %s", ['github.com', repoUserName, repoSameName, user, password, langId, chatId])
            else:
                execute_update(con, "INSERT INTO `repository_settings`(CHAT_ID, REPO_SITE, REPO_USER_NAME, REPO_SAME_NAME, USER, PASSWORD, LANG_ID) VALUES (%s, %s, %s, %s, %s, %s, %s)", [chatId, 'github.com', repoUserName, repoSameName, user, password, langId])
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
        langId = safe_get_key(data, ["langId"])
        if ((fileName is not None) and (content is not None) and (start is not None) and (end is not None) and (langId is not None)):
            fileContent = base64.b64decode(content)
            langId = int(langId)
            errors = LanguageFactory().create(langId).checkSyntax(fileName, fileContent.decode('UTF-8'), start, end)
            errors = base64.b64encode(errors.encode('UTF-8')).decode('UTF-8')
            return jsonify({"errors": errors})
    except Exception as e:
        append_to_log("/reviewgram/check_syntax: Exception " + traceback.format_exc())
    return jsonify({"errors": ""})

@app.route('/reviewgram/get_autocompletions/', methods=['POST', 'GET'])
def get_autocompletions():
    data = request.json
    if data is None:
        return jsonify([])
    try:
        tokens = safe_get_key(data, ["tokens"])
        content = safe_get_key(data, ["content"])
        line = int(safe_get_key(data, ["line"]))
        position = int(safe_get_key(data, ["position"]))
        chatId = int(safe_get_key(data, ["chatId"]))
        branchId = safe_get_key(data, ["branchId"])
        langId = safe_get_key(data, ["langId"])
        if ((tokens is not None) and (content is not None) and (line is not None) and (position is not None) and (chatId is not None) and (branchId is not None) and (langId is not None)):
            if (not isinstance(tokens, list)):
                raise Exception("Error!")
            langId = int(langId)
            fileContent = base64.b64decode(content)
            con1 = connect_to_db()
            con2 = connect_to_db()
            result = []
            try:
                with con1:
                    result = result +  LanguageFactory().create(langId).getAutocompletions(con1, tokens, fileContent, line, position, chatId, branchId,)
            except Exception as e:
                append_to_log("/reviewgram/get_autocompletions: Exception " + traceback.format_exc())
            append_to_log("/reviewgram/get_autocompletions: Proceeding to table")
            try:
                with con2:
                    if (len(result) == 0):
                        result = result + table_try_autocomplete(con2, tokens, langId)
            except Exception as e:
                append_to_log("/reviewgram/get_autocompletions: Exception " + traceback.format_exc())
            append_to_log("/reviewgram/get_autocompletions: Proceeding to result")
            resultHash = {}
            filteredResult = []
            for part in result:
                if (not (part["complete"] in resultHash)):
                    resultHash[part["complete"]] = True
                    filteredResult.append(part)
            if (len(filteredResult) > 5):
                filteredResult = filteredResult[0:5]
            return jsonify(filteredResult)
    except Exception as e:
        append_to_log("/reviewgram/get_autocompletions: Exception " + traceback.format_exc())
    return jsonify([])
    
@app.route('/reviewgram/start_recognizing/', methods=['POST'])
def start_recognizing():
    langId = request.form.get("langId")
    record = request.files.get("record")
    if (request.form.get("langId") is not None):
        append_to_log("/reviewgram/start_recognizing: " + request.form.get("langId"))
    if (record is None):
        return jsonify([])
    record.seek(0, os.SEEK_END)
    fileLength = record.tell()
    if (fileLength >= int(os.getenv("MAX_RECORD_SIZE")) * 1024 * 1024):
        return jsonify({"error": "file is too large: " + str(fileLength) })
    fileName = os.getenv("APP_FOLDER") + "records/" + str(uuid.uuid4()) + "-" +  str(time.time()) + ".ogg"
    append_to_log("/reviewgram/start_recognizing: " + fileName)
    record.seek(0, os.SEEK_SET)
    record.save(fileName)
    con = connect_to_db()
    if (langId is None):
        langId = 0
    rowId = execute_insert(con, "INSERT INTO `recognize_tasks`(FILENAME, LANG_ID) VALUES (%s, %s)", [fileName, langId])
    return jsonify({"id": rowId})
    
@app.route('/reviewgram/recognizing_status/', methods=['GET'])
def recognizing_status():
    id = request.values.get("id")
    if (id is None):
        return  jsonify({"status": "pending"})
    else:
        try:
            id = int(id)
            con = connect_to_db()
            row = select_and_fetch_one(con, "SELECT `ID`, `RES` FROM `recognize_tasks` WHERE `ID` = %s AND `DATE_END` IS NOT NULL LIMIT 1", [id])
            if (row is not None):
                return  jsonify({"status": "ok", "result": row[1] })
            else:
                return  jsonify({"status": "pending"})
        except Exception as e:
            append_to_log("/reviewgram/recognizing_status: Exception " + traceback.format_exc())
            return  jsonify({"status": "pending"})
 
if __name__ == '__main__':
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
    app.run(debug=True, host='0.0.0.0')
