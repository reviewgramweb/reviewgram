from language import Language
from Levenshtein import distance

# Обычный язык для распознавания
class GenericLanguage(Language): 
    def __init__(self):
        return
    
    
    # Возвращает список подсказок для распознавания
    def getRecognitionHints(self):
        return []

    # Проверка синтаксиса, где
    # fileName  (str) - имя файла
    # fileContent  (str) - содержимое файла
    # start (int) - начало проверяемого участка
    # end   (int) - конец проверяемого участка
    # Возвращает
    # list со списком ошибок
    def checkSyntax(self, fileName, fileContent, start, end):
       return []

    # Получение автодополнений, где
    # con - соединение
    # tokens (list) - список лексем
    # content (str) - содержимое файла
    # line (int) - строка
    # position (int) - позиция в строке
    # chatId (str) - ID чата
    # branchId (str) -  ID ветки
    def getAutocompletions(self, con, tokens, content, line, position, chatId, branchId):
        return []
        
    # Распознавание фразы на языке
    # stmt (str) - входное выражение
    # table (str[][]) таблица автозамен
    # sourceFileContent (str) контент файла
    # Возвращает
    # строку с заменами
    def recognizeStatement(self, stmt, table, sourceFileContent):
        items = self.splitStatement(stmt)
        table_new = self.transformTable(table)
        local_table = [
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
            ["_",	"underscore"],
            ["\t",	"tab"],
            ["\t", "temp"],
            ["\t", "tabs"],
            [" ",	"space"],
            [" ", "bass"],
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
        for entry in local_table:
#            print (entry)
            parts = list(filter(lambda x: len(x) > 0, entry[1].split(" ")))
            table_new.append({"from": parts, "to": entry[0], "score": len(entry[1]) *  (-1), "registry": False, "first": False})
        i = 0 
        while (i < len(items)):
            if (distance(items[i]["original"],"Master") < 3):
                items[i]["original"] = "master"
            if (distance(items[i]["original"], "Slave") < 2):
                items[i]["original"] = "slave"
            i = i + 1
        
        return self.collectReplace(self.replaceAccordingGenericTables(items, table_new, False))
