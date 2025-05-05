# pref/preferences.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget
)

from pref.kbd.font_settings import FontSettingsTab
from pref.repl.replacement_settings import ReplacementSettingsTab
from pref.kbd.keyboard_settings import KeyboardSettingsTab
from pref.tran_history.translation_db_gui import TranslationHistoryDialog

class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.resize(600, 450)

        # Tab widget
        tabs = QTabWidget(self)
        self.font_tab        = FontSettingsTab(self)
        self.repl_tab        = ReplacementSettingsTab(self)
        self.keyboard_tab    = KeyboardSettingsTab(self)
        self.history_tab = TranslationHistoryDialog(self)

        tabs.addTab(self.font_tab,     "Fonts and Languages")
        tabs.addTab(self.repl_tab,     "Replacements")
        tabs.addTab(self.keyboard_tab, "Keyboard Mappings")
        tabs.addTab(self.history_tab, "Translation History")

        # # OK / Cancel
        # buttons = QDialogButtonBox(
        #     QDialogButtonBox.Ok, parent=self
        # )
        # # Unset default on OK button
        # ok_button = buttons.button(QDialogButtonBox.Ok)
        # ok_button.setDefault(False)
        #
        # buttons.accepted.connect(self.accept)

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        # layout.addWidget(buttons)

        # Load existing settings into each tab
        self.font_tab.load_settings()
        self.repl_tab.load_settings()
        self.keyboard_tab.load_settings()

    def save_settings(self):
        pass

    def accept(self):
        # Save each tab’s settings before closing
        self.font_tab.save_settings()
        self.repl_tab.save_settings()
        self.keyboard_tab.save_settings()
        super().accept()
