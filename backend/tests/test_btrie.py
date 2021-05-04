#test btrie.py
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

from btrie import BTrie, get_dataset_trie

def test_get_dataset_trie():
    btrie = get_dataset_trie()
    assert not (btrie is None)
    assert btrie.max_length == 819

def test_btrie():
    btrie = BTrie()
    btrie.add([0,1,0,1])
    btrie.add([1,1,0,1])
    assert btrie.max_length == 4
    assert btrie.count_mismatches([0,0,0,0]) == 2
    assert btrie.count_mismatches([0,0,1,0]) == 3