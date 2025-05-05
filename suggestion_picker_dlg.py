from PySide6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QListWidgetItem
from PySide6.QtCore import Qt


class SuggestionPickerDialog(QDialog):
    """
    Dialog to choose from a list of suggestion versions.
    Displays version numbers and their text; double-clicking an item
    accepts the dialog and stores the selected text.
    """
    def __init__(self, parent=None, versions=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Suggestion Version")
        self.selected_text = None

        self._versions = versions or []  # list of (ver, text)

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.setWordWrap(True)

        for ver, txt in self._versions:
            item = QListWidgetItem(f"{ver}: {txt}")
            item.setData(Qt.UserRole, txt)
            self.list_widget.addItem(item)

        self.list_widget.itemDoubleClicked.connect(self._on_item_double)
        layout.addWidget(self.list_widget)

    def _on_item_double(self, item: QListWidgetItem):
        self.selected_text = item.data(Qt.UserRole)
        self.accept()
