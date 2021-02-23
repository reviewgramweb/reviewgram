# Формирование автосписка, исходя из данных для тестирования
# см. tooltodataset.py для преобразования его в данных для нейросети
import sys
import os
from tokenize import tokenize, untokenize, NUMBER, STRING, NAME, OP
from io import BytesIO

def unique(list1):
    list_set = set(list1)
    unique_list = (list(list_set))
    return unique_list

def toList(token):
    if token == "os.path":
        return [token]
    delimiters = [".", "," "%", "#"]
    lst = [token]
    flatten = lambda t: [item for sublist in t for item in sublist]
    for delimiter in delimiters:
        lst = list(filter(lambda x: len(x)> 0, flatten(list(map(lambda x: x.partition(delimiter), lst)))))
    return lst


def getTokens(text):
    if (text == "os.path"):
        result = ["os.path"]
        return result
    if (text == "import os.path"):
        result = ["import", "os.path"]
        return result
    if (text == "#"):
        result = ["#"]
        return result        
    stream = tokenize(BytesIO(text.encode('utf-8')).readline)
    result = []
    for _, tokval, _, _, _ in stream:
        tokval = tokval.strip()
        if (len(tokval)):
            should_add = not (tokval[0] == '#') and not (tokval == '\r') and not (tokval == '\n')
            if should_add:
                tokens = toList(tokval)
                for tokval in tokens:
                    if (tokval.startswith("'") or tokval.startswith("\"")):
                        if (tokval.endswith("'") or tokval.endswith("\"")):
                            result.append(tokval[0:1])
                            result.append(tokval[1:len(tokval) - 1])
                            result.append(tokval[-1])
                        else:
                            result.append(tokval[0:1])
                            result.append(tokval[1:len(tokval)])
                    else:
                        result.append(tokval)
    result = result[1:]
    return result



data = ["import os",
"i = i + 1",
"total_items = items * multiplier",
"import os.path",
"handler = subprocess.run([\"rm\", file.txt])",
"k = k * 2",
"last_date = math.min(datetime.now(), last_date)",
"import shutil",
"logging.warning(\"Low memory\")",
"logging",
"logging.basicConfig(filename='example.log',level=logging.DEBUG)",
"import logging",
"logging.info('Started')",
"import mylib",
"logger = logging.getLogger(__name__)",
"Logger.addFilter() ",
"Logger.removeFilter() ",
"formatter = logging.Formatter()",
"ch.setLevel(logging.DEBUG)",
"if logger.isEnabledFor(logging.DEBUG):",
"sys._getframe()",
"handle.read()",
"handle.write(2)",
"handle.readlines()",
"num_sqrt = num ** 0.5",
"num_sqrt = cmath.sqrt(num)",
"fahrenheit = (celsius * 1.8) + 32",
"while count < nterms:",
"if((greater % x == 0) and (greater % y == 0)):",
"def compute_lcm(x, y):",
"while(True):",
"lcm = (x*y)//compute_gcd(x,y)",
"return n*factorial(n-1)",
"with open(\"names.txt\",'r',encoding = 'utf-8') as names_file:",
"name.strip()",
"if year % 4 == 0 and year % 100 != 0:",
"os.system(\"clear\")",
"request = urllib2.Request(url)",
"response = json.load(urllib2.urlopen(request))",
"json.dumps(response,indent=2)",
"bestmatch = re.compile(r' ')",
"search = bestmatch.sub('+', match)",
"b64_encoded = base64.b64encode(search)",
"sys.exit()",
"sortByVotes()",
"elif answer == \"5\":",
"for root, dirs, files in os.walk(rootPath):",
"for filename in fnmatch.filter(files, pattern):",
"for extensions in images:",
"from distutils.spawn import find_executable",
"devnull = open(os.devnull, 'w')",
"return bool(find_executable(self.command[0]))",
"def encode(self, decoder_process, bitrate):",
"cmd[cmd.index('BITRATE')] = str(bitrate)",
"self.mimetype = MIMETYPES[filetype]",
"cmd = [find_executable(self.command[0])] + self.command[1:]",
" def __str__(self):",
"Exception.__init__(self, value)",
"return filepath.lower()",
"Encoder('ogg', ['oggenc', '-b', 'BITRATE', '-']),",
"if not encoder:",
"return encoder.encode(decoder_process, bitrate)",
"raise EncodeError(errmsg % audio_format)",
"self.check_encoder_available(audioformat)",
"decoder_process = self._decode(filepath, decoder)",
"if decoder_process.stderr:",
"if encoder_process:",
"encoder_process.stdout.close()",
"b, g, r = cv2.split(img)",
"compressed_image = cv2.imread('compressed_image.png', 1)",
"compressedPixelAt = calculate(compressed_image)",
"error = np.sum(np.abs(diff) ** 2)",
"PSNR = -(10 * math.log10(error / (255 * 255)))",
"import argparse ",
"dict , final , img_list = {} , [] , []",
"img = np.zeros((height,len(c_sorted),3),np.uint8)  ",
"r ,g , b = c_sorted[x][0]*255,c_sorted[x][1]*255,c_sorted[x][2]*255",
"if row==height-1 and col == width-1 : ",
"h2 = int(h * repetitions)",
"v2 = int(v * repetitions)",
"def findThreshold(lst , add) : ",
"img = cv2.resize(img,(800,500))  ",
"if np.all(np.asarray(color)) ==  True :",
"response = requests.get(url)",
"pdf.set_subject('python')",
"pdf.set_title('Generating PDF with Python')",
"pdf.add_page()",
"img.close()",
"clockTime.after(1000, time)",
"key = key or self.__key or 1",
"for ch in content:",
"ans.append(chr(ord(ch) ^ key))",
"try:",
"except:",
"return False",
"for line in fin:",
"group.add(self)",
"return len(self._bricks) == 0",
"for brick in self._bricks:",
"unittest",
"fractions",
"glob",
"copy",
"functions",
"os.path",
"calendar",
"pickle",
"bisect",
"collections",
"array",
"itertools",
"random",
"atexit",
"gc",
"inspect",
"marshal",
"traceback",
"types",
"warnings",
"weakref",
"future_builtins",
"pdb",
"doctest",
"decimal",
"numbers",
"abc",
"contextlib",
"functools",
"heapq",
"operator",
"codecs",
"string",
"struct",
"unicodedata",
"sqlite3",
"shelve",
"bz2",
"filecmp",
"gzip",
"tarfile",
"tempfile",
"zipfile",
"zlib",
"commands",
"configparser",
"errno",
"fcntl",
"io",
"mmap",
"msvcrt",
"optparse",
"signal",
"winreg",
"multiprocessing",
"threading",
"queue",
"asynchat",
"asyncore",
"select",
"socket",
"ssl",
"socketserver",
"ftplib",
"http",
"smtplib",
"urllib",
"xmlrpc",
"cgi",
"cgitb",
"wsgiref",
"flask",
"django",
"gunicorn",
"binascii",
"csv",
"email",
"hashlib",
"hmac",
"htmlparser",
"mimetypes",
"quopri",
"xml",
"ctypes",
"import unittest",
"import fractions",
"import glob",
"import copy",
"import functions",
"import os.path",
"import calendar",
"import pickle",
"import bisect",
"import collections",
"import array",
"import itertools",
"import random",
"import atexit",
"import gc",
"import inspect",
"import marshal",
"import traceback",
"import types",
"import warnings",
"import weakref",
"import future_builtins",
"import pdb",
"import doctest",
"import decimal",
"import numbers",
"import abc",
"import contextlib",
"import functools",
"import heapq",
"import operator",
"import codecs",
"import string",
"import struct",
"import unicodedata",
"import sqlite3",
"import shelve",
"import bz2",
"import filecmp",
"import gzip",
"import tarfile",
"import tempfile",
"import zipfile",
"import zlib",
"import commands",
"import configparser",
"import errno",
"import fcntl",
"import io",
"import mmap",
"import msvcrt",
"import optparse",
"import signal",
"import winreg",
"import multiprocessing",
"import threading",
"import queue",
"import asynchat",
"import asyncore",
"import select",
"import socket",
"import ssl",
"import socketserver",
"import ftplib",
"import http",
"import smtplib",
"import urllib",
"import xmlrpc",
"import cgi",
"import cgitb",
"import wsgiref",
"import flask",
"import django",
"import gunicorn",
"import binascii",
"import csv",
"import email",
"import hashlib",
"import hmac",
"import htmlparser",
"import mimetypes",
"import quopri",
"import xml",
"import ctypes",
"6 \ 7",
"master",
"slave",
"_",
"frontend",
"backend",
"await data",
"if none else",
"else",
"`"
"1 << 9",
"1 >> 9",
"<<"
">>",
"true",
"false",
"#",
";",
"@",
"&",
"|",
":=",
">",
"<=",
">=",
"->",
"+=",
"-=",
"*=",
"/=",
"//=",
"**=",
"&=",
"|=",
"%=",
"@=",
">>=",
"<<=",
"^=",
"$",
"?",
"break",
"lambda",
"nonlocal",
"assert",
"del",
"global",
"yield"
]

tokenReplaceTable = [
["shutil","shell utilities","show me chili's"],
["unittest","unit test"],
["subprocess","subtract mixed"],
["fractions","fractions"],
["cmath","sea math","sea mess","cmos","st math"],
["glob","global find","global fight","global fine","global fine"],
["copy","copy"],
["functions","function"],
["os","operation system","horse"],
["os.path","operation system path","operation system bass","horse path","horse bass"],
["json","json"],
["calendar","calendar"],
["pickle","pickle"],
["datetime","date-time","daytime"],
["bisect","bisect"],
["collections","collections"],
["array","are","every"],
["itertools","iteration tools"],
["time","time"],
["sys","system","seas"],
["random","ran and"],
["math","mess"],
["atexit","at exit"],
["gc","garbage collection"],
["inspect","inspect"],
["marshal","marshall"],
["traceback","trace back","chase back"],
["types","tight"],
["warnings","warninks"],
["weakref","weak references","week references"],
["future_builtins","future built-ins","future buildings"],
["pdb","program debug","randy bug"],
["doctest","documentation test","documentation text"],
["decimal","decimal"],
["numbers","numbers"],
["abc","a b c"],
["abc","abc"],
["contextlib","context library"],
["functools","functional tools"],
["heapq","heap queue","heap fewer","hip queue","heap queue"],
["heapq","eq"],
["operator","operator"],
["codecs","codex"],
["re","regular expression"],
["string","string"],
["struct","structure"],
["unicodedata","unicode data","unico data"],
["sqlite3","sqlite three"],
["shelve","shelf"],
["bz2","b z two","b z 2","be set to","busy too","busy to"],
["filecmp","file compare"],
["fnmatch","function match"],
["gzip","g zip"],
["tarfile","tar file","tar files"],
["tempfile","temp file","temp files"],
["zipfile","zip file","zip files"],
["zlib","z lib","that sleep","z sleep","zeeland"],
["commands","commands"],
["configparser","configuration parser"],
["errno","error number","your number"],
["fcntl","file control","while control"],
["io","i o"],
["logging","logging"],
["mmap","memory mapping","memory metal","memory match"],
["msvcrt","microsoft runtime"],
["optparse","option parse","option pass","austin carr"],
["signal","signal"],
["winreg","windows registry"],
["multiprocessing","multi-processing"],
["threading","trade inc","threaten","shredding"],
["queue","queue"],
["asynchat","asynchronous chat","asynchronous shirt"],
["asyncore","asynchronous core","a synchronous or","asynchronous score","asynchronous corey","asynchronous query"],
["select","select"],
["socket","sockets"],
["ssl","secure socket layer","secure sockets layer"],
["socketserver","socket server"],
["ftplib","ftp library","icp library","lcp library"],
["http","http"],
["smtplib","smtp library","smpp library"],
["urllib","url library","you are a library"],
["xmlrpc","xml remote procedure calls","xml remote procedure call"],
["cgi","c g i","c o g i","c v i","c d i"],
["cgitb","cgi t b","cgi tv","c g i t b","c t i t b","c c i t"],
["wsgiref","wsgi reference","w s g i reference","w s g reference"],
["flask","flesk"],
["django","jungle","junker"],
["django","django"],
["gunicorn","g unicorn","the unicorn"],
["base64","day 64"],
["binascii","bin aski","bin ascii","sq","benassi"],
["csv","c s v","c s we","cs we"],
["email","mary"],
["hashlib","crash library","hash library","crash sleep","hash sleep","has library"],
["hmac","h mac","h mark","smack","it smack","h maggie"],
["htmlparser","html parser"],
["mimetypes","mime types","mineplex","minds heights","mind heights"],
["quopri","q prime","quo prime","core prime","coupon"],
["xml","accident","flexinail"],
["ctypes","sea types","c types","seaside","c-type","seat height"],
["/","slash"],
["\\","backslash"],
["\"","quote","gold","court"],
["'","single quote","single quotes","single proton"],
["#","hash"],
["[","left square bracket"],
["]","right square bracket"],
["{","left brace","left brain"],
["}","right brace","right brain"],
[";","semicolon","jamie cullum"],
[":","colon","call him"],
[".","dot"],
[",","comma"],
["+","plus"],
["-","minus"],
["*","multiply"],
["*","x"],
["^","caret","carrots","carry","carried"],
["%","modulus","modules","model is"],
["**","exponentiation"],
["//","floor division","for our division"],
["@","at sign"],
["<<","shift left","just left"],
[">>","shift right","shift right"],
["&","bitwise and","beach wise and","bitwise end","beach wise end","wyzant"],
["|","vertical bar","horizontal wave","where is on the wave"],
[":=","colon assign","all of the sign",": assign",": inside"],
[">","greater"],
["<","lesser"],
["<=","lesser or equal","less or equal"],
[">=","greater or equal"],
["==","equal"],
["!=","not equal"],
["(","opening round bracket","opening round brackets"],
[")","closing round bracket","closing round brackets"],
["->","arrow"],
["+=","plus equal"],
["-=","minus equal"],
["*=","multiply equal"],
["*=","x equal"],
["/=","divide equal","divided equal","division equal"],
["//=","double slash equal","double/equal","cc equal"],
["**=","double star equal","devil star evil","devil star equal"],
["&=","and equal","an equal"],
["|=","or equal","glory"],
["%=","percent sign equal","% evil"],
["@=","at sign equal","@equal","that sign equal","at signing for"],
[">>=","shift right equal","just right equal","shift right evil","just right evil"],
["<<=","shift left equal","just left equal","shift left evil","just left evil"],
["^=","exclusive or equal","exclusive voorheesville"],
["$","dollar sign"],
["?","question mark"],
["`","grave accent","gravis","graphics and"],
["0","zero"],
["1","one"],
["2","two"],
["3","three"],
["4","four"],
["5","five"],
["6","six"],
["7","seven"],
["8","eight"],
["9","nine"],
["_","underscore"],
["master","master"],
["slave","slave"],
["frontend","front-end"],
["backend","back-end"],
["false","false","pause"],
["await","the way","wait out"],
["else","elsa"],
["import","input","importance"],
["none","none","known"],
["break","break"],
["break","drake"],
["except","upset"],
["in","in keyword","in keywords","in key word","in key west"],
["raise","rise"],
["true","through","true","future"],
["return","returned"],
["and","and keyword","and keywords","and keyboard","and key west"],
["for","4keyword","4keywords","for keyword","for keywords","for key west"],
["lambda","lomza","lambda"],
["try","troy"],
["as","ave","ass","os","a s"],
["def","death","define","definition"],
["from","from"],
["nonlocal","non-local","9 local","9 logo"],
["while","i'll","wow"],
["assert","assault"],
["del","jail","zelle","jealous"],
["global","global"],
["not","not"],
["with","width"],
["elif","else if"],
["if","i f"],
["or","or keyword"],
["yield","yield"],
["=","="],
["_","_"],
["min","min"],
["now","now"],
["warning","warning"],
["log","log"],
["level","level"],
["DEBUG","DEBUG"],
["info","info"],
["logger","logger"],
["getLogger","getLogger"],
["__name__","__name__"],
["Logger","Logger"],
["addFilter","addFilter"],
["removeFilter","removeFilter"],
["Formatter","Formatter"],
["setLevel","setLevel"],
["isEnabledFor","isEnabledFor"],
["_getframe","_getframe"],
["handle","handle"],
["read","read"],
["write","write"],
["readlines","readlines"],
["sqrt","sqrt"],
["open","open"],
["encoding","encoding"],
["utf-8","utf-8"],
["strip","strip"],
["system","system"],
["urllib2","urllib2"],
["request","request"],
["response","response"],
["Request","Request"],
["url","url"],
["load","load"],
["urlopen","urlopen"],
["dumps","dumps"],
["indent","indent"],
["compile","compile"],
["sub","sub"],
["b64encode","b64encode"],
["exit","exit"],
["walk","walk"],
["filter","filter"],
["distutils","distutils"],
["spawn","spawn"],
["find_executable","find_executable"],
["devnull","devnull"],
["bool","bool"],
["self","self"],
["str","str"],
["__str__","__str__"],
["Exception","Exception"],
["__init__","__init__"],
["close","close"],
["argparse","argparse"],
["int","int"],
["requests","requests"],
["get","get"],
["chr", "chr"],
["ord", "ord"],
["len", "len"]
]

tokenReplaceHash  = {}
tokenReplaceUsed = {}
tokenReplaceIndex = {}

i = 0
for item in tokenReplaceTable:
    tokenReplaceHash[item[0]] = item[1:]
    tokenReplaceUsed[item[0]] = False
    tokenReplaceIndex[item[0]] = i
    i = i + 1
    
print(tokenReplaceIndex["="])


def countSpacedTokens(stmt):
    i = 0
    for items in stmt:
        ddd = items.split(" ")
        for p in ddd:
            i = i + 1
    return i

result = []
def translateTokens(stmt, lst, end):
    if (len(end) == 0):
        for pairs, item in lst:
            tpl = (stmt, ",".join(pairs), " ".join(item))
            result.append(tpl)
    else:
        current = end[0]
        newend = end[1:]
        if (current in tokenReplaceHash):
            tokenReplaceUsed[current] = True
            for replaceItem in tokenReplaceHash[current]:
                new_lst = []
                for pairs, item in lst:
                    newpairs = list(pairs)
                    newpairs.append("1 " + str(tokenReplaceIndex[current]))
                    newitem = list(item)
                    newitem.append(replaceItem)
                    tpl = (newpairs,newitem)
                    new_lst.append(tpl)
                    translateTokens(stmt, new_lst, newend)
        else:
            new_lst = []
            for pairs, item in lst:
                lenpairs = countSpacedTokens(item)
                newpairs = list(pairs)
                newpairs.append("0 " + str(lenpairs))
                newitem = list(item)
                newitem.append(current)
                tpl = (newpairs,newitem)
                new_lst.append(tpl)
                translateTokens(stmt, new_lst, newend)

def makeAllPossibleInputsFromStatement(stmt):
    tokens = getTokens(stmt)
    if (len(tokens) < 4):
        translateTokens(stmt, [([],[])], tokens)
    else:
        i = 0
        while i < len(tokens) - 3:
            tokenPart = tokens[i:i+4]
            stmt = " ".join(tokenPart)
            translateTokens(stmt, [([],[])], tokenPart)
            i = i + 1

for curstmt in data:
    makeAllPossibleInputsFromStatement(curstmt)

for stmt, inputs, read_stmt in result:
    print("\"" + stmt.replace("\"", "\\\"") + "\"", "\t", inputs, "\t", "\"" + read_stmt.replace("\"", "\\\"") + "\"")

for k, v in tokenReplaceUsed.items():
    if not v:
        print(k, " is not used")
#print(toList("1.58"))
#print(getTokens("\"hello\"+\"world\",device.execute(1.58, 5)"))