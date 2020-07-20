from abc import ABC, abstractmethod
from reviewgramdb import *
from repoutils import *
import pymysql
import jedi


#  Делает автодополнение через jedi, используя даннные папки и содержимое
def jedi_try_autocomplete_with_folder(content, line, position, folderName):
    result = []
    try:
        script = jedi.Script(content, line, position, folderName)
        completions = script.completions()
    except jedi.NotFoundError:
        completions = []
    for completion in completions:
        result.append({
            'append_type': 'no_space',
            'complete': completion.complete,
            'name_with_symbols': completion.name_with_symbols
        })
    return result

# Пытается сделать автодополнение через jedi,  добавляя репозиторий на клонирование в процессе
def jedi_try_autocomplete(con, chatId, branchId, content, line, position):
    result = select_and_fetch_one(con, "SELECT REPO_SITE, REPO_USER_NAME, REPO_SAME_NAME FROM `repository_settings` WHERE `CHAT_ID` = " + str(chatId) + " LIMIT 1"  ,[])
    if (result is not None):
        repoSite = result[0]
        repoUserName = result[1]
        repoSameName = result[2]
        result = []
        if (is_repo_folder_exists(repoUserName, repoSameName, branchId)):
            folderName = full_repo_folder_name(repoUserName, repoSameName, branchId)
            result = jedi_try_autocomplete_with_folder(content, line, position, folderName)
        else:
            try_insert_cloning_repo_task(con, repoSite, repoUserName, repoSameName, branchId)
            result =  jedi_try_autocomplete_with_folder(content, line, position, ".")
        return result
    else:
        return []
 
# Класс для дополнения данных для питона
class PythonAutocompleter(ABC): 
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
    def getAutocompletions(self, con, tokens, content, line, position, chatId, branchId):
        return jedi_try_autocomplete(con, chatId, branchId, content, line, position)
