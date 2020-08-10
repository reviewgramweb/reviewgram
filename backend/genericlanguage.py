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
        table_new = []
        for entry in table:
            parts = list(filter(lambda x: len(x) > 0, entry[0].split(" ")))
            if (entry[0].strip() != entry[1].strip()):
                table_new.append({"from": parts, "to": entry[1], "score": len(entry[0]) *  (-1)})
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
            table_new.append({"from": parts, "to": entry[0], "score": len(entry[1]) *  (-1)})
        i = 0 
        while (i < len(items)):
            if (distance(items[i]["original"],"Master") < 3):
                items[i]["original"] = "master"
            if (distance(items[i]["original"], "Slave") < 2):
                items[i]["original"] = "slave"
            i = i + 1
        similarityLimit = 0.25
        replacedRuleIndex = 0
        for entry in table_new:
            replacedRuleIndex = replacedRuleIndex + 1
            from_parts = entry["from"]
            to = entry["to"]
#            print ("Replacing " + str(from_parts) + " to " + to)
            changed = True
            i = 0
            while (changed):
                changed = False
#                print ("Starting search")
                i = 0
                while ((i <= len(items) - len(from_parts)) and (not changed)):
                    localSlice = items[i:i+len(from_parts)]
#                    print("Local slice, from: " + str(i) + ": " + str(localSlice))
                    j = 0
                    matches = True
                    while (j < len(from_parts)):
                        matches = matches and (distance(from_parts[j], localSlice[j]["lower"]) <= len(from_parts[j]) * similarityLimit) and (localSlice[j]["ruleIndex"] != replacedRuleIndex)
                        j = j + 1
                    if (matches):
#                        print ("Found entry at " + str(i))
                        changed = True
                        if (i == 0):
                            items = [{"original": to, "lower": to.lower(), "replaced": True, "ruleIndex": replacedRuleIndex}] +  items[i+len(from_parts):]
                        else:
                            items = items[:max(i, 0)] + [{"original": to, "lower": to.lower(), "replaced": True, "ruleIndex": replacedRuleIndex}] +  items[i+len(from_parts):]
                    i = i + 1
#                print (changed)
#                print (items)
                
        return self.collectReplace(items)
