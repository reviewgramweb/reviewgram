from abc import ABC, abstractmethod
 
# Абстрактный класс языка для работы с ними
class Language(ABC): 
    def __init__(self):
        super().__init__()
    
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
