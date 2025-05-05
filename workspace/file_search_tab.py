# workspace/file_search_tab.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel,
    QFileDialog, QTreeView, QFileSystemModel
)
from PySide6.QtCore import Signal, QDir

class FileSearchTab(QWidget):
    """
    Tab for cross-file search/replace:
     • Find/Replace QLineEdits
     • Include / Exclude extensions QLineEdits
     • Directory picker + Browse button
     • QTreeView showing the directory tree
    """
    fileActivated = Signal(str)   # path

    def __init__(self, parent=None):
        super().__init__(parent)
        L = QVBoxLayout(self)

        # — find/replace + filters —
        top = QHBoxLayout()
        self.find_edit    = QLineEdit(); self.find_edit.setPlaceholderText("Find …")
        self.replace_edit = QLineEdit(); self.replace_edit.setPlaceholderText("Replace …")
        self.inc_ext      = QLineEdit(); self.inc_ext.setPlaceholderText("include *.py;*.txt")
        self.exc_ext      = QLineEdit(); self.exc_ext.setPlaceholderText("exclude *.log")
        top.addWidget(self.find_edit)
        top.addWidget(self.replace_edit)
        top.addWidget(QLabel("Inc:"))
        top.addWidget(self.inc_ext)
        top.addWidget(QLabel("Exc:"))
        top.addWidget(self.exc_ext)
        L.addLayout(top)

        # — directory selector —
        drow = QHBoxLayout()
        self.dir_edit = QLineEdit()
        btn = QPushButton("Browse…")
        btn.clicked.connect(self._browse)
        drow.addWidget(self.dir_edit)
        drow.addWidget(btn)
        L.addLayout(drow)

        # — file tree —
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath(QDir.rootPath())
        self.tree = QTreeView()
        self.tree.setModel(self.fs_model)
        L.addWidget(self.tree)

        # double‐click to activate
        self.tree.doubleClicked.connect(self._on_double_click)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Select directory")
        if d:
            self.dir_edit.setText(d)
            self.tree.setRootIndex(self.fs_model.index(d))

    def _on_double_click(self, idx):
        path = self.fs_model.filePath(idx)
        self.fileActivated.emit(path)
