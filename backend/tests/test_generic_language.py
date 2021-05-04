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

from genericlanguage import GenericLanguage
from language import Language

class TLanguage(Language):
    def __init__(self):
        super().__init__()

    def getRecognitionHints(self):
        return []

    def checkSyntax(self, fileName, fileContent, start, end):
       return []

    def getAutocompletions(self, con, tokens, content, line, position, chatId, branchId):
        return []

def test_generic_language_common_methods():
    lang = GenericLanguage()
    assert len(lang.getRecognitionHints()) == 0
    assert len(lang.checkSyntax("1.txt", "", 0, 1)) == 0
    assert len(lang.getAutocompletions(None, [], "", 1, 1, 0, "main")) == 0


def test_generic_language_recognize_statement():
    lang = GenericLanguage()
    result = lang.recognizeStatement("zero one two three four six seven eight nine fall tower underscore tab temp tabs space bass anthem", [], "")
    assert result.replace("\t", "  ") == "012346789 fall tower _         anthem"
    result = lang.recognizeStatement("front-end back-end front end back end black ant bronte and bronx france front and front ends fall tower Master Slave", [["fall", "falley"], ["tower", "bashnya"]], "")
    assert result == "frontend backend frontend backend backend frontend frontend frontend frontend falley bashnya master slave"
    
def test_language():
    lang = TLanguage()
    result = lang.recognizeStatement("zero", [], "")
    assert result.replace("\t", "  ") == "zero"