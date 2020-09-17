from abc import ABC, abstractmethod
from Levenshtein import distance
 
# Абстрактный класс языка для работы с ними
class Language(ABC): 
    def __init__(self):
        super().__init__()

    # Возвращает список подсказок для распознавания
    @abstractmethod
    def getRecognitionHints(self):
        pass

    # Проверка синтаксиса, где
    # fileName  (str) - имя файла
    # fileContent  (str) - содержимое файла
    # start (int) - начало проверяемого участка
    # end   (int) - конец проверяемого участка
    # Возвращает
    # list со списком ошибок
    @abstractmethod
    def checkSyntax(self, fileName, fileContent, start, end):
        pass

    # Получение автодополнений, где
    # con - соединение
    # tokens (list) - список лексем
    # content (str) - содержимое файла
    # line (int) - строка
    # position (int) - позиция в строке
    # chatId (str) - ID чата
    # branchId (str) -  ID ветки
    @abstractmethod
    def getAutocompletions(self, con, tokens, content, line, position, chatId, branchId):
        pass

    # Распознавание фразы на языке
    # stmt (str) - входное выражение
    # table (str[][]) таблица автозамен
    # sourceFileContent (str) контент файла
    # Возвращает
    # строку с заменами
    def recognizeStatement(self, stmt, table, sourceFileContent):
        return stmt

    # Разделяет файл и работает на замену данных
    # stmt (str) - входные данные
    # Возвращает список объектов для результата
    def splitStatement(self, stmt):
        tmp = list(filter(lambda x: len(x) > 0, stmt.split(" ")))
        result = []
        for item in tmp:
            result.append({"original": item, "lower": item.lower(), "replaced": False, "ruleIndex": -1})
        return result
        
    # Трансформирует исходную таблицу замен в более надёжную
    def transformTable(self, table):
        table_new = []
        for entry in table:
            parts = list(filter(lambda x: len(x) > 0, entry[0].split(" ")))
            if (entry[0].strip() != entry[1].strip()):
                table_new.append({"from": parts, "to": entry[1], "score": len(entry[0]) *  (-1), "registry": True, "first": False})
        return table_new
    
    # Заменяет данные в записи согласно списку в таблице
    # item (dict[]) - объекты
    # table_new (dist[]) - таблица правил
    # only_second (bool) - только второе
    # возвращает список для замены
    def replaceAccordingGenericTables(self, items, table_new, only_second):
        similarityLimit = 0.25
        replacedRuleIndex = 0
        for entry in table_new:
            replacedRuleIndex = replacedRuleIndex + 1
            from_parts = entry["from"]
            to = entry["to"]
            registry = entry["registry"]
            first = entry["first"]
#            print ("Replacing " + str(from_parts) + " to " + to)
            changed = True
            i = 0
            while (changed):
                changed = False
#                print ("Starting search")
                i = 0
                limit = 0
                if (not first):
                    limit = len(items) - len(from_parts)
                if (only_second):
                    i = 1
                    limit = min(1, len(items) - len(from_parts))
                while ((i <= limit) and (not changed)):
                    localSlice = items[i:i+len(from_parts)]
#                    print("Local slice, from: " + str(i) + ": " + str(localSlice))
                    j = 0
                    matches = True
                    while (j < len(from_parts)):
                        cmpData = localSlice[j]["lower"]
                        if (registry):
                            cmpData = localSlice[j]["original"]
                        localSliceRuleIndex = None
                        if ("ruleIndex" in localSlice[j]):
                            localSliceRuleIndex = localSlice[j]["ruleIndex"]
                        matches = matches and (distance(from_parts[j], cmpData) <= len(from_parts[j]) * similarityLimit) and (localSliceRuleIndex != replacedRuleIndex)
                        j = j + 1
                    if (matches):
#                        print ("Found entry at " + str(i))
                        changed = True
                        if (i == 0):
                            items = [{"original": to, "lower": to.lower(), "replaced": True, "ruleIndex": replacedRuleIndex}] +  items[i+len(from_parts):]
                        else:
                            items = items[:max(i, 0)] + [{"original": to, "lower": to.lower(), "replaced": True, "ruleIndex": replacedRuleIndex}] +  items[i+len(from_parts):]
                    i = i + 1
                    limit = 0
                    if (not first):
                        limit = len(items) - len(from_parts)
                    if (only_second):
                        limit = min(1, len(items) - len(from_parts))
#                print (changed)
#                print (items)
        return items
        
    # Группирует буквы в идентификаторы
    def groupLetters(self, objects):
        i = 0
        result = []
        while (i < len(objects)):
            handled = False
            if ((objects[i]["lower"] == "upper") and ((i + 1) < len(objects))):
                if (len(objects[i + 1]["lower"]) == 1):
                    o = objects[i + 1]["lower"].upper()
                    result.append({"original": o, "lower": o.lower(), "replaced": False})
                    i = i + 1
                    handled = True
            if ((objects[i]["lower"] == "lower") and ((i + 1) < len(objects)) and not handled):
                if (len(objects[i + 1]["lower"]) == 1):
                    o = objects[i + 1]["lower"].lower()
                    result.append({"original": o, "lower": o.lower(), "replaced": False})
                    i = i + 1
                    handled = True
            if (not handled):
                result.append(objects[i])
            i = i + 1
        tmp = result
        result2 = []
        i = 0
        while (i < len(tmp)):
            if ((len(tmp[i]["lower"]) == 1) and (tmp[i]["original"].isalpha())):
                j = i + 1
                buffer = tmp[i]["original"]
                isalnum = True
                while ((j < len(tmp)) and (isalnum)):
                    if ((len(tmp[j]["original"]) == 1) and ((tmp[j]["original"].isalnum()) or (tmp[j]["original"] == "_"))):
                        buffer = buffer + tmp[j]["original"]
                        j = j + 1
                    else:
                        isalnum = False
                result2.append({"original": buffer, "lower": buffer.lower(), "replaced": False})
                i = j - 1
            else:
                if ((len(tmp[i]["lower"]) == 1) and (tmp[i]["original"].isdigit())):
                    isalnum = True
                    j = i + 1
                    buffer = tmp[i]["original"]
                    while ((j < len(tmp)) and (isalnum)):
                        if ((len(tmp[j]["original"]) == 1) and (tmp[j]["original"].isdigit())):
                            buffer = buffer + tmp[j]["original"]
                            j = j + 1
                        else:
                            isalnum = False
                    result2.append({"original": buffer, "lower": buffer.lower(), "replaced": False})
                    i = j - 1
                else:
                    result2.append(tmp[i])
            i = i + 1
        return result2

    # Сливает список объектов, объединяя их в строку
    # objects - входной список
    # Возвращает строку с объединением
    def collectReplace(self, objects):
        result2 = self.groupLetters(objects)
        i = 0
        result = ""
        is_opened_single_quote = False
        is_opened_quote = False
        prev = False
        while (i < len(result2)):
            item = result2[i]["original"]
            if (i == 0):
                result = item
                if (item == "\""):
                    is_opened_quote = True
                    prev = True
                if (item == "\'"):
                    is_opened_single_quote = True
                    prev = True
                if (item == "(" or item == "[" or item == "{" or item == "~"):
                    prev = True
            else:
                if (item == ":" or item == ";" or item == " " or item == "\t" or item == "\n" or item == "\r"):
                    result = result + item
                    prev = False
                else:
                    if (item == "\""):
                        if (is_opened_quote):
                            is_opened_quote = False
                            result = result + item
                        else:
                            is_opened_quote = True
                            if (prev):
                                result = result + item
                            else:
                                result = result + " " + item
                            prev = True
                    else: 
                        if (item == "\'"):
                            if (is_opened_single_quote):
                                is_opened_single_quote = False
                                result = result + item
                            else:
                                is_opened_single_quote = True
                                if (prev):
                                    result = result + item
                                else:
                                    result = result + " " + item
                                prev = True
                        else: 
                            if (item == "(" or item == "[" or item == "{"):
                                if (prev):
                                    result = result + item
                                else:
                                    result = result + " " + item
                                prev = True
                            else: 
                                if (item == ")" or item == "]" or item == "}"):
                                    result = result + item
                                    prev = False
                                else:
                                    if (prev):
                                        result = result + item
                                    else:
                                        result = result + " " + item
                                    prev = False
            i = i + 1
        return result