"""
/***************************************************************************
MIT License

Copyright (c) 2024 Nethum Lamahewage

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

"""
Modifications by Chris York to make it play with PySpellChecker as well as pyEnchant (for use with QGIS)
"""

from collections.abc import Callable
import os.path
from pathlib import Path

try:
    from enchant import DictWithPWL, Broker
except:
    pass

from spellchecker import SpellChecker
from qgis.PyQt.QtCore import QTemporaryFile


class SpellCheckWrapper:
    """Wrapper for spell checking library."""

    def __init__(self,
        spellinglibrary: str,
        lang: str,
        personal_word_list: list[str],
        pwl_file: str,
        byod: str
    ):
        if spellinglibrary == "pyenchant":
            #Creating temporary file
            self.spellinglibrary = "pyenchant"
            lang = "en_US" if lang == None else lang
            self.file = QTemporaryFile()
            self.file.open()
            self.broker = Broker()
            self.spelldict = DictWithPWL(
                lang,
                self.file.fileName(),
            )
         
        
        else:
            if lang == "Bring-your-own" or lang == "en-gb":
                self.spelldict = SpellChecker(language = None)
                self.spelldict.word_frequency.load_dictionary(byod)   
            # elif lang == "en-gb":
                # engb = str(os.path.dirname(__file__))+"/en-gb.json"
                # self.spelldict = SpellChecker(language = None)
                # self.spelldict.word_frequency.load_dictionary(engb2)
            else:
                self.spelldict = SpellChecker(language = lang)
            self.spellinglibrary = "pyspellchecker"
        self.personal = pwl_file
        self.word_list = set(personal_word_list)
        self.load_words(self.word_list)

    def load_words(self,pwl):
        if self.spellinglibrary == "pyenchant":
            for word in pwl:
                self.spelldict.add(word)
        elif self.spellinglibrary =="pyspellchecker":
            
            self.spelldict.word_frequency.load_words(pwl)

    def get_languages(self) -> list[str]:
        if self.spellinglibrary == "pyenchant":
            languages = self.broker.list_languages()
            
        elif self.spellinglibrary =="pyspellchecker": 
            languages = self.spelldict.languages()
        return languages

    def suggestions(self, word: str) -> list[str]:
        if self.spellinglibrary == "pyenchant":
            return self.spelldict.suggest(word)
        elif self.spellinglibrary =="pyspellchecker":
            return self.spelldict.candidates(word)

    def correction(self, word: str) -> str:
        if self.spellinglibrary == "pyenchant":
            return self.spelldict.suggest(word)[0]
        elif self.spellinglibrary =="pyspellchecker":
            return self.spelldict.correction(word)

    def add_word(self, new_word: str) -> bool:
        if self.check(new_word):
            return False
        self.word_list.add(new_word)
        self.addToDictionary(new_word)
        if self.spellinglibrary == "pyenchant":
            self.spelldict.add(new_word)
        elif self.spellinglibrary =="pyspellchecker":
            self.spelldict.word_frequency.add(new_word)
        return True

    def check(self, word: str) -> bool:
        if self.spellinglibrary == "pyenchant":
            return self.spelldict.check(word)
        elif self.spellinglibrary =="pyspellchecker":
            return self.spelldict.word_usage_frequency(word.lower())!=0 #note that this is now agnostic about capitalisation by converting to lower case!
        
    def getNewWords(self) -> set[str]:
        return self.word_list

    def addToDictionary(self, new_word: str):
        with open(self.personal, 'a') as f:
            f.write("\n" + new_word)