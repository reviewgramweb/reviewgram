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
from reviewgram import AESCipher, repo_folder_name

env_path = Path(path + "/../") / '.env'
load_dotenv(dotenv_path=env_path)
timestamp = int(time.time())
updateTime = int(os.getenv("REPO_UPDATE_TIME"))
os.chdir(path + "/../repos/");

def try_print_error(result):
    errorContent = result.stderr.decode("UTF-8").lower()
    if ((errorContent.find("error") != -1) or (errorContent.find("ошибка") != -1)):
        print(errorContent)
        return True
    errorContent = result.stdout.decode("UTF-8").lower()
    if ((errorContent.find("error") != -1) or (errorContent.find("ошибка") != -1)):
        print(errorContent)
        return True
    return False

def clone_or_update_repo(con, repoInfo, timestamp):
    folderName = repo_folder_name(repoInfo["REPO_USER_NAME"], repoInfo["REPO_SAME_NAME"], repoInfo["BRANCH_ID"])
    sitePath = repoInfo["USER"] + ":" + repoInfo["PASSWORD"] + "@" + repoInfo["REPO_SITE"]
    onlineRepoPath = "https://" + sitePath + "/" + repoInfo["REPO_USER_NAME"] + "/" + repoInfo["REPO_SAME_NAME"] + ".git"
    error = False
    if (not os.path.isdir(folderName)):
        os.mkdir(folderName)
    if (os.path.isdir(folderName + "/.git/")):
        print("Updating...")
        os.chdir(folderName)
        content = ""
        with open('.git/config', 'r') as content_file:
            content = content_file.read()
            content_file.close()
        content = re.sub(r"url = [^\n]+", "url = " + onlineRepoPath, content)
        with open('.git/config', 'w') as content_file:
            content_file.write(content)
            content_file.close()
        result = subprocess.run(['git', 'pull', 'origin',  repoInfo["BRANCH_ID"]], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        error = try_print_error(result)
        os.chdir("..")
    else:
        print("Cloning...")
        os.chdir(folderName)
        result = subprocess.run(['git', 'clone', '--single-branch',  '--branch',  repoInfo["BRANCH_ID"], onlineRepoPath, "."], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        error = try_print_error(result)
        os.chdir("..")
    if (not error):
        cur = con.cursor()
        cur.execute("UPDATE `repository_cache_storage_table` SET `TSTAMP` = " + str(timestamp) + " WHERE `ID` = " + str(repoInfo["ID"]))
        con.commit()

con = pymysql.connect(os.getenv("MYSQL_HOST"), os.getenv("MYSQL_USER"), os.getenv("MYSQL_PASSWORD"), os.getenv("MYSQL_DB"), cursorclass=pymysql.cursors.DictCursor)
with con:
    cur = con.cursor()
    request = "SELECT" \
              "   r.ID, " \
              "   r.REPO_SITE, " \
              "   r.REPO_USER_NAME," \
              "   r.REPO_SAME_NAME," \
              "   r.BRANCH_ID," \
              "   USER,"  \
              "   PASSWORD " \
              "FROM " \
              "`repository_cache_storage_table` AS r,  " \
              "`repository_settings` AS s  " \
              "WHERE  " \
              "" + str(timestamp) + " - TSTAMP >= " + str(updateTime) + " " \
              " AND r.REPO_SITE = s.REPO_SITE " \
              " AND r.REPO_USER_NAME = s.REPO_USER_NAME " \
              " AND r.REPO_SAME_NAME = s.REPO_SAME_NAME "
    cur.execute(request)
    rows = cur.fetchall()
    c = AESCipher()
    for row in rows:
        row["PASSWORD"] = c.decrypt(row["PASSWORD"])
        print("Cloning or updating repo: " + "https://" + row["REPO_SITE"] + "/" + row["REPO_USER_NAME"] + "/" + row["REPO_SAME_NAME"] + ".git")
        clone_or_update_repo(con, row, timestamp)
    cur.close()
