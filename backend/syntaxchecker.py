from abc import ABC, abstractmethod


# Абстрактный класс для проверки синтаксиса
class SyntaxChecker(ABC): 
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
