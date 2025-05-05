# preferences.py
# Preferences dialog with tabs for Fonts and Text Substitutions
# Language mapping: code -> (country_code, country_name)
from PySide6.QtWidgets import (
    QDialog, QWidget, QTabWidget, QVBoxLayout, QLabel,
    QPushButton, QFontDialog, QDialogButtonBox, QComboBox
)
from PySide6.QtCore import QSettings
from PySide6.QtGui import QFont
from replacement_gui import ReplacementsDialog
import gv

class PreferencesDialog(QDialog):
    """
    Tabbed Preferences: Font settings and Text Replacements.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")

        self.settings = QSettings("POEditor", "Settings")
        # set default target language if unset
        if not self.settings.contains("targetLanguage"):
            default_lang = list(gv.LANGUAGES.values())[0][0]
            self.settings.setValue("targetLanguage", default_lang)

        tabs = QTabWidget(self)

        # --- Font Settings Tab ---
        font_tab = QWidget()
        f_layout = QVBoxLayout(font_tab)

        self.table_font_label = QLabel()
        self.table_font_btn   = QPushButton("Choose Table Font...")
        self.table_font_btn.clicked.connect(self.choose_table_font)

        self.text_font_label = QLabel()
        self.text_font_btn   = QPushButton("Choose Text Fields Font...")
        self.text_font_btn.clicked.connect(self.choose_text_font)
        # Target language selector
        self.target_label = QLabel("Target Language:")
        self.target_combo = QComboBox()
        for lang, (country, name) in gv.LANGUAGES.items():
            self.target_combo.addItem(name, country)
        f_layout.addSpacing(10)
        f_layout.addWidget(self.target_label)
        f_layout.addWidget(self.target_combo)

        f_layout.addWidget(QLabel("Table Font:"))
        f_layout.addWidget(self.table_font_label)
        f_layout.addWidget(self.table_font_btn)
        f_layout.addSpacing(10)
        f_layout.addWidget(QLabel("Text Fields Font:"))
        f_layout.addWidget(self.text_font_label)
        f_layout.addWidget(self.text_font_btn)
        f_layout.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save_preferences)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        f_layout.addWidget(buttons)

        # --- Replacements Tab ---
        repl_tab = ReplacementsDialog(self)

        tabs.addTab(font_tab, "Fonts")
        tabs.addTab(repl_tab, "Replacements")

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(tabs)

        self.load_settings()

    def load_settings(self):
        default = QFont()
        tbl_str = self.settings.value("tableFont", default.toString())
        txt_str = self.settings.value("textFont", default.toString())
        self.table_font = QFont(); self.table_font.fromString(tbl_str)
        self.text_font  = QFont(); self.text_font.fromString(txt_str)
        self.update_labels()
        # load target language
        cur = self.settings.value("targetLanguage")
        idx = self.target_combo.findData(cur)
        if idx >= 0:
            self.target_combo.setCurrentIndex(idx)

    def update_labels(self):
        self.table_font_label.setText(f"{self.table_font.family()}, {self.table_font.pointSize()}pt")
        self.text_font_label.setText(f"{self.text_font.family()}, {self.text_font.pointSize()}pt")

    def _save_preferences(self):
        """Save target language preference before closing"""
        lang = self.target_combo.currentData()
        self.settings.setValue("targetLanguage", lang)

    def choose_table_font(self):
        dlg = QFontDialog(self.table_font, self)
        dlg.setWindowTitle("Select Table Font")
        if dlg.exec() == QDialog.Accepted:
            self.table_font = dlg.selectedFont()
            self.settings.setValue("tableFont", self.table_font.toString())
            self.update_labels()

    def choose_text_font(self):
        dlg = QFontDialog(self.text_font, self)
        dlg.setWindowTitle("Select Text Fields Font")
        if dlg.exec() == QDialog.accepted:
            self.text_font = dlg.selectedFont()
            self.settings.setValue("textFont", self.text_font.toString())
            self.update_labels()
