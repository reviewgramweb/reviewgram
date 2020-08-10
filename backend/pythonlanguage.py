from language import Language
from pythonautocompleter import PythonAutocompleter
from pythonsyntaxchecker import PythonSyntaxChecker
from tokenize import tokenize, untokenize, NUMBER, STRING, NAME, OP
from io import BytesIO
from Levenshtein import distance

def entry_score_hash(item):
    if (item["first"]):
        return -1000000 - item["score"]
    else:
        return 0 - item["score"]

# Класс для работы с языком Python
class PythonLanguage(Language): 
    def __init__(self):
        self.autocompleter = PythonAutocompleter()
        self.syntaxChecker = PythonSyntaxChecker()
        keywords = [
            ["False",	"false", "pause"],						
            ["await",	"the way",	"wait out"],						
            ["else",	"elsa"],							
            ["import",	"input",	"importance",	"+registry",	"+first"],
            ["None",	"none",	"known"],
            ["break",	"Break",	"+registry"],	
            ["break",	"drake"],
            ["except",	"upset"],
            ["in",	"in keyword",	"in keywords",	"in key word",	"in key west"],
            ["raise",	"rise"],
            ["True",	"through",	"true",	"future"],
            ["return",	"returned"],
            ["and",	"and keyword",	"and keywords",	"and keyboard",	"and key west"],
            ["for",	"4 keyword", "4 keywords", "4keyword",	"4keywords",	"for keyword",	"for keywords",	"for key west"],
            ["lambda",	"lomza",	"lambda"],
            ["try",	"troy"],
            ["as",	"ave",	"ass",	"OS",	"a s", "+registry"],
            ["def",	"death",	"define",	"definition", "+first"],
            ["from",	"From"],
            ["nonlocal",	"non-local",	"9 local",	"9 logo"],
            ["while",	"I'll",	"wow", "+registry"],
            ["assert",	"assault"],
            ["del",	"jail",	"zelle",	"jealous"],
            ["global",	"Global", "+registry"],
            ["not",	"Not", "+registry"],
            ["with",	"width"],
            ["elif",	"else if"],
            ["if",	"i f"],
            ["or",	"or keyword"],
            ["yield",	"Yield", "+registry"]
        ]
        common = [
            ["/",	"slash"],								
            ["\\",	"backslash"],								
            ["\"",	"quote",	"gold",	"court"],						
            ["\'",	"single quote",	"single quotes",	"single proton"],						
            ["#",	"hash"],								
            ["[",	"left square bracket"],								
            ["]",	"right square bracket"],								
            ["{",	"left brace",	"left brain"],							
            ["}",	"right brace",	"right brain"],							
            [";",	"semicolon",	"jamie cullum"],							
            [":",	"colon",	"call him"],							
            [".",	"dot"],								
            [",",	"comma"],								
            ["+",	"plus"],								
            ["-",	"minus"],								
            ["*",	"multiply"],								
            ["*",	"X",						"+registry"],		
            ["^",	"caret",	"carrots",	"carry",	"carried"],					
            ["%",	"modulus",	"modules",	"model is"],						
            ["**",	"exponentiation"],								
            ["//",	"floor division",	"for our division"],							
            ["@",	"at sign"],								
            ["<<",	"shift left",	"just left"],							
            [">>",	"shift right",	"shift right"],							
            ["&",	"bitwise and",	"beach wise and",	"bitwise end",	"beach wise end",	"wyzant"],				
            ["|",	"vertical bar",	"horizontal wave",	"where is on the wave"],						
            [":=",	"colon assign",	"all of the sign",	": assign",	": inside"],					
            [">",	"greater"],								
            ["<",	"lesser"],								
            ["<=",	"lesser or equal",	"less or equal"],							
            [">=",	"greater or equal"],								
            ["==",	"equal"],								
            ["!=",	"not equal"],								
            ["(",	"opening round bracket",	"opening round brackets"],							
            [")",	"closing round bracket",	"closing round brackets"],							
            ["->",	"arrow"],								
            ["+=",	"plus equal"],								
            ["-=",	"minus equal"],								
            ["*=",	"multiply equal"],								
            ["*=",	"X equal",						"+registry"],		
            ["/=",	"divide equal",	"divided equal",	"division equal"],						
            ["//=",	"double slash equal",	"double/equal",	"cc equal"],						
            ["**=",	"double star equal",	"devil star evil",	"devil star equal"],						
            ["&=",	"and equal",	"an equal"],							
            ["|=",	"or equal",	"glory"],							
            ["%=",	"percent sign equal",	"% evil"],							
            ["@=",	"at sign equal",	"@equal",	"that sign equal",	"at signing for"],					
            [">>=",	"shift right equal",	"just right equal",	"shift right evil",	"just right evil"],					
            ["<<=",	"shift left equal",	"just left equal",	"shift left evil",	"just left evil"],					
            ["^=",	"exclusive or equal",	"exclusive voorheesville"],							
            ["$",	"dollar sign"],								
            ["?",	"question mark"],								
            ["`",	"grave accent",	"gravis",	"graphics and"],						
            ["0",	"zero"],
            ["1",	"one"],
            ["2",	"two"],
            ["3",	"three"],
            ["4",	"four"],
            ["5",	"five"],
            ["6",	"six"],
            ["7",	"seven"],
            ["8",	"eight"],
            ["9",	"nine"],
            ["_"	"underscore"],								
            ["\t",	"tab",	"temp",	"tabs"],						
            [" ",	"space",	"bass"],
            ["master",	"Master",								"+registry"],
            ["slave",	"Slave",								"+registry"],
            ["frontend",	"front-end"],								
            ["backend",	"back-end"],
            ["frontend",	"front end"],
            ["backend",	"back end"],
            ["backend",	"black ant"],
            ["frontend",	"bronte and"],
            ["frontend", "bronx france"],
            ["frontend", "front and"],
            ["frontend", "front ends"]
        ]

        modules = [
            ["shutil","shell utilities","+registry"],
            ["shutil","show me Chili's","+registry"],
            ["unittest","unit test","+registry"],
            ["subprocess","subtract mixed","+registry"],
            ["fractions","Fractions","+registry"],
            ["cmath","sea math","sea mess","CMOS","ST Math","+registry"],
            ["glob","global find","global fight","global fine","global fine"],
            ["copy","Copy","+registry"],
            ["functions","function","+registry"],
            ["os","operation system","horse"],
            ["os.path","operation system path","operation system bass","horse path","horse bass"],
            ["json","Json","+registry"],
            ["calendar","Calendar","+registry"],
            ["pickle","Pickle","+registry"],
            ["datetime","date-time","daytime"],
            ["bisect","Bisect","+registry"],
            ["collections","Collections","+registry"],
            ["array","are","every"],
            ["itertools","iteration tools","+registry"],
            ["time","Time","+registry"],
            ["sys","system","seas"],
            ["random","ran and","+registry"],
            ["math","mess","+registry"],
            ["atexit","at exit","+registry"],
            ["gc","garbage collection","+registry"],
            ["inspect","Inspect","+registry"],
            ["marshal","marshall","+registry"],
            ["traceback","trace back","chase back"],
            ["types","tight","+registry"],
            ["warnings","warninks","+registry"],
            ["weakref","weak references","week references"],
            ["future_builtins","future built-ins","future buildings"],
            ["pdb","program debug","randy bug"],
            ["doctest","documentation test","documentation text"],
            ["decimal","Decimal","+registry"],
            ["numbers","Numbers","+registry"],
            ["abc","a b c","+registry"],
            ["abc","ABC","+registry"],
            ["contextlib","context library","+registry"],
            ["functools","functional tools","+registry"],
            ["heapq","heap queue","heap fewer","hip queue","heap queue"],
            ["heapq","EQ","+registry"],
            ["operator","Operator","+registry"],
            ["codecs","codex","+registry"],
            ["re","regular expression","+registry"],
            ["string","String","+registry"],
            ["struct","structure","+registry"],
            ["unicodedata","unicode data","unico data"],
            ["sqlite3","sqlite three","+registry"],
            ["shelve","shelf","+registry"],
            ["bz2","b z two","b z 2","be set to","busy too","busy to"],
            ["filecmp","file compare","+registry"],
            ["fnmatch","function match","+registry"],
            ["gzip","g zip","+registry"],
            ["tarfile","tar file","tar files"],
            ["tempfile","temp file","temp files"],
            ["zipfile","zip file","zip files"],
            ["zlib","z lib","that sleep","z sleep","zeeland"],
            ["commands","Commands","+registry"],
            ["configparser","configuration parser","+registry"],
            ["errno","error number","your number"],
            ["fcntl","file control","while control"],
            ["io","i o","+registry"],
            ["logging","Logging","+registry"],
            ["mmap","memory mapping","memory metal","memory match"],
            ["msvcrt","microsoft runtime","+registry"],
            ["optparse","option parse","option pass","austin carr"],
            ["signal","Signal","+registry"],
            ["winreg","windows registry","+registry"],
            ["multiprocessing","multi-processing","+registry"],
            ["threading","trade inc","threaten","shredding"],
            ["queue","Queue","+registry"],
            ["asynchat","asynchronous chat","asynchronous shirt"],
            ["asyncore","asynchronous core","a synchronous or","asynchronous score","asynchronous corey","asynchronous query"],
            ["select","Select","+registry"],
            ["socket","sockets","+registry"],
            ["ssl","secure socket layer","secure sockets layer"],
            ["SocketServer","socket server","+registry"],
            ["ftplib","ftp library","icp library","lcp library"],
            ["http","HTTP","+registry"],
            ["smtplib","smtp library","smpp library"],
            ["urllib","url library","you are a library"],
            ["xmlrpc","xml remote procedure calls","xml remote procedure call"],
            ["cgi","c g i","c o g i","c v i","c d i"],
            ["cgitb","cgi t b","cgi tv","c g i t b","c t i t b","c c i t"],
            ["wsgiref","wsgi reference","w s g i reference","w s g reference"],
            ["flask","flesk","+registry"],
            ["django","jungle","junker"],
            ["django","Django","+registry"],
            ["gunicorn","g unicorn","the unicorn"],
            ["base64","day 64","+registry"],
            ["binascii","bin aski","bin ascii","SQ","benassi"],
            ["csv","c s v","c s we","cs we"],
            ["email","mary","+registry"],
            ["hashlib","crash library","hash library","crash sleep","hash sleep","has library"],
            ["hmac","h mac","h mark","smack","it smack","h maggie"],
            ["HTMLParser","html parser","+registry"],
            ["mimetypes","mime types","mineplex","minds heights","mind heights"],
            ["quopri","q prime","quo prime","core prime","coupon"],
            ["xml","accident","flexinail"],
            ["ctypes","sea types","c types","seaside","c-type","seat height"]
        ]
        self.keywords = self.commandListToObjects(keywords)
        self.common = self.commandListToObjects(common)
        self.modules = self.commandListToObjects(modules)
        super().__init__()
    
    # Превращает список писков слов в структурированные описания слов
    # commands (str[][]) - команды
    # Возвращает
    # dict[] со списком распознавания
    def commandListToObjects(self, commands):
        result = []
        for command in commands:
            o = {"to_word": "", "from_words": [], "registry": False, "first": False}
            i = 0
            for item in command:
                if (i == 0):
                    o["to_word"] = item
                else:
                    if (item == "+registry"):
                        o["registry"] = True
                    else:
                            if (item == "+first"):
                                o["first"] = True
                            else:
                                o["from_words"].append(item.split(" "))
                i = i + 1
            for item in o["from_words"]:
                r = {"to_word": o["to_word"], "from_words": item, "registry": o["registry"], "first": o["first"], "score": 0}
                j = 0
                for word in item:
                    r["score"] = r["score"] + len(word)
                    if (j != 0):
                        r["score"] = r["score"] + 1
                    j = j + 1
                result.append(r)
        return sorted(result, key=entry_score_hash)
    
    # Возвращает список подсказок для распознавания
    def getRecognitionHints(self):
        result = []
        entries = [self.keywords, self.common, self.modules]
        for entry in entries:
            for item in entry:
                if (item["to_word"][0].isalpha()):
                    result.append(item["to_word"])
        return list(set(result))
        
    # Возвращает идентификаторы из файла
    # content (str) содержимое файла
    # Возвращает
    # list со списком идентификаторов
    def getIdentifierList(self, content):
        try:
            raise Error("222")
            result = []
            stream = tokenize(BytesIO(content.encode('utf-8')).readline)
            for tt, tokval, _, _, _ in stream:
                tokval = tokval.strip()
                if (len(tokval) and (tt == NAME)):
                    result.append(tokval)
            return result
        except:
            return []

    # Проверка синтаксиса, где
    # fileName  (str) - имя файла
    # fileContent  (str) - содержимое файла
    # start (int) - начало проверяемого участка
    # end   (int) - конец проверяемого участка
    # Возвращает
    # list со списком ошибок
    def checkSyntax(self, fileName, fileContent, start, end):
        return self.syntaxChecker.checkSyntax(fileName, fileContent, start, end)

    # Получение автодополнений, где
    # con - соединение
    # tokens (list) - список лексем
    # content (str) - содержимое файла
    # line (int) - строка
    # position (int) - позиция в строке
    # chatId (str) - ID чата
    # branchId (str) -  ID ветки
    def getAutocompletions(self, con, tokens, content, line, position, chatId, branchId):
        return self.autocompleter.getAutocompletions(con, tokens, content, line, position, chatId, branchId)
