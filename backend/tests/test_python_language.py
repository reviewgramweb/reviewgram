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
    
