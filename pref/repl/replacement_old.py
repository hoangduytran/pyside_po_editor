# replacement_gui.py
import os
import json
import plistlib, subprocess, tempfile, os
import gv

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit,
    QHBoxLayout, QFileDialog, QSplitter, QDialog,
    QDialogButtonBox, QFormLayout,
    QTextEdit,
    QSizePolicy,
)
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QHeaderView
from subcmp.line_rep_imp import ReplacementLineEdit

def write_to_system(raw_list):
    """
    raw_list: a Python list of dicts, each with 'replace' and 'with' keys.
    This will overwrite the global NSUserDictionaryReplacementItems.
    """
    # 1) write a temp plist
    tf = tempfile.NamedTemporaryFile(suffix=".plist", delete=False)
    try:
        plistlib.dump(raw_list, tf)
        tf.flush()
        tf.close()
        # 2) import it into the global domain
        subprocess.run([
            "defaults", "import", "-g", "NSUserDictionaryReplacementItems", tf.name
        ], check=True)
    finally:
        os.unlink(tf.name)

class ReplacementsDialog(QWidget):
    """
    Widget encapsulating text replacements management.
    Displays a 2-column table, supports search, row highlighting,
    editing via bottom panel, drag-and-drop import/export, sorting,
    and add/delete via modal dialogs.
    """
    SHORTCUT    = 0
    REPLACEMENT = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("POEditor", "Replacements")
        self.settings.clear()  # start fresh
        self.setAcceptDrops(True)

        # Sorting state
        self.column_type = self.SHORTCUT
        self.sort_descending = False

        layout = QVBoxLayout(self)

        # Search field
        self.search_field = ReplacementLineEdit()
        self.search_field.setPlaceholderText("Search shortcuts or replacements...")
        self.search_field.textChanged.connect(self._on_search)
        layout.addWidget(self.search_field)

        # 2-column table
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Shortcut", "Replacement"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.sectionClicked.connect(self._on_header_clicked)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        # Bottom editor panel (hidden)
        self.editor_panel = QWidget()
        ep_layout = QVBoxLayout(self.editor_panel)
        self.edit_shortcut    = QLineEdit()
        self.edit_replacement = ReplacementLineEdit()
        self.save_btn         = QPushButton("Save")
        self.save_btn.clicked.connect(self._save_edit)
        ep_layout.addWidget(QLabel("Edit Shortcut:"))
        ep_layout.addWidget(self.edit_shortcut)
        ep_layout.addWidget(QLabel("Edit Replacement:"))
        ep_layout.addWidget(self.edit_replacement)
        ep_layout.addWidget(self.save_btn)
        self.editor_panel.hide()
        layout.addWidget(self.editor_panel)

        # Buttons: Import, Clear Search, Export, Add, Delete
        btn_layout = QHBoxLayout()
        self.import_btn       = QPushButton("Import .plist")
        self.clear_search_btn = QPushButton("Clear Search")
        self.export_btn       = QPushButton("Export…")
        self.add_btn          = QPushButton("+")
        self.delete_btn       = QPushButton("–")
        btn_layout.addWidget(self.import_btn)
        btn_layout.addWidget(self.clear_search_btn)
        btn_layout.addWidget(self.export_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

        # Connect signals
        self.import_btn.clicked.connect(self._import_plist)
        self.clear_search_btn.clicked.connect(self._clear_search)
        self.export_btn.clicked.connect(self._export_current)
        self.add_btn.clicked.connect(self._show_add_dialog)
        self.delete_btn.clicked.connect(self._delete_selected)
        self.save_btn.clicked.connect(self._save_edit)
        self.table.cellActivated.connect(self._on_cell_activated)

        # Initial population
        self._replacement_refresh_table()

    def _replacement_refresh_table(self):
        """Load substitutions from QSettings and sort."""
        self.table.setRowCount(0)
        raw = self.settings.value("NSUserDictionaryReplacementItems") or []
        rows = []
        for entry in raw:
            s = entry.get('replace')
            r = entry.get('with')
            if s and r:
                rows.append((s, r))
        rows.sort(key=lambda x: x[self.column_type], reverse=self.sort_descending)
        for s, r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(s))
            self.table.setItem(row, 1, QTableWidgetItem(r))

    def _on_search(self, text):
        text = text.lower()
        self.table.clearSelection()
        for row in range(self.table.rowCount()):
            s = self.table.item(row, 0).text().lower()
            r = self.table.item(row, 1).text().lower()
            if text and (text in s or text in r):
                self.table.selectRow(row)
        self.editor_panel.hide()

    def _on_header_clicked(self, section):
        self.column_type = section
        self.sort_descending = not self.sort_descending
        self._replacement_refresh_table()

    def _on_cell_activated(self, row, col):
        s = self.table.item(row, 0).text()
        r = self.table.item(row, 1).text()
        self.edit_shortcut.setText(s)
        self.edit_replacement.setText(r)
        self.current_edit_row = row
        self.editor_panel.show()

    def _save_edit(self):
        raw = self.settings.value("NSUserDictionaryReplacementItems") or []
        idx = getattr(self, 'current_edit_row', None)
        if isinstance(idx, int) and 0 <= idx < len(raw):
            raw[idx]['replace'] = self.edit_shortcut.text()
            raw[idx]['with']    = self.edit_replacement.text()
            self.settings.setValue("NSUserDictionaryReplacementItems", raw)
        self.editor_panel.hide()
        self._replacement_refresh_table()

    def _clear_search(self):
        self.search_field.clear()

    def _import_plist(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Text Substitutions .plist", "", "Property List (*.plist)"
        )
        if path:
            self._load_plist(path)

    def _load_plist(self, path):
        try:
            with open(path, 'rb') as f:
                data = plistlib.load(f)
            self.settings.setValue("NSUserDictionaryReplacementItems", data)
            self._replacement_refresh_table()
        except Exception as e:
            print(f"Failed to load plist: {e}")

    def _export_current(self):
        items = []
        for row in range(self.table.rowCount()):
            s = self.table.item(row, 0).text()
            r = self.table.item(row, 1).text()
            items.append({'replace': s, 'with': r})
        out_path = os.path.join(os.getcwd(), 'replacement_list.json')
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"Exported {len(items)} entries to {out_path}")
        except Exception as e:
            print(f"Failed to export replacements: {e}")

    def _show_add_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Add Replacement")
        dlg.resize(500, 300)

        # Main vertical layout
        vlay = QVBoxLayout(dlg)
        vlay.setContentsMargins(12, 12, 12, 12)
        vlay.setSpacing(8)

        # --- Shortcut field ---
        key_edit = QLineEdit(dlg)
        key_edit.setPlaceholderText("Enter the shortcut…")
        key_edit.setStyleSheet("background-color: #f0f0f0;")
        key_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        vlay.addWidget(key_edit)

        # --- Replacement area ---
        val_edit = QTextEdit(dlg)
        val_edit.setPlaceholderText("Enter the replacement text here…")
        val_edit.setStyleSheet("background-color: #f0f0f0;")
        val_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        val_edit.setAcceptRichText(False)
        vlay.addWidget(val_edit)

        # --- OK / Cancel buttons centered ---
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=dlg)
        hb = QHBoxLayout()
        hb.addStretch()
        hb.addWidget(button_box)
        hb.addStretch()
        vlay.addLayout(hb)

        button_box.accepted.connect(dlg.accept)
        button_box.rejected.connect(dlg.reject)

        if dlg.exec() == QDialog.Accepted:
            shortcut   = key_edit.text().strip()
            replacement = val_edit.toPlainText().strip()
            if shortcut and replacement:
                raw = self.settings.value("NSUserDictionaryReplacementItems") or []
                raw.append({"replace": shortcut, "with": replacement})
                self.settings.setValue("NSUserDictionaryReplacementItems", raw)
                write_to_system(raw)
                self._replacement_refresh_table()

                # Highlight the newly added row
                for row in range(self.table.rowCount()):
                    item_s = self.table.item(row, 0).text()
                    item_r = self.table.item(row, 1).text()
                    if item_s == shortcut and item_r == replacement:
                        self.table.selectRow(row)
                        self.table.scrollToItem(self.table.item(row, 0))
                        break

    def _delete_selected(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return

        # Capture the first selected index to choose neighbor later
        indices = sorted(r.row() for r in selected)
        raw = self.settings.value("NSUserDictionaryReplacementItems") or []
        for idx in reversed(indices):
            if 0 <= idx < len(raw):
                raw.pop(idx)
        self.settings.setValue("NSUserDictionaryReplacementItems", raw)
        self._replacement_refresh_table()

        # Highlight a neighbor row (above the first deleted, or the first remaining)
        if self.table.rowCount() > 0:
            target = indices[0] - 1
            if target < 0:
                target = 0
            elif target >= self.table.rowCount():
                target = self.table.rowCount() - 1
            self.table.selectRow(target)
            self.table.scrollToItem(self.table.item(target, 0))
