# po_editor/po_editor_widget.py

import os
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableView, QTextEdit, QCheckBox, QLabel,
    QTableWidget, QHeaderView, QSizePolicy
)
from PySide6.QtGui     import QKeySequence, QAction
from PySide6.QtCore    import Qt, QSettings

from main_utils.po_ed_table_model import POFileTableModel
from main_utils.table_widgets     import SelectableTable
from pref.tran_history.tran_db_record import DatabasePORecord
from pref.tran_history.versions.tran_edit_version_tbl_model import VersionTableModel
from sugg.suggestion_controller   import SuggestionController

from main_utils.actions_factory import get_actions  # your factory
from gv                            import main_gv, MAIN_TABLE_COLUMNS


class POEditorWidget(QWidget):
    """
    A self‐contained widget for editing one .po file.
    Can be placed in a QTabWidget.
    """

    def __init__(self, po_path: str, parent=None):
        super().__init__(parent)
        self.po_path = po_path

        # 1) Build all the sub‐widgets
        self._build_ui()

        # 2) Hook up per-widget actions
        #    Pass `self` into the factory so callbacks target this instance
        acts = get_actions(gv=main_gv)
        self._connect_actions(acts)

        # 3) Load the file
        self.load_file(po_path)

    def _build_ui(self):
        # ─── table model & view ────────────────────────────
        self.table_model = POFileTableModel(
            column_headers=[hdr for hdr, _ in MAIN_TABLE_COLUMNS]
        )
        self.table = SelectableTable()
        self.table.setModel(self.table_model)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        # resize modes
        for col, (_, mode) in enumerate(MAIN_TABLE_COLUMNS):
            self.table.horizontalHeader().setSectionResizeMode(col, mode)

        # ─── source / translation editors ───────────────────
        self.source_edit      = QTextEdit(readOnly=True, fixedHeight=60)
        self.translation_edit = QTextEdit()  # or your ReplacementTextEdit
        self.fuzzy_toggle     = QCheckBox("Needs Work")
        trans_panel = QWidget()
        vlay = QVBoxLayout(trans_panel)
        vlay.addWidget(self.translation_edit)
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(self.fuzzy_toggle)
        vlay.addLayout(h)

        # ─── suggestions & comments ────────────────────────
        empty_rec = DatabasePORecord(msgstr_versions=[])
        self.suggestion_model         = VersionTableModel(empty_rec, parent=self)
        self.suggestion_version_table = QTableView()
        self.suggestion_version_table.setModel(self.suggestion_model)
        hdr2 = self.suggestion_version_table.horizontalHeader()
        hdr2.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr2.setSectionResizeMode(1, QHeaderView.Stretch)
        self.comments_edit = QTextEdit()

        # ─── splitters ─────────────────────────────────────
        left_bottom = QSplitter(Qt.Vertical)
        left_bottom.addWidget(self.source_edit)
        left_bottom.addWidget(trans_panel)
        left_bottom.setStretchFactor(0, 1)
        left_bottom.setStretchFactor(1, 1)

        left_splitter = QSplitter(Qt.Vertical)
        left_splitter.addWidget(self.table)
        left_splitter.addWidget(left_bottom)
        left_splitter.setStretchFactor(0, 3)
        left_splitter.setStretchFactor(1, 1)

        sugg_panel = QWidget()
        sp_lay = QVBoxLayout(sugg_panel)
        sp_lay.setContentsMargins(0,0,0,0)
        sp_lay.addWidget(QLabel("Suggestions"))
        sp_lay.addWidget(self.suggestion_version_table)

        comm_panel = QWidget()
        cp_lay = QVBoxLayout(comm_panel)
        cp_lay.addWidget(QLabel("Comments"))
        cp_lay.addWidget(self.comments_edit)

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(sugg_panel)
        right_splitter.addWidget(comm_panel)
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 1)

        # ─── final layout ───────────────────────────────────
        outer = QSplitter(Qt.Horizontal)
        outer.addWidget(left_splitter)
        outer.addWidget(right_splitter)
        outer.setStretchFactor(0, 3)
        outer.setStretchFactor(1, 1)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0)
        lay.addWidget(outer)

    def _connect_actions(self, acts: dict):
        """Wire menu‐driven and widget signals to actions_factory callbacks."""
        # File loading / saving
        load_act = QAction(self)
        load_act.triggered.connect(acts['on_open_file'])
        save_act = QAction(self)
        save_act.triggered.connect(acts['on_save_file'])
        # (you would register these with your global menu helper)

        # Table interaction
        self.table.clicked.connect(lambda idx: acts['on_table_selection'](idx.row(), idx.column()))
        self.table.selectionModel().currentRowChanged.connect(self._on_row_change)

        # Fuzzy, translation, comments
        self.fuzzy_toggle.clicked.connect(acts['on_fuzzy_changed'])
        self.translation_edit.textChanged.connect(acts['on_translation_changed'])
        self.comments_edit.textChanged.connect(acts['on_comments_changed'])

        # Suggestions
        self.suggestion_version_table.doubleClicked.connect(acts['on_suggestion_double_click'])
        self.suggestion_version_table.customContextMenuRequested.connect(
            acts['on_suggestion_context_menu']
        )

        # Sorting via menu
        # (your menu helper will call acts['on_sort_by_id'], etc.)

    def _on_row_change(self, current, previous):
        """When table row changes, update source/translation/comments."""
        row = current.row()
        acts = get_actions(main_gv, target_widget=self)
        acts['on_table_selection'](row, 0)
        # and repopulate your suggestion controller, etc.

    def load_file(self, path: str):
        """Load a .po file into this widget’s model & UI."""
        from polib import pofile
        try:
            po = pofile(path)
        except Exception as e:
            # show error…
            return
        main_gv.current_file = path
        self.table_model.setEntries(po)
        self.source_edit.clear()
        self.translation_edit.clear()
        self.fuzzy_toggle.setChecked(False)
        self.comments_edit.clear()
        # update tab label via parent QTabWidget if desired

    def save_file(self):
        """Save current .po back to disk."""
        # delegate to actions_factory
        acts = get_actions(main_gv, target_widget=self)
        acts['on_save_file']()

    # ...and expose other methods for sort, find, replace, etc...
