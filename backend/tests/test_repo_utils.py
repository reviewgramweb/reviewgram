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


def test_repo_utils():
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    k = repo_folder_name("me34", "repo", "sdsdsd23___23")
    assert k == "me34_repo_sdsdsd23___23"
    assert not is_repo_folder_exists("me34", "repo", "sdsdsd23___23")
    k = full_repo_folder_name("me34", "repo", "sdsdsd23___23")
    assert k == "/root/reviewgram/repos/me34_repo_sdsdsd23___23/"
    con = connect_to_db()
    with con:
        id = try_insert_cloning_repo_task(con, "github.com", "reviewgram", "reviewgram_tokenize", "test_cron")
        assert id > 0
        execute_update(con, "DELETE FROM `repository_cache_storage_table` WHERE `ID`=" + str(id), [])
