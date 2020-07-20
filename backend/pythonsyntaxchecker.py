from abc import ABC, abstractmethod
from reviewgramdb import *
import tempfile
import subprocess
import os

# Группирует ошибки из pyflakes в кортежи (строка, список ошибок)
def build_error_line_groups(fileName, errorContent):
    errorContentLines = errorContent.split("\n")
    errorsByLines = []
    for line in errorContentLines:
        if (line.startswith(fileName)):
            lineWithoutName = line[(len(fileName)+1):]
            secondColonPos = lineWithoutName.index(":")
            numberAsString = lineWithoutName[:secondColonPos]
            lineNo = int(numberAsString)
            tuple = (lineNo, [line])
            errorsByLines.append(tuple)
        else:
            if (len(errorsByLines) != 0):
                errorsByLines[len(errorsByLines) - 1][1].append(line)
    return errorsByLines

# Запускает PyFlakes
def run_pyflakes(name, content, start, end):
    with tempfile.NamedTemporaryFile() as temp:
        temp.write(content.encode("UTF-8"))
        temp.flush()
        fileName = temp.name
        result = subprocess.run(['pyflakes', fileName], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        errorContent = result.stderr.decode("UTF-8")
        errors = build_error_line_groups(fileName, errorContent)
        ownErrors = [error for error in errors if ((error[0] >= start) and (error[0] <= end))]
        ownErrors = list(map(lambda x:"\n".join(x[1]), ownErrors))
        ownErrors = "\n".join(ownErrors).replace(fileName, name)
        return ownErrors

# Класс для проверки синтаксиса питона
class PythonSyntaxChecker(ABC): 
    def __init__(self):
        super().__init__()

    # Проверка синтаксиса, где
    # fileName  (str) - имя файла
    # fileContent  (str) - содержимое файла
    # start (int) - начало проверяемого участка
    # end   (int) - конец проверяемого участка
    # Возвращает
    # list со списком ошибок
    def checkSyntax(self, fileName, fileContent, start, end):
        return run_pyflakes(fileName, fileContent, start, end)
