# pref/replacement_settings.py
from PySide6.QtWidgets import QWidget, QVBoxLayout
from .replacement_gui import ReplacementsDialog  # your existing dialog widget

class ReplacementSettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        # embed your ReplacementsDialog directly
        self.dialog = ReplacementsDialog(self)
        layout.addWidget(self.dialog)

    def load_settings(self):
        # ensure it shows the latest
        self.dialog._replacement_refresh_table()

    def save_settings(self):
        # no-op: the dialog writes back to QSettings itself
        pass
