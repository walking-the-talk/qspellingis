# QspellinGIS
![QspellinGIS logo](/qspellinggis.png)
This is a QGIS plug-in that allows contextual spell-checking of attribute data using python spelling libraries. 

Install via QGIS plugin repository https://plugins.qgis.org/plugins/qspellingis/. 

Please also install pySpellChecker, see https://pyspellchecker.readthedocs.io/en/latest/quickstart.html

** Linux / WSL (/ Mac?)** - you can also use the Enchant library either using `pyEnchant` or by installing the package `Libenchant-2.2` (or similar).

## Set up
with pySpellChecker you can select a dictionary from those pre-installed, or British English (en-gb), which is included in the plug-in. If you have your own dictionary (Word Frequency List) you can **Bring your own Dictionary** (the last option on the drop-down languages). Please see https://pyspellchecker.readthedocs.io/en/latest/quickstart.html#how-to-build-a-new-dictionary for details of how to build a dictionary.



## Use as a macro for QGIS Attribute Forms
You can now spell-check as you enter data. The spell-checking functionality works in QGIS drag-and-drop forms or your own QGIS custom attribute forms. A `SpellCheckHelper` class is provided that can be attached to any standard `QTextEdit`, `QPlainTextEdit`, or `QLineEdit` widget. The script will automatically find all text widgets (including single-line edits) in your form and enable spell-checking, using your global QspellinGIS settings if available (falling back to the British English dictionary). It is compatible with both PyQt5 and PyQt6.

You can 'attach' QspellinGIS to any attribute form:
1. Open the layer properties and navigate to the Attribute Form tab.
2. Open the `Python Init Code Configuration` dialog.
3. Choose `Load from External File`, choose `qspellinggis_attribute_form_script.py` which you will find in this plugin's folder and then 

3. Alternatively choose `Provide code in this dialog` then copy the code from  `qspellinggis_attribute_form_script.py`  into the form's Python Function and set the `Function name` to `formOpen`
4. Set the `Function name` to `formOpen`

You may need to enable macros in order for the script to run.

## Use as a Dock Window
This is a clunky work-around for spell-checking existing records (and allows you to set up the language). For simplicity QspellinGIS works with specified visible layers (select from the drop-down) and you can either BROWSE existing records or IDENTIFY them on the canvas. When BROWSING, the plugin behaves in a similar way to the core QGIS attribute table function that allows you to pan / zoom to each feature. It works like a standard spell-checker by highlighting unknown words. With pySpellChecker it will confirm unknown words as being such. The layer does not need to be in edit mode to make changes and there is a visual check if you make changes to an attribute but don't save...

### Features
You can add new words to your Personal Word List (stored in your _home_ folder), which is a plain text file - right-click on an unknown word and select `add to dictionary` in the context menu. Your settings (default dictionary / language / PWL) are now stored in your QGIS profile settings (QSettings) instead of a local file.

pySpellChecker does not allow case-sensitive spell checking within its core dictionaries, so please bear that in mind (the plugin assumes all lower-case). Enchant is a more sophisticated spelling library with wider language support. Unfortunately Enchant does not play nicely with QGIS on Windows - Enchant works well with Linux / WSL (and probably Mac, but I don't have a Mac to test!)

## History and Credits

This plugin is (literally) the successor of QGISpell, which was a proof-of-concept plugin but doesn't work on Windows. It grew out of a need to help me correct my terrible typing skills so I have been borrowing code from across different QGIS plugins and code repositories to make it happen. For a complex ecosystem such as QGIS not to have a basic spell-checking function has been a bugbear of mine for years - if you want the best Jam, you gotta make your own... (Michelle Shocked). I found go2NextFeature (https://plugins.qgis.org/plugins/go2nextfeature/) had some basic functions for navigating records and viewing attributes - I adapted this and created the attribute form 'on-the-fly' for the selected layer based on data type. 

QspellinGIS uses pySpellChecker as it's required library but can also be used with Enchant on Linux / WSL systems. The spellchecking function has been adapted from pyqt-spellcheck to work with the additional library but also to work with pyqt6 (and therefore it is QGIS 4 compatible).

I am grateful to Stephan Sokolow (https://blog.ssokolow.com/archives/2018/03/29/an-improved-qplaintextedit-for-pyqt5/) for his original code to create a contextual spell checker using a custom python class (modifying QPlainTextEdit), which got the original plugin vaguely functional. However, it relies on Enchant so doesn't actually work within QGIS in Windows.

After the dead-end of trying to get Enchant to work (https://github.com/qgis/QGIS/issues/49934) and incorporated into OSGeo4W (https://trac.osgeo.org/osgeo4w/ticket/874), I found another tantalising possibility based on QTextEdit (https://pypi.org/project/pyqt-spellcheck/), which opened a new opportunity. This uses a wrapper for spelling libraries so I was able to adapt the code to add pySpellChecker and away it went. Being pure python, pySpellChecker has no (known) conflicts with QGIS. I also adapted pyqt-spellcheck to be PyQt6 compatible.

pySpellChecker uses generic English dictionary, with Americanised / International spellings (-ize not -ise). So I found a British English dictionary that has been collated in the form of a Word Frequency List (json) at https://github.com/dwyl/english-words

**PLEASE NOTE:** I am not a native coder, which should be obvious. Errors and poor code are probably my fault. Use at your own risk... Update from v1.1 to v2 was done with the help of Junie AI - so might have made things better, or worse.

