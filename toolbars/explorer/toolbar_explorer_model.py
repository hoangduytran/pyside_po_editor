# toolbars/explorer/toolbar_explorer_model.py

import os
from PySide6.QtWidgets import QFileSystemModel
from PySide6.QtGui      import QBrush, QColor
from PySide6.QtCore     import Qt

class HighlightingFileSystemModel(QFileSystemModel):
    """Extends QFileSystemModel to give .po files a special background."""
    def data(self, index, role):
        if role == Qt.BackgroundRole:
            path = self.filePath(index)
            if os.path.isfile(path) and path.lower().endswith(".po"):
                return QBrush(QColor("#fff2b8"))  # light yellow
        return super().data(index, role)
