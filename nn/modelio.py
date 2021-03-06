import pickle
import nltk
from functools import lru_cache
import itertools
from itertools import product as iterprod
#import random
from genericlanguage import GenericLanguage

dataset = []
with open('dataset.pickle', 'rb') as f:
     dataset = pickle.load(f)
     


__model_dataset_table = [
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
["get", "get"],
["chr", "chr"],
["ord", "ord"],
["len", "len"]
]

def model_text_tokenize(text):
    parts = text.split(" ")
    local_parts = []
    for part in parts:
        part = part.strip()
        cur = ""
        if len(part) > 0:
            for ch in part:
                if ch.isalnum() or (ch == "_") or (ch == "-"):
                    cur = cur + ch
                else:
                    if len(cur) != 0:
                        local_parts.append(cur)
                    local_parts.append(ch)
                    cur = ""
            if len(cur) != 0:
                local_parts.append(cur)
    return local_parts

def decode_model_output(output_as_text, output):
    language = GenericLanguage()
    tokens = model_text_tokenize(output_as_text)
    #print(tokens)
    step = 10
    current = 0
    result = []
    while current < len(output):
        num = output[current + 1] * 256 \
            + output[current + 2] * 128 \
            + output[current + 3] * 64 \
            + output[current + 4] * 32 \
            + output[current + 5] * 16 \
            + output[current + 6] * 8 \
            + output[current + 7] * 4 \
            + output[current + 8] * 2 \
            + output[current + 9]
        if output[current] == 0:
            if (num != 511):
                if (num < len(tokens)):
                    d = tokens[num]
                    result.append({"original": d, "lower": d.lower(), "replaced": False})
                # Handle another case silently, as we can disable it
        else:
            if (num < len(__model_dataset_table)):
                d = __model_dataset_table[num][0]
                result.append({"original": d, "lower": d.lower(), "replaced": False})
        current = current + step
    result = language.collectReplace(result)
    return result
    


try:
    arpabet = nltk.corpus.cmudict.dict()
except LookupError:
    nltk.download('cmudict')
    arpabet = nltk.corpus.cmudict.dict()

@lru_cache()
def _wordbreak(s):
    s = s.lower()
    if s in arpabet:
        result = arpabet[s][0]
        return result
    middle = len(s)/2
    partition = sorted(list(range(len(s))), key=lambda x: (x-middle)**2-x)
    for i in partition:
        pre, suf = (s[:i], s[i:])
        w = _wordbreak(suf)
        if pre in arpabet and w is not None:
            return arpabet[pre][0] + w
    return None

def wordbreak(s):
    arr = []
    cur = ""
    for ch in s:
        if (len(cur) == 0):
            cur = cur + ch
        else:
            if cur[0].isalpha():
                if ch.isalpha():
                    cur = cur + ch
                else:
                    if ch.isnumeric():
                        if (len(cur) != 0):
                            arr.append(cur)
                        cur = "" + ch
                    else:
                        if (len(cur) != 0):
                            arr.append(cur)
                        arr.append("" + ch)
                        cur = ""
            else:
               if cur[0].isnumeric():
                   if ch.isnumeric():
                        if (len(cur) != 0):
                            arr.append(cur)
                        cur = "" + ch
                   else:
                        if ch.isalpha():
                            if (len(cur) != 0):
                                arr.append(cur)
                            cur = "" + ch
                        else:
                            if (len(cur) != 0):
                                arr.append(cur)
                            arr.append("" + ch)
                            cur = ""
    if (len(cur) != 0):
        arr.append(cur)
    result = []
    for item in arr:
        if item[0].isalpha():
            result = result + _wordbreak(item)
        else:
            result.append(item)
    return result

basicPhonemes = [ "AA", "AE", "AH", "AO", "AW", "AY", "B", "CH", "D", "DH", "EH", "ER", "EY", "F", "G", "HH", "IH", "IY", "JH", "K", "L", "M", "N", "NG", "OW", "OY", "P", "R", "S", "SH", "T", "TH", "UH", "UW", "V", "W", "Y", "Z", "ZH"]

recognizedByGoogle = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '=', '_', '.', '[', '-', "'", ',', ']', '\\', '"', ':', '/', '%', '@']

phonemeDict = {}
i = 0
for phoneme in basicPhonemes:
    phonemeDict[phoneme] = i
    i = i + 1
    phonemeDict[phoneme + "0"] = i
    i = i + 1
    phonemeDict[phoneme + "1"] = i
    i = i + 1
    phonemeDict[phoneme + "2"] = i
    i = i + 1

for phoneme in recognizedByGoogle:
    phonemeDict[phoneme] = i
    i = i + 1


def __tokenize_input(text):
    parts = text.split(" ")
    local_parts = []
    for part in parts:
        part = part.strip()
        cur = ""
        if len(part) > 0:
            for ch in part:
                if ch.isalnum() or (ch == "_") or (ch == "-"):
                    cur = cur + ch
                else:
                    if len(cur) != 0:
                        local_parts.append(cur)
                    local_parts.append(ch)
                    cur = ""
            if len(cur) != 0:
                local_parts.append(cur)
    return local_parts

def __to_network_basic_input(tokenizedParts):
    i = 0
    maxresult = 819
    result = []
    for tokenizedPart in tokenizedParts:
        phonemes = wordbreak(tokenizedPart)
        for phoneme in phonemes:
            result.append([i, phonemeDict[phoneme]])
        i = i + 1
    return result
    
def encode_model_input(s):
    lst = __to_network_basic_input(__tokenize_input(s))
    result_input = []
    padding = [1, 1, 1, 1, 1,   1, 1, 1, 1, 1, 1, 1, 1]
    maxresult = 819 / len(padding)
    for inp in lst:
        bits1 = '{0:05b}'.format(inp[0])
        bits2 = '{0:08b}'.format(inp[1])
        result_input.append([int(bits1[0]), int(bits1[1]), int(bits1[2]), int(bits1[3]), int(bits1[4]), int(bits2[0]), int(bits2[1]), int(bits2[2]), int(bits2[3]), int(bits2[4]), int(bits2[5]), int(bits2[6]), int(bits2[7])])
    while len(result_input) < maxresult:
        result_input.append(padding)
    return [item for sublist in result_input for item in sublist]

#print(encode_model_input("bst defines"))
#i = 0
#while (i < len(dataset)):
#    ddd = decode_model_output(dataset[i]["synonym"],dataset[i]["output"])
#    if (ddd != dataset[i]["fst"]):
#        print(dataset[i]["fst"], "<=====>", ddd)
#    i = i + 1