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


def run_checker(name, content, start, end, program, is_stdout):
    with tempfile.NamedTemporaryFile() as temp:
        temp.write(content.encode("UTF-8"))
        temp.flush()
        fileName = temp.name
        runProgram = program.copy()
        runProgram.append(fileName)
        result = subprocess.run(runProgram, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        errorContent = ""
        if (is_stdout):
            errorContent = result.stdout.decode("UTF-8")
        else:
            errorContent = result.stderr.decode("UTF-8")
        errors = build_error_line_groups(fileName, errorContent)
        ownErrors = [error for error in errors if ((error[0] >= start) and (error[0] <= end))]
        ownErrors = list(map(lambda x:"\n".join(x[1]), ownErrors))
        ownErrors = "\n".join(ownErrors).replace(fileName, name)
        return ownErrors


# Запускает PyFlakes
def run_pyflakes(name, content, start, end):
    return run_checker(name, content, start, end, ['pyflakes'], False)
        
def run_pylint(name, content, start, end):
    return run_checker(name, content, start, end, ['pylint', '--score=n'], True)

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
        pyflakes_output = run_pyflakes(fileName, fileContent, start, end)
        pylint_output = run_pylint(fileName, fileContent, start, end)
        output = ""
        if (len(pyflakes_output) != 0):
            output = output + "Результаты проверки pyflakes:\n" + pyflakes_output + "\n"
        if (len(pylint_output) != 0):
            output = output + "Результаты проверки Pylint:\n" + pylint_output + "\n"            
        return output
