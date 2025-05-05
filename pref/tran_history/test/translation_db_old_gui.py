# pref/translation_db_gui.py

import os
import math
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QFileDialog,
    QDialog, QDialogButtonBox, QLineEdit,
    QSpinBox, QTextEdit, QSizePolicy, QHeaderView,
)
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QEvent, QMimeData, QUrl, QPoint, QSettings
from PySide6.QtGui import QDrag, QKeySequence, QShortcut

from pref.tran_history.translation_db import TranslationDB

# How many entries to show per page
ENTRIES_PER_PAGE = 30

DEFAULT_EXPORT_PATH = os.path.join(os.getcwd(), "translation_db.po")

class TranslationHistoryDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = TranslationDB()
        self.current_unique_id: Optional[int] = None
        self._drag_start_pos = QPoint()

        # ─── Pagination State ─────────────────────────────────────────
        # Full list of (unique_id, msgid) tuples
        self.complete_history_entry_list = []  # type: list[tuple[int, str]]
        # Which page number is currently displayed (0-based index)
        self.current_page_number = 0
        # Total number of pages (computed)
        self.total_number_of_pages = 1
        # ────────────────────────────────────────────────────────────────

        # ─── Build UI Controls ─────────────────────────────────────────
        main_layout = QVBoxLayout(self)

        # Import / Export buttons row
        import_export_row = QHBoxLayout()
        self.import_button = QPushButton("Import PO…")
        self.export_button = QPushButton("Export PO…")
        import_export_row.addWidget(self.import_button)
        import_export_row.addWidget(self.export_button)
        import_export_row.addStretch()
        main_layout.addLayout(import_export_row)

        # History table: three columns: ID, msgid, latest version
        self.history_table = QTableWidget(0, 3)
        self.history_table.setHorizontalHeaderLabels([
            "ID", "Message (msgid)", "Latest ▶ Translation (msgstr)"
        ])
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setDragEnabled(True)
        main_layout.addWidget(self.history_table)

        # Control buttons: Close, Edit, Add, Delete
        control_buttons_row = QHBoxLayout()
        self.close_button = QPushButton("Close")
        self.edit_button = QPushButton("Edit…")
        self.add_button = QPushButton("Add…")
        self.delete_button = QPushButton("Delete")
        for btn in (
                self.close_button, self.edit_button,
                self.add_button, self.delete_button
        ):
            control_buttons_row.addWidget(btn)
        control_buttons_row.addStretch()
        main_layout.addLayout(control_buttons_row)

        # Pager controls row
        pager_layout = QHBoxLayout()
        self.first_page_button = QPushButton("|<")
        self.previous_page_button = QPushButton("<")
        self.page_info_label = QLabel()  # will be set after populate
        self.next_page_button = QPushButton(">")
        self.last_page_button = QPushButton(">|")
        for widget in (
                self.first_page_button,
                self.previous_page_button,
                self.page_info_label,
                self.next_page_button,
                self.last_page_button
        ):
            pager_layout.addWidget(widget)
        pager_layout.addStretch()
        main_layout.addLayout(pager_layout)

        # Wire UI signals
        self.import_button.clicked.connect(self._on_import)
        self.export_button.clicked.connect(self._on_export)
        self.close_button.clicked.connect(self.close)
        self.edit_button.clicked.connect(lambda: self._on_edit_entry(new=False))
        self.add_button.clicked.connect(lambda: self._on_edit_entry(new=True))
        self.delete_button.clicked.connect(self._on_delete_entry)
        self.history_table.cellClicked.connect(self._on_row_selected)

        self.first_page_button.clicked.connect(
            lambda: self._go_to_page(0)
        )
        self.previous_page_button.clicked.connect(
            lambda: self._go_to_page(self.current_page_number - 1)
        )
        self.next_page_button.clicked.connect(
            lambda: self._go_to_page(self.current_page_number + 1)
        )
        self.last_page_button.clicked.connect(
            lambda: self._go_to_page(self.total_number_of_pages - 1)
        )

        # Drag/drop support
        self.setAcceptDrops(True)
        self.history_table.viewport().installEventFilter(self)

        # Apply keyboard shortcuts
        self._apply_keyboard_shortcuts()

        # Initial population
        self._refresh_history_entries()

    def _go_to_page(self, page_index: int):
        # clamp between 0 and last page
        new_index = max(0, min(self.total_number_of_pages - 1, page_index))
        if new_index != self.current_page_number:
            self.current_page_number = new_index
            self._refresh_history_entries()

    def _refresh_history_entries(self):
        # load or rebuild the complete list only once
        if not self.complete_history_entry_list:
            self.complete_history_entry_list = self.db.list_entries()
            total_entries = len(self.complete_history_entry_list)
            self.total_number_of_pages = max(
                1,
                math.ceil(total_entries / ENTRIES_PER_PAGE)
            )

        # slice for current page
        start = self.current_page_number * ENTRIES_PER_PAGE
        end = start + ENTRIES_PER_PAGE
        page_entries = self.complete_history_entry_list[start:end]

        # populate table
        self.history_table.setRowCount(0)
        for uid, msgid in page_entries:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            id_item = QTableWidgetItem(str(uid))
            id_item.setFlags(id_item.flags() ^ Qt.ItemIsEditable)
            self.history_table.setItem(row, 0, id_item)
            msgid_item = QTableWidgetItem(msgid)
            msgid_item.setFlags(msgid_item.flags() ^ Qt.ItemIsEditable)
            self.history_table.setItem(row, 1, msgid_item)
            latest_version = self.db.get_latest_version(uid)
            latest_text = self.db.get_msgstr(uid, latest_version) or ""
            combo = QComboBox()
            combo.addItem(f"{latest_version} ▶ {latest_text}", latest_version)
            self.history_table.setCellWidget(row, 2, combo)

        # update page label
        self.page_info_label.setText(
            f"Page {self.current_page_number + 1} of {self.total_number_of_pages}"
        )

    # I/O handlers
    def _on_import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import PO…", "", "PO Files (*.po)"
        )
        if path:
            self.db.import_po(path)
            self.complete_history_entry_list = []  # force reload
            self.current_page_number = 0
            self._refresh_history_entries()

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PO…", DEFAULT_EXPORT_PATH, "PO Files (*.po)"
        )
        if path:
            self.db.export_to_po(path)

    # Shortcuts setup
    def _apply_keyboard_shortcuts(self):
        from pref.preferences import SHORTCUTS
        settings = QSettings("POEditor", "Settings")
        # map your internal names to button-click slots
        shortcut_map = {
            'first_page': (SHORTCUTS.get('page_first', "Home"),
                           self.first_page_button.click),
            'previous_page': (SHORTCUTS.get('page_prev', "PageUp"),
                              self.previous_page_button.click),
            'next_page': (SHORTCUTS.get('page_next', "PageDown"),
                          self.next_page_button.click),
            'last_page': (SHORTCUTS.get('page_last', "End"),
                          self.last_page_button.click),
        }

        for name, (seq_str, slot_fn) in shortcut_map.items():
            # create a QShortcut instead of QAction
            sc = QShortcut(QKeySequence(seq_str), self.table)
            sc.setContext(Qt.ApplicationShortcut)
            sc.activated.connect(slot_fn)

    # Row selection
    def _on_row_selected(self, row: int, _column: int):
        self.current_unique_id = int(
            self.history_table.item(row, 0).text()
        )

    # Edit/Add/Delete
    def _on_edit_entry(self, new: bool):
        dlg = _EntryDialog(
            self, self.db,
            None if new else self.current_unique_id,
            is_new=new
        )
        if dlg.exec() == QDialog.Accepted:
            self.complete_history_entry_list = []
            self._refresh_history_entries()

    def _on_delete_entry(self):
        if self.current_unique_id is not None:
            self.db.delete_entry(self.current_unique_id)
            self.complete_history_entry_list = []
            self._refresh_history_entries()

    # Drag & drop
    def dragEnterEvent(self, event: QEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.po'):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith('.po'):
                self._on_import()
                return

    def eventFilter(self, obj, ev: QEvent):
        if obj is self.history_table.viewport():
            if ev.type() == QEvent.MouseButtonPress:
                self._drag_start_pos = ev.pos()
            elif ev.type() == QEvent.MouseMove:
                if (
                        ev.buttons() & Qt.LeftButton and
                        (ev.pos() - self._drag_start_pos).manhattanLength()
                        > QApplication.startDragDistance()
                ):
                    self._start_file_drag()
        return super().eventFilter(obj, ev)

    def _start_file_drag(self):
        # ensure default export exists
        self.db.export_to_po(out_path=DEFAULT_EXPORT_PATH)
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(DEFAULT_EXPORT_PATH)])
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)


# Entry editor dialog
class _EntryDialog(QDialog):
    def __init__(self, parent, db: TranslationDB,
                 unique_id: Optional[int], is_new: bool):
        super().__init__(parent)
        self.db = db
        # Determine entry ID
        if is_new or unique_id is None:
            self.entry_id = db.add_entry("", None)
            initial_msgid = ""
        else:
            self.entry_id = unique_id
            initial_msgid = dict(db.list_entries())[self.entry_id]

        self.setWindowTitle("Edit Translation Entry")

        # Layout and controls
        form_layout = QVBoxLayout(self)
        form_layout.addWidget(QLabel(f"ID: {self.entry_id}"))
        form_layout.addWidget(QLabel("Message (msgid):"))
        self.msgid_line_edit = QLineEdit(initial_msgid)
        form_layout.addWidget(self.msgid_line_edit)

        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel("Version:"))
        self.version_spin_box = QSpinBox()
        max_version = db.get_latest_version(self.entry_id)
        self.version_spin_box.setRange(1, max_version + 10)
        self.version_spin_box.setValue(max_version + (1 if is_new else 0))
        version_layout.addWidget(self.version_spin_box)
        form_layout.addLayout(version_layout)

        form_layout.addWidget(QLabel("Translation (msgstr):"))
        self.translation_text_edit = QTextEdit()
        self.translation_text_edit.setMinimumHeight(100)
        self.translation_text_edit.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.translation_text_edit.setPlainText(
            db.get_msgstr(self.entry_id, self.version_spin_box.value()) or ""
        )
        form_layout.addWidget(self.translation_text_edit)

        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self._on_save)
        button_box.rejected.connect(self.reject)
        form_layout.addWidget(button_box)

        # Sync msgstr when version changes
        self.version_spin_box.valueChanged.connect(self._load_msgstr)

    def _load_msgstr(self, version: int):
        text = self.db.get_msgstr(self.entry_id, version) or ""
        self.translation_text_edit.setPlainText(text)

    def _on_save(self):
        new_msgid = self.msgid_line_edit.text().strip()
        version = self.version_spin_box.value()
        text = self.translation_text_edit.toPlainText().strip()

        # Update msgid if changed
        if new_msgid and new_msgid != dict(self.db.list_entries())[self.entry_id]:
            self.db.update_entry(self.entry_id, new_msgid)

        # Save or update version
        if version > self.db.get_latest_version(self.entry_id):
            self.db.add_version(self.entry_id, text, version)
        else:
            self.db.update_version(self.entry_id, version, text)

        self.accept()
