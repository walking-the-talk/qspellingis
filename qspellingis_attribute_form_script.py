from qgis.PyQt.QtWidgets import QTextEdit, QPlainTextEdit, QWidget, QLineEdit
from qgis.PyQt.QtCore import QSettings
from qgis.core import Qgis, QgsMessageLog
import os
import sys

# Try to import from the plugin folder, handling various possible installation names
try:
    from qspellingis.pyqt_spellcheck import SpellCheckHelper, SpellCheckWrapper
except ImportError:
    try:
        from pyqt_spellcheck import SpellCheckHelper, SpellCheckWrapper
    except ImportError:
        # Fallback for when the plugin folder might be named differently
        # or not in the path as expected
        import inspect
        cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0], "")))
        if cmd_subfolder not in sys.path:
            sys.path.insert(0, cmd_subfolder)
        try:
            from pyqt_spellcheck import SpellCheckHelper, SpellCheckWrapper
        except ImportError:
            QgsMessageLog.logMessage("QspellinGIS: Could not find pyqt_spellcheck modules", "Plugins", Qgis.Error)
            SpellCheckHelper, SpellCheckWrapper = None, None

def formOpen(dialog, layer, feature):
    """
    Hook function for QGIS attribute form.
    To use this:
    1. Open Layer Properties -> Attributes Form
    2. Change 'Python Init Function' to 'formOpen'
    3. Ensure 'qspellingis' plugin is installed and enabled.
    """
    if SpellCheckHelper is None or SpellCheckWrapper is None:
        return

    # Define settings for the speller from QSettings with fallbacks
    settings = QSettings()
    spelling_library = settings.value("qspellingis/spelling_library", "pyspellchecker")
    language = settings.value("qspellingis/language", "en-gb")
    
    # Path to your personal word list
    default_pwl = os.path.join(os.path.expanduser("~"), "qspellingis_pwl.txt")
    pwl_path = settings.value("qspellingis/pwl_path", default_pwl)
    
    # BYOD file
    byod_file = settings.value("qspellingis/byod_file", "")
    
    # Load existing words from the personal word list
    personal_words = []
    if os.path.exists(pwl_path):
        try:
            with open(pwl_path, 'r') as f:
                personal_words = [line.strip() for line in f if line.strip()]
        except Exception as e:
            QgsMessageLog.logMessage(f"QspellinGIS: Error reading PWL: {str(e)}", "Plugins", Qgis.Warning)
    
    # Initialize the speller
    try:
        speller = SpellCheckWrapper(spelling_library, language, personal_words, pwl_path, byod_file)
    except Exception as e:
        QgsMessageLog.logMessage(f"QspellinGIS: Error initializing speller: {str(e)}", "Plugins", Qgis.Error)
        return
    
    # Find all text edit widgets in the dialog and attach the spell checker
    # This includes QTextEdit, QPlainTextEdit, and QLineEdit
    found_any = False
    
    # Some QGIS widgets are wrappers (like QgsTextEdit)
    text_widgets = dialog.findChildren(QTextEdit) + dialog.findChildren(QPlainTextEdit) + dialog.findChildren(QLineEdit)
    
    for widget in text_widgets:
        # Attach the helper if not already attached
        # We check children to avoid duplicate attachment
        if not any(isinstance(child, SpellCheckHelper) for child in widget.children()):
            SpellCheckHelper(widget, speller)
            found_any = True

    if not found_any:
        # If no standard text edits found, it might be a custom form or QgsTextEdit wrappers
        # that don't expose their children directly in some versions.
        # But usually the above works.
        pass
