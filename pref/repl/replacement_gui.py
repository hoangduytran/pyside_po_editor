import os
import sys
import platform
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit,
    QHBoxLayout, QFileDialog, QHeaderView, QComboBox, QCheckBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import QSettings
from subcmp.line_rep_imp import ReplacementLineEdit
from subcmp.text_rep_imp import ReplacementTextEdit
from .replacement_actions import (ReplacementActions, SETTINGS_KEY)

class ReplacementsDialog(QWidget):
    SHORTCUT = 0
    REPLACEMENT = 1

    def __init__(self, parent=None):
        super().__init__(parent)
        # Use cross-platform settings key
        self.settings = QSettings("POEditor", "Replacements")
        # Initialize if unset
        if self.settings.value(SETTINGS_KEY) is None:
            self.settings.setValue(SETTINGS_KEY, [])
        self.setAcceptDrops(True)

        # Sorting state
        self.column_type = self.SHORTCUT
        self.sort_descending = False

        main_layout = QVBoxLayout(self)

        # Import/Export buttons
        top_btn_layout = QHBoxLayout()
        self.import_btn = QPushButton("Import…")
        self.export_btn = QPushButton("Export…")
        top_btn_layout.addWidget(self.import_btn)
        top_btn_layout.addWidget(self.export_btn)
        main_layout.addLayout(top_btn_layout)

        # Search layout
        search_layout = QHBoxLayout()

        # Scoped search selector
        # 1️⃣ scope combo
        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["Both", "Shortcut", "Replacement"])
        self.scope_combo.setToolTip("Search in…")
        search_layout.addWidget(self.scope_combo)

        # 2️⃣ match-case checkbox (“Aa”)
        self.match_case_cb = QCheckBox("Aa")
        self.match_case_cb.setToolTip("Match case")
        search_layout.addWidget(self.match_case_cb)

        # 3️⃣ word-boundary checkbox (“ab” underlined)
        self.match_boundary_cb = QCheckBox("ab")
        font = QFont(self.match_boundary_cb.font())
        font.setUnderline(True)
        self.match_boundary_cb.setFont(font)
        self.match_boundary_cb.setToolTip("Match whole word")
        search_layout.addWidget(self.match_boundary_cb)

        # 4️⃣ regex checkbox (“.*”)
        self.match_regex_cb = QCheckBox(".*")
        self.match_regex_cb.setToolTip("Use regular expression")
        search_layout.addWidget(self.match_regex_cb)

        # re‐fire search whenever any option toggles
        for cb in (self.match_case_cb, self.match_boundary_cb, self.match_regex_cb):
            cb.toggled.connect(lambda _: self._on_search_text_changed(self.search_field.text()))


        # Search field and navigation
        self.search_field = ReplacementLineEdit()
        self.search_field.setPlaceholderText("Search…")
        self.search_field.textChanged.connect(self._on_search_text_changed)
        search_layout.addWidget(self.search_field)

        self.find_btn = QPushButton("Find")
        self.prev_btn = QPushButton("↑")
        self.next_btn = QPushButton("↓")
        for btn in (self.find_btn, self.prev_btn, self.next_btn):
            btn.setEnabled(False)
        self.find_btn.clicked.connect(self._on_find)
        self.prev_btn.clicked.connect(self._on_prev_match)
        self.next_btn.clicked.connect(self._on_next_match)
        search_layout.addWidget(self.find_btn)
        search_layout.addWidget(self.prev_btn)
        search_layout.addWidget(self.next_btn)

        main_layout.addLayout(search_layout)

        # Replacement table
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Shortcut", "Replacement"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.sectionClicked.connect(self._on_header_clicked)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellClicked.connect(self._on_cell_activated)
        main_layout.addWidget(self.table)

        # Edit panel
        edit_layout = QVBoxLayout()
        self.edit_shortcut = QLineEdit()
        self.edit_shortcut.setPlaceholderText("Shortcut…")
        edit_layout.addWidget(QLabel("Shortcut:"))
        edit_layout.addWidget(self.edit_shortcut)

        self.edit_replacement = ReplacementTextEdit()
        self.edit_replacement.setPlaceholderText("Replacement…")
        edit_layout.addWidget(QLabel("Replacement:"))
        edit_layout.addWidget(self.edit_replacement)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("+ Add")
        self.delete_btn = QPushButton("- Delete")
        self.save_btn = QPushButton("Save")
        self.add_btn.clicked.connect(self._on_add)
        self.delete_btn.clicked.connect(self._on_delete)
        self.save_btn.clicked.connect(self._on_save_edit)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.save_btn)
        edit_layout.addLayout(btn_layout)
        main_layout.addLayout(edit_layout)

        # Hook up actions
        self.actions = ReplacementActions(self)
        self.import_btn.clicked.connect(self._on_import)
        self.export_btn.clicked.connect(self._on_export)

        # Initial population of the table
        self._replacement_refresh_table()

    def _on_import(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Replacements")
        if path:
            self.actions.import_file(self, path)

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Replacements")
        if path:
            fmt = os.path.splitext(path)[1].lstrip('.') or None
            self.actions.export_current(self, out_path=path, fmt=fmt)

    def _on_search_text_changed(self, text):
        # Determine the scope from the combo box: “both”, “shortcut” or “replacement”
        scope = self.scope_combo.currentText().lower()
        match_case = self.match_case_cb.isChecked()
        boundary   = self.match_boundary_cb.isChecked()
        regex      = self.match_regex_cb.isChecked()
        self.actions.on_search_text_changed(text, scope, match_case, boundary, regex)

    def _on_find(self):
        self.actions.on_find()

    def _on_prev_match(self):
        self.actions.on_prev_match()

    def _on_next_match(self):
        self.actions.on_next_match()

    def _on_cell_activated(self, row, col):
        shortcut = self.table.item(row, 0).text()
        replacement = self.table.item(row, 1).text()
        self.edit_shortcut.setText(shortcut)
        self.edit_replacement.setText(replacement)

    def _on_add(self):
        self.actions.on_add(self, self.edit_shortcut.text(), self.edit_replacement.text())

    def _on_delete(self):
        self.actions.on_delete(self, self.edit_shortcut.text(), self.edit_replacement.text())

    def _on_save_edit(self):
        self.actions.on_save_edit(self)

    def _replacement_refresh_table(self):
        raw = self.settings.value(SETTINGS_KEY, [])
        rows = [(e.get('replace'), e.get('with')) for e in raw if e.get('replace') and e.get('with')]
        rows.sort(key=lambda x: x[self.column_type], reverse=self.sort_descending)
        self.table.setRowCount(0)
        for s, r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(s))
            self.table.setItem(row, 1, QTableWidgetItem(r))

    def _on_header_clicked(self, section):
        self.column_type = section
        self.sort_descending = not self.sort_descending
        self._replacement_refresh_table()
