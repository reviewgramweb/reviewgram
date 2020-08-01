# encoding=UTF-8
# Клонирует или обновляет репозитории
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
import io
from google.cloud import speech_v1
from google.cloud.speech_v1 import enums
from google.cloud.speech_v1 import types

path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(path + "/../")

import reviewgramdb
from reviewgramlog import *

env_path = Path(path + "/../") / '.env'
load_dotenv(dotenv_path=env_path)
os.chdir(path + "/../repos/");

expiration_time = 30 * 60

def ogg2wav_convert(old, new):
    result = subprocess.run(['ffmpeg', "-hide_banner", "-loglevel", "panic", "-y", "-i", old, new], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stderr.decode("UTF-8")
    
def try_recognize(fileName, table):
    encoding = enums.RecognitionConfig.AudioEncoding.LINEAR16
    sample_rate_hertz = 48000
    language_code = 'en-US'
    model = 'command_and_search'
    config = {'encoding': encoding, 'sample_rate_hertz': sample_rate_hertz, 'language_code': language_code, 'model': model, 'speech_contexts': [ speech_v1.types.SpeechContext(phrases=['insert', 'tab', 'space', 'juggle', 'remove', 'master', 'branch', 'backend', 'frontend', 'main', 'dot', 'py', 'import', 'os', 'sys', 'pymongo', 'tokenize', 'untokenize', 'comma', 'op', 'colon', 'semicolon', 'quote', 'single', 'round', 'square', 'curvy', 'bracket', 'opening', 'closing', 'left', 'right', 'brace', 'caret', 'modulus', 'floor', 'division', 'ampersand', 'bitwise', 'assign', 'arrow', 'lambda', 'def', 'as', 'while', 'assert', 'del', 'async', 'elif', 'yield', 'shell', 'utilities', 'unit', 'test', 'find', 'copy', 'path', 'json', 'calendar', 'pickle', 'iteration', 'tools', 'weak', 'built-ins', 'debug', 'functools', 'context', 'heap', 'queue', 'warnings', 'doc', 'structure', 'string', 'config', 'parser', 'shelve', 'tar', 'temp', 'error', 'file', 'mapping', "parse", "signal", "select", "registry", "asynchronous", "chat", "core"]) ]}
    content = ""
    with io.open(fileName, "rb") as f:
        content = f.read()
    audio = {'content': content}
    client = speech_v1.SpeechClient.from_service_account_file(os.getenv("GOOGLE_SPEECH_CREDENTIALS"))
    operation = client.long_running_recognize(config=config, audio=audio)
    response = operation.result()
    total_result = []
    for result in response.results:
        alternative = result.alternatives[0]
        total_result.append(alternative.transcript)
    return " ".join(total_result).replace(". ", "")
    
def select_and_perform_task():
    con = reviewgramdb.connect_to_db()
    with con:
        timestamp = int(time.time())
        request = "SELECT" \
              "   r.ID, " \
              "   r.FILENAME, " \
              "   r.RES," \
              "   r.LANG_ID," \
              "   r.LOG," \
              "   r.CONTENT,"  \
              "   r.REPO_ID " \
              " FROM " \
              "`recognize_tasks` AS r  " \
              " WHERE  " \
              " ((DATE_START IS NULL) OR (" + str(timestamp) + " - UNIX_TIMESTAMP(`DATE_START`) >= " + str(expiration_time) + ")) AND (DATE_END IS NULL) " \
              " LIMIT 1 "
        row = reviewgramdb.select_and_fetch_one(con, request, [])
        if (row is not None):
            id = row[0]
            fileName = row[1]
            if (row[6] is not None):
                repoId = int(row[6])
            else:
                repoId = 0
            table = []
            rows = reviewgramdb.select_and_fetch_all(con, "SELECT FROM_TEXT, TO_TEXT FROM `replace_tables` WHERE `REPO_ID` = %s ORDER BY `ID` ASC" ,[repoId])
            for localRow in rows:
                table.append([localRow[0], localRow[1]])
            langId = 0
            if (row[3] is not None):
                langId = int(row[3])
            content = ""
            if (row[5] is not None):
                content = row[5]
            reviewgramdb.execute_update(con, "UPDATE `recognize_tasks` SET `DATE_START` = NOW()  WHERE `ID` = %s", [id])
            if (os.path.exists(fileName) and os.path.isfile(fileName)):
                try:
                    print(fileName)
                    newFileName = fileName.replace("ogg", "wav")
                    errors = ogg2wav_convert(fileName, newFileName)
                    if (len(errors) > 0):
                        print("Errors while converting ogg to wav:" + errors)
                        reviewgramdb.execute_update(con, "UPDATE `recognize_tasks` SET `RES` = %s, `LOG` = %s  WHERE `ID` = %s", ['', 'Errors in running ffmpeg ' + errors, id])
                    else:
                        reviewgramdb.execute_update(con, "UPDATE `recognize_tasks` SET `RES` = %s, `LOG` = %s  WHERE `ID` = %s", ['', 'Processed ogg 2 wav', id])
                        print("Recognizing...")
                        result = try_recognize(newFileName, table)
                        reviewgramdb.execute_update(con, "UPDATE `recognize_tasks` SET `RES` = %s, `LOG` = %s  WHERE `ID` = %s", [result, 'Successfully processed result', id])
                except Exception as e:
                    print('Exception: ' + traceback.format_exc())
                    reviewgramdb.execute_update(con, "UPDATE `recognize_tasks` SET `RES` = %s, `LOG` = %s  WHERE `ID` = %s", ['', 'Exception: ' + traceback.format_exc(), id])
            else:
                reviewgramdb.execute_update(con, "UPDATE `recognize_tasks` SET `RES` = %s, `LOG` = %s  WHERE `ID` = %s", ['', 'Unable to find file ', id])
            reviewgramdb.execute_update(con, "UPDATE `recognize_tasks` SET `DATE_END` = NOW()  WHERE `ID` = %s", [id])
    print("Performed")

i = 0
max = 4;
start_time = int(time.time())
while (i < max):
    i = i + 1
    select_and_perform_task()
    end_time = int(time.time())
    if (end_time - start_time > 15 * max):
        break