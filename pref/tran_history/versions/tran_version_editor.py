from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton, QSizePolicy
)
from subcmp.text_rep_imp import ReplacementTextEdit

class TransVersionEditor(QDialog):
    """
    Dialog to add or edit a single translation version.
    """
    def __init__(self, parent=None, version_id: Optional[int]=None,
                 translation_text: str="", is_add: bool=False):
        super().__init__(parent)
        self.is_add = is_add
        self.setWindowTitle("Add Version" if is_add else "Edit Version")

        layout = QVBoxLayout(self)

        # Version field
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("Version ID:"))
        self.version_spin = QSpinBox()
        self.version_spin.setMinimum(1)
        if version_id is not None:
            self.version_spin.setValue(version_id)
        if is_add:
            self.version_spin.setReadOnly(True)
        version_layout.addWidget(self.version_spin)
        layout.addLayout(version_layout)

        # Translation text
        layout.addWidget(QLabel("Translation Text:"))
        self.text_edit = ReplacementTextEdit()
        self.text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.text_edit.setPlainText(translation_text)
        if is_add:
            # select all so user can overtype
            self.text_edit.selectAll()
        layout.addWidget(self.text_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Cancel")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)
