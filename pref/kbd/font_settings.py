# pref/font_settings.py
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFontDialog,
    QComboBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import QSettings
from typing import Dict, Tuple

# code -> (country_code, country_name)
LANGUAGES: Dict[str, Tuple[str, str]] = {
    'vi': ('vn', 'Việt Nam'),
    'en': ('us', 'United States'),
    'fr': ('fr', 'France'),
    'es': ('es', 'Spain'),
}


class FontSettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("POEditor", "Settings")

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Table Font:"))
        self.table_font_label = QLabel()
        layout.addWidget(self.table_font_label)
        self.table_font_btn = QPushButton("Choose Table Font…")
        layout.addWidget(self.table_font_btn)
        self.table_font_btn.clicked.connect(self.choose_table_font)

        layout.addSpacing(10)
        layout.addWidget(QLabel("Text Fields Font:"))
        self.text_font_label = QLabel()
        layout.addWidget(self.text_font_label)
        self.text_font_btn = QPushButton("Choose Text Fields Font…")
        layout.addWidget(self.text_font_btn)
        self.text_font_btn.clicked.connect(self.choose_text_font)

        # --- Target language ---
        layout.addWidget(QLabel("Target Language:"))
        self.target_combo = QComboBox()
        for lang_code, (country_code, country_name) in LANGUAGES.items():
            # store the two‑letter ISO language code as userData
            self.target_combo.addItem(country_name, lang_code)
        layout.addWidget(self.target_combo)

        layout.addStretch()

        self.table_font = QFont()
        self.text_font  = QFont()
        self.load_settings()

    def load_settings(self):
        """Populate widgets from QSettings."""
        # Fonts
        default_font = QFont()
        tbl_str = self.settings.value("tableFont", default_font.toString())
        txt_str = self.settings.value("textFont", default_font.toString())

        self.table_font = QFont()
        self.table_font.fromString(tbl_str)
        self.text_font = QFont()
        self.text_font.fromString(txt_str)
        self._update_font_labels()

        # Target language
        code = self.settings.value("targetLanguage", list(LANGUAGES.keys())[0])
        idx = self.target_combo.findData(code)
        if idx >= 0:
            self.target_combo.setCurrentIndex(idx)

    def _update_font_labels(self):
        """Refresh the labels showing the current font choices."""
        self.table_font_label.setText(f"{self.table_font.family()}, {self.table_font.pointSize()}pt")
        self.text_font_label.setText(f"{self.text_font.family()}, {self.text_font.pointSize()}pt")

    def choose_table_font(self):
        """Show a font dialog to pick the table font."""
        dlg = QFontDialog(self.table_font, self)
        dlg.setWindowTitle("Select Table Font")
        if dlg.exec() == QFontDialog.Accepted:
            self.table_font = dlg.selectedFont()
            self.settings.setValue("tableFont", self.table_font.toString())
            self._update_font_labels()

    def choose_text_font(self):
        """Show a font dialog to pick the text fields font."""
        dlg = QFontDialog(self.text_font, self)
        dlg.setWindowTitle("Select Text Fields Font")
        if dlg.exec() == QFontDialog.Accepted:
            self.text_font = dlg.selectedFont()
            self.settings.setValue("textFont", self.text_font.toString())
            self._update_font_labels()

    def save_settings(self):
        """Persist the selected target language."""
        lang_code = self.target_combo.currentData()
        self.settings.setValue("targetLanguage", lang_code)
