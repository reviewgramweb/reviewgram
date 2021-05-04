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

from reviewgramdb import *


def test_reviewgramdb():
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    con = connect_to_db()
    with con:
        data = select_and_fetch_all(con, "SELECT `ID` FROM `repo_locks`", [])
        assert len(data) == 0
        data = select_and_fetch_first_column(con, "SELECT `ID` FROM `recognize_tasks`", [])
        assert int(data) > 0
        data = select_and_fetch_first_column(con, "SELECT `ID` FROM `repo_locks`", [])
        assert data is None