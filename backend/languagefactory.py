from language import Language
from pythonlanguage import PythonLanguage

class LanguageFactory:

    def __init__(self):
        self.idsToLangs = {1 : PythonLanguage()}
        
    def create(self, langId):
        if (langId in self.idsToLangs)
            return self.idsToLangs[langId]
        else
            raise Exception("No such language")
