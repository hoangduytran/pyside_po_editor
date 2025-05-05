from pref.tran_history.tran_db_record import DatabasePORecord
from .tran_edit_version_tbl_model import VersionTableModel
from .tran_version_actions import (
    add_version, delete_version, edit_version, save_versions, cancel_edit
)
from .tran_version_editor import TransVersionEditor

from typing import List
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QDialog,
    QPushButton, QTableView, QSizePolicy, QTextEdit, QHeaderView
)
from PySide6.QtCore import Qt


class _EntryDialog(QDialog):
    def __init__(
        self,
        parent,
        db,
        db_record_list: List[DatabasePORecord],
        entry_record: DatabasePORecord,
        index: int,
        is_new: bool
    ):
        super().__init__(parent)
        self.db = db
        self.db_record_list = db_record_list
        self.entry_record = entry_record
        self.record_index = index
        self.setWindowTitle("Edit Translation Entry")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"ID: {entry_record.unique_id}"))

        # msgid field
        layout.addWidget(QLabel("Message (msgid):"))
        self.msgid_edit = QTextEdit()
        self.msgid_edit.setPlainText(entry_record.msgid)
        self.msgid_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        self.msgid_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout.addWidget(self.msgid_edit)

        # Versions table
        layout.addWidget(QLabel("Translation Versions:"))
        self.version_model = VersionTableModel(self.entry_record, parent=self)
        self.version_table = QTableView()
        self.version_table.setModel(self.version_model)
        self.version_table.setSelectionBehavior(QTableView.SelectRows)
        self.version_table.setSelectionMode(QTableView.MultiSelection)

        header = self.version_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setStretchLastSection(True)

        self.version_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.version_table)

        # Action buttons
        btn_layout = QHBoxLayout()
        self.btn_add    = QPushButton("Add")
        self.btn_del    = QPushButton("Del")
        self.btn_edit   = QPushButton("Edit")
        self.btn_save   = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")

        for btn in (self.btn_add, self.btn_del, self.btn_edit):
            btn_layout.addWidget(btn)
        btn_layout.addStretch()
        for btn in (self.btn_save, self.btn_cancel):
            btn_layout.addWidget(btn)

        layout.addLayout(btn_layout)

        # Signals
        self.btn_add.clicked.connect(self.on_add)
        self.btn_del.clicked.connect(self.on_delete)
        self.btn_edit.clicked.connect(self.on_edit)
        self.btn_save.clicked.connect(self.on_save)
        self.btn_cancel.clicked.connect(self.on_cancel)
        self.version_table.doubleClicked.connect(self.on_edit)

    def on_add(self):
        # open editor
        next_ver = max((v for v, _ in self.entry_record.msgstr_versions), default=0) + 1
        prev_text = ""
        dlg = TransVersionEditor(self, next_ver, prev_text, is_add=True)
        if dlg.exec() == QDialog.Accepted:
            rec = add_version(self.entry_record, dlg.text_edit.toPlainText())
            # refresh table
            self.version_model.setRecord(rec)

    def on_delete(self):
        rows = {idx.row() for idx in self.version_table.selectionModel().selectedRows()}
        for row in sorted(rows, reverse=True):
            ver_id, _ = self.entry_record.msgstr_versions[row]
            rec = delete_version(self.entry_record, ver_id)
        self.version_model.setRecord(rec)

    def on_edit(self):
        sel = self.version_table.selectionModel().selectedRows()
        if not sel:
            return
        row = sel[0].row()
        ver_id, text = self.entry_record.msgstr_versions[row]
        dlg = TransVersionEditor(self, ver_id, text, is_add=False)
        if dlg.exec() == QDialog.Accepted:
            rec = edit_version(self.entry_record, ver_id, dlg.text_edit.toPlainText())
            self.version_model.setRecord(rec)

    def on_save(self):
        save_versions(self.entry_record, self.db.conn)
        self.accept()

    def on_cancel(self):
        cancel_edit()
        self.reject()

    def reject(self):
        print("Dialog was cancelled!")
        super().reject()
