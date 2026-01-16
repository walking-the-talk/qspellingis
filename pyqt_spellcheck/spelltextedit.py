from __future__ import annotations
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
Modifications by Chris York to make it play with PySpellChecker as well as pyEnchant (for use with QGIS on Windows) - including no suggestions found
"""





from qgis.PyQt.QtCore import QEvent, Qt, pyqtSlot
from qgis.PyQt.QtGui import QContextMenuEvent, QMouseEvent, QTextCursor
from qgis.PyQt.QtWidgets import QMenu, QTextEdit

from .correction_action import CorrectionAction
from .highlighter import SpellCheckHighlighter
from .spellcheckwrapper import SpellCheckWrapper


class SpellTextEdit(QTextEdit):
    """QTextEdit widget with spell checking."""

    def __init__(self, *args):
        if args and isinstance(args[0], SpellCheckWrapper):
            super().__init__(*args[1:])
            self.speller = args[0]
        else:
            super().__init__(*args)

        self.highlighter = SpellCheckHighlighter(self.document())
        if hasattr(self, "speller"):
            self.highlighter.setSpeller(self.speller)

        self.contextMenu: QMenu | None = None

    def setSpeller(self, speller: SpellCheckWrapper):
        self.speller = speller
        self.highlighter.setSpeller(self.speller)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        if event is None:
            return

        if event.button() == Qt.MouseButton.RightButton:
            event = QMouseEvent(
                QEvent.Type.MouseButtonPress,
                event.pos(),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
        super().mousePressEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent | None) -> None:
        if event is None:
            return
        suggestions = []
        self.contextMenu = self.createStandardContextMenu()
        if self.contextMenu is None:
            return

        textCursor = self.textCursor()
        textCursor.select(QTextCursor.WordUnderCursor)
        self.setTextCursor(textCursor)
        wordToCheck = textCursor.selectedText()

        if wordToCheck != "":
            
            suggestions = self.speller.suggestions(wordToCheck)
            if suggestions: #Added to handle words with no suggestions
                if len(suggestions) > 0:
                    self.contextMenu.addSeparator()
                    self.contextMenu.addMenu(self.createSuggestionsMenu(suggestions))
            else: #Added to handle words with no suggestions
                    self.contextMenu.addSeparator()
                    suggestions =["--Unknown word--",wordToCheck]
                    self.contextMenu.addMenu(self.noSuggestionsMenu(suggestions))
                    
            if not self.speller.check(wordToCheck):
                addToDictionary_action = CorrectionAction(
                    "Add to dictionary",
                    self.contextMenu,
                )
                addToDictionary_action.triggered.connect(self.addToDictionary)
                self.contextMenu.addAction(addToDictionary_action)

        self.contextMenu.exec_(event.globalPos())

    def createSuggestionsMenu(self, suggestions: list[str]):
        suggestionsMenu = QMenu("Spelling->", self)
        for word in suggestions:
            action = CorrectionAction(word, self.contextMenu)
            action.actionTriggered.connect(self.correctWord)
            suggestionsMenu.addAction(action)

        return suggestionsMenu

    #Added to handle words with no suggestions
    def noSuggestionsMenu(self, suggestions: list[str]):
        suggestionsMenu = QMenu("Spelling->", self)
        for word in suggestions:
            action = CorrectionAction(word, self.contextMenu)
            #action.actionTriggered.connect(self.correctWord)
            suggestionsMenu.addAction(action)

        return suggestionsMenu

    @pyqtSlot(str)
    def correctWord(self, word: str):
        """Replace the currently selected word with the given word."""
        textCursor = self.textCursor()
        textCursor.beginEditBlock()
        textCursor.removeSelectedText()
        textCursor.insertText(word)
        textCursor.endEditBlock()

    @pyqtSlot()
    def addToDictionary(self):
        textCursor = self.textCursor()
        new_word = textCursor.selectedText()
        self.speller.add_word(new_word)
        self.highlighter.rehighlight()
