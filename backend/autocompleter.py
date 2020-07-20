from abc import ABC, abstractmethod


# Абстрактный класс для дополнения данных
class Autocompleter(ABC): 
    def __init__(self):
        super().__init__()

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
