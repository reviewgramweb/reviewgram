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
              "   r.CONTENT"  \
              " FROM " \
              "`recognize_tasks` AS r  " \
              " WHERE  " \
              " ((DATE_START IS NULL) OR (" + str(timestamp) + " - UNIX_TIMESTAMP(`DATE_START`) >= " + str(expiration_time) + ")) AND (DATE_END IS NULL) " \
              " LIMIT 1 "
        row = reviewgramdb.select_and_fetch_one(con, request, [])
        if (row is not None):
            id = row[0]
            fileName = row[1]
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
                except Exception as e:
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