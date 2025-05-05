# workspace/workspace_tab.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton,
    QCheckBox, QListWidget
)
from PySide6.QtCore import Signal

class WorkspaceTab(QWidget):
    """
    Tab for in-document search/replace:
     • QLineEdit for Find
     • QLineEdit for Replace
     • Checkboxes: match-case, word-boundary, regex
     • QListWidget showing hit locations (row, col)
    """
    hitActivated = Signal(int, int)   # row, col

    def __init__(self, parent=None):
        super().__init__(parent)
        L = QVBoxLayout(self)

        # — find/replace row + options —
        row = QHBoxLayout()
        self.find_edit        = QLineEdit(); self.find_edit.setPlaceholderText("Find …")
        self.replace_edit     = QLineEdit(); self.replace_edit.setPlaceholderText("Replace …")
        self.match_case_cb    = QCheckBox("Aa")
        self.word_boundary_cb = QCheckBox(r"\b")
        self.regex_cb         = QCheckBox(".*")
        self.do_replace_btn   = QPushButton("Replace All")
        row.addWidget(self.find_edit)
        row.addWidget(self.replace_edit)
        row.addWidget(self.match_case_cb)
        row.addWidget(self.word_boundary_cb)
        row.addWidget(self.regex_cb)
        row.addWidget(self.do_replace_btn)
        L.addLayout(row)

        # — list of hits —
        self.hit_list = QListWidget()
        L.addWidget(self.hit_list)

        # connect clicks
        self.hit_list.itemClicked.connect(self._on_hit_clicked)

    def _on_hit_clicked(self, item):
        # assume text is "Row 12, Col 5"
        parts = item.text().split()
        row = int(parts[1].rstrip(","))
        col = int(parts[3])
        self.hitActivated.emit(row, col)
