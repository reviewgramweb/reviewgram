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

from pythonlanguage import PythonLanguage
from reviewgramdb import connect_to_db


def test_python_language():
    f = PythonLanguage()
    d = f.recognizeStatement("import operating system", [["ke", "ko"]], "")
    assert d == "import os"
    d = f.recognizeStatement("import shell utilities", [["ke", "ko"]], "")
    assert d == "import shutil"
    d = f.recognizeStatement("0 1 2 3 4 a b c test", [["ke", "ko"]], "")
    assert d == "01234 abc test"
    d = f.recognizeStatement("importance horse bass", [["ke", "ko"]], "")
    assert d == "import os.path"
    d = f.recognizeStatement("= items x multiplier", [["ke", "ko"]], "")
    assert d == "= items * multiplier"
    d = f.recognizeStatement("single quote abrams single quote", [["ke", "ko"]], "")
    assert d == "'abrams'"
    d = f.recognizeStatement("left square bracket data right square bracket", [["ke", "ko"]], "")
    assert d == "[data]"
    d = f.recognizeStatement("bee single quote abrams single quote", [["ke", "ko"]], "")
    assert d == "bee 'abrams'"
    d = f.recognizeStatement("array left square bracket data right square bracket", [["ke", "ko"]], "")
    assert d == "array [data]"
    d = f.recognizeStatement("single quote single quote", [["ke", "ko"]], "")
    assert d == "''"
    d = f.recognizeStatement("left square bracket left square bracket right square bracket right square bracket", [["ke", "ko"]], "")
    assert d == "[[]]"
    d = f.recognizeStatement("quote upper a lower a quote", [["ke", "ko"]], "")
    assert d == "\"Aa\""
    d = f.recognizeStatement("quote quote pattern quote quote", [["ke", "ko"]], "")
    assert d == "\"\"pattern \"\""
    d = f.recognizeStatement("", [["ke", "ko"]], "")
    assert d == ""
    d = f.recognizeStatement("mumacio mimacio", [["ke", "ko"]], "memacio = 1 + 1")
    assert d == "memacio memacio"

def test_python_language_recognition_hints():
    f = PythonLanguage()
    assert len(f.getRecognitionHints()) != 0
    
def test_python_language_get_identifier_list():
    f = PythonLanguage()
    ids = f.getIdentifierList("pip = bob + 1")
    assert len(ids) == 2
    assert ids[0] == "pip"
    assert ids[1] == "bob"
    ids = f.getIdentifierList("'22222")
    assert len(ids) == 0
    ids = f.getIdentifierList("!@@@")
    assert len(ids) == 0
    
def test_python_language_check_syntax():
    f = PythonLanguage()
    errors = f.checkSyntax("a.py", "me = 1 + 1", 0, 1)
    assert len(errors) == 0
    errors = f.checkSyntax("a.py", "me = 1 + ", 0, 1)
    assert len(errors) != 0
    
def test_python_language_get_autocompletions():
    path = os.path.dirname(os.path.abspath(__file__))
    env_path = Path(path + "/../") / '.env'
    load_dotenv(dotenv_path=env_path)
    f = PythonLanguage()
    con = connect_to_db()
    with con:
        autocompletions = f.getAutocompletions(con, ["import"], "", 1, 1, -485373794, "master")
        assert(autocompletions) != 0
    