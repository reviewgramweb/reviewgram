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

from languagefactory import LanguageFactory


def test_language_factory():
    f = LanguageFactory()
    assert f.create(1) is not None
    try:
        k = f.create(100) is None
        assert False
    except:
        assert True