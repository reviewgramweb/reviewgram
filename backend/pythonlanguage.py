from language import Language
from pythonautocompleter import PythonAutocompleter
from pythonsyntaxchecker import PythonSyntaxChecker
 
# Абстрактный класс языка для работы с ними
class PythonLanguage(Language): 
    def __init__(self):
        self.autocompleter = PythonAutocompleter()
        self.syntaxChecker = PythonSyntaxChecker()
        super().__init__()
    
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
