import os
from typing import Optional, List, Tuple, Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableView, QTableWidget, QPushButton, QFileDialog, QHeaderView, QDialog,
    QCheckBox, QSplitter,
)
from PySide6.QtCore import Qt, QEvent, QPoint, QSettings, QModelIndex
from PySide6.QtGui import QKeySequence, QShortcut

from .translation_db import TranslationDB
from .tran_search_nav_bar import SearchNavBar
from pref.tran_history.versions.tran_entry_edit_dlg import _EntryDialog
from subcmp.line_rep_imp import ReplacementLineEdit
from pref.tran_history.history_table_model import HistoryTableModel
from pref.tran_history.db_msgtr_combo import ComboBoxDelegate

from pref.tran_history.tran_db_record import DatabasePORecord
# How many entries to show per page
ENTRIES_PER_PAGE = 22

DEFAULT_EXPORT_PATH = os.path.join(os.getcwd(), "translation_db.po")

# ─── SPECIFICATIONS ──────────────────────────────────────────────────────────

# 1) Search Bar specs: (attr_name, placeholder_or_text, unused_callable)
SEARCH_BAR: List[Tuple[str,str,int,str,str]] = [
    ("search_box",      "Search msgid or msgstr text", 1, "textChanged", "on_search_text_changed"),
    ("search_btn", "Find",                              0, "clicked",      "_on_search_commence"),
    ("prev_search_btn", "↑",                           0, "clicked",      "_select_previous_result"),
    ("next_search_btn", "↓",                           0, "clicked",      "_select_next_result"),
    ("show_navbar_checkbox", "Show Navigation Bar",      0, "toggled",      "_toggle_navbar_visibility"),
]

# 2) I/O buttons
IO_BUTTONS: List[Tuple[str,str,Callable]] = [
    ("import_button", "Import PO…", lambda self: self._on_import()),
    ("export_button", "Export PO…", lambda self: self._on_export()),
]

# 3) Table columns
TABLE_COLUMNS: List[Tuple[str,int]] = [
    ("ID",                                QHeaderView.ResizeToContents),
    ("Message (msgid)",                   QHeaderView.Stretch),
    ("Latest ▶ Translation (msgstr)",     QHeaderView.Stretch),
]

# 4) Control buttons
CONTROL_BUTTONS: List[Tuple[str,str,Callable]] = [
    ("close_button",  "Close",  lambda self: self.close()),
    ("clear_database",  "Clear All",  lambda self: self._clear_all()),
    ("edit_button",   "Edit…",  lambda self: self._on_edit_entry(new=False)),
    ("add_button",    "Add…",   lambda self: self._on_edit_entry(new=True)),
    ("delete_button", "Delete", lambda self: self._on_delete_entry()),
]

# 5) Pager buttons
PAGER_BUTTONS: List[Tuple[str,str,Callable[["TranslationHistoryDialog"],None]]]=[
    ("first_page_button",    "⇤", lambda s: s._go_to_page(0)),
    ("previous_page_button", "⭠",  lambda s: s._go_to_page(s.current_page_number - 1)),
    ("next_page_button",     "⭢",  lambda s: s._go_to_page(s.current_page_number + 1)),
    ("last_page_button",     "⇥", lambda s: s._go_to_page(s.total_number_of_pages - 1)),
]

# 6) Keyboard shortcuts for paging
KEYBOARD_SHORTCUTS = {
    "first_page":    ("page_first",    "Home",     "first_page_button"),
    "previous_page": ("page_prev",     "PageUp",   "previous_page_button"),
    "next_page":     ("page_next",     "PageDown", "next_page_button"),
    "last_page":     ("page_last",     "End",      "last_page_button"),
}

class TranslationHistoryDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Example data for history table
        self.btn_find: QPushButton = None
        self.btn_search_next: QPushButton = None
        self.btn_search_prev: QPushButton = None

        self.db = TranslationDB()
        self.db_record_list: List[DatabasePORecord] = self.db.list_entries()
        self.current_unique_id: Optional[int] = None
        self._drag_start_pos = QPoint()

        # ─── paging state ────────────────────────────────────────────────
        self.complete_history_entry_list: List[Tuple[int, str]] = []
        self._highlight_indices_on_page: List[int] = []
        self.current_page_number = 0
        self.total_number_of_pages = 1
        # ────────────────────────────────────────────────────────────────

        # ─── build UI ───────────────────────────────────────────────────
        main_layout = QVBoxLayout(self)

        # search state
        self._search_indices: List[int] = []
        self._current_search = -1

        # ─── SEARCH ROW BUILT FROM SPEC ──────────────────────────
        search_row = QHBoxLayout()
        for attr, label, stretch, signal, callback_name in SEARCH_BAR:
            if attr == "search_box":
                widget = ReplacementLineEdit(self)
                widget.setPlaceholderText(label)
            elif attr == "show_navbar_checkbox":  # Handle the checkbox for showing the navbar
                widget = QCheckBox(label, self)
                widget.setChecked(True)  # Default state (checked means the navbar is shown)
            else:
                widget = QPushButton(label, self)
                widget.setEnabled(False)
                if attr == 'search_btn': self.btn_find = widget
                if attr == 'prev_search_btn': self.btn_search_prev = widget
                if attr == 'next_search_btn': self.btn_search_next = widget

            # Add to layout
            search_row.addWidget(widget, stretch)

            # Stash as self.attr
            setattr(self, attr, widget)

            # Hook up signal → method
            if callback_name and signal:
                sig = getattr(widget, signal)
                cb = getattr(self, callback_name)
                sig.connect(cb)

        main_layout.addLayout(search_row)

        # 2) I/O buttons
        io_row = QHBoxLayout()
        for attr, label, cb in IO_BUTTONS:
            btn = QPushButton(label, self);
            setattr(self, attr, btn)
            btn.clicked.connect(lambda _, f=cb: f(self))
            io_row.addWidget(btn)
        io_row.addStretch()

        # — Results count label —
        self.results_label = QLabel("0 found", self)
        io_row.addWidget(self.results_label)
        main_layout.addLayout(io_row)

        # 3) Table
        # 4) Control buttons
        tbl_row = QHBoxLayout()

        # Create the model with data and columns
        self.history_model = HistoryTableModel(self.db_record_list, TABLE_COLUMNS)

        # Create the table view and set the model
        self.history_table = QTableView()
        self.history_table.setModel(self.history_model)

        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setDragEnabled(True)
        tbl_row.addWidget(self.history_table)

        # ── Create a QSplitter to allow resizing of the navbar and history table ──
        splitter = QSplitter(Qt.Horizontal, self)
        self.navbar = SearchNavBar(parent=self)  # Create navbar as QDockWidget
        # Connect the navbar's closed signal to a method
        self.navbar.navbar_closed.connect(self.on_navbar_closed)
        # Connect the record_selected signal from navbar to the handler
        self.navbar.record_selected.connect(self.on_record_selected)

        splitter.addWidget(self.history_table)  # Add history table in the splitter
        # Create and set the navbar widget inside the splitter
        splitter.addWidget(self.navbar)

        # Set the initial size of the splitter's sections using percentages
        total_width = splitter.width()
        navbar_width = int(total_width * 0.2)  # 20% width for navbar
        table_width = total_width - navbar_width  # Remaining width for table
        splitter.setSizes([table_width, navbar_width])  # Set sizes as percentages

        # Add the splitter to the main layout
        main_layout.addWidget(splitter)

        # 4) Control buttons
        ctrl_row = QHBoxLayout()
        for attr, label, cb in CONTROL_BUTTONS:
            btn = QPushButton(label, self);
            setattr(self, attr, btn)
            btn.clicked.connect(lambda _, f=cb: f(self))
            ctrl_row.addWidget(btn)
        ctrl_row.addStretch()
        main_layout.addLayout(ctrl_row)

        # 5) Pager
        pager_row = QHBoxLayout()
        for attr, label, cb in PAGER_BUTTONS:
            btn = QPushButton(label, self);
            setattr(self, attr, btn)
            btn.clicked.connect(lambda _, f=cb: f(self))
            pager_row.addWidget(btn)
        self.page_info_label = QLabel(self);
        pager_row.insertWidget(2, self.page_info_label)
        pager_row.addStretch()
        main_layout.addLayout(pager_row)

        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 0)
        main_layout.setStretch(2, 1)

        # wire table & drag/drop
        self.history_table.clicked.connect(self._on_row_selected)
        self.setAcceptDrops(True)
        self.history_table.viewport().installEventFilter(self)

        # keyboard shortcuts
        self._apply_keyboard_shortcuts()

        # initial load
        self._refresh_history_entries()

        # ────────────────────────────────────────────────────────────────

    def on_navbar_closed(self):
        """Handle the navbar being closed."""
        # When the navbar is closed, uncheck the checkbox to hide the navbar
        self.show_navbar_checkbox.setChecked(False)
        self.navbar.hide()  # Optionally hide the navbar

    def on_navbar_width_changed(self, value):
        """Called when the slider value changes to resize the SearchNavBar."""
        self.navbar.setFixedWidth(value)  # Set the width of the SearchNavBar to the slider value

    # Implement the toggle visibility method for the navbar
    def _toggle_navbar_visibility(self, checked):
        if checked:
            self.navbar.show()  # Show the navigation bar
        else:
            self.navbar.hide()  # Hide the navigation bar

    def _go_to_page(self, page_index: int):
        ni = max(0, min(self.total_number_of_pages-1, page_index))
        if ni != self.current_page_number:
            self.current_page_number = ni
            self._refresh_history_entries()

    def _refresh_history_entries(self):
        self._highlight_indices_on_page = []

        if not self.complete_history_entry_list:
            self.complete_history_entry_list = self.db.list_entries()

        total = len(self.complete_history_entry_list)
        self.total_number_of_pages = max(1, (total + ENTRIES_PER_PAGE - 1) // ENTRIES_PER_PAGE)
        self.navbar.setTotal(total)

        start = self.current_page_number * ENTRIES_PER_PAGE
        page = self.complete_history_entry_list[start:start + ENTRIES_PER_PAGE]

        # Pass the list of DatabasePORecord objects to the model
        self.history_model.refreshData(page)

        # Resize columns for better layout
        self.history_table.setColumnWidth(0, 80)  # ID column fixed width (8-9 digits wide)
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Stretch msgid column
        self.history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Stretch msgstr column

        # Set delegate for the msgstr column (column index 2)
        combo_delegate = ComboBoxDelegate(self.history_table)
        self.history_table.setItemDelegateForColumn(2, combo_delegate)
        self.history_table.setEditTriggers(QTableView.AllEditTriggers)

        # Update labels & highlights
        self.results_label.setText(f"{len(self._search_indices)} found")
        self.navbar.setFoundRecords(self._search_indices)
        self.page_info_label.setText(f"Page {self.current_page_number + 1} of {self.total_number_of_pages}")
        if self._highlight_indices_on_page and self._current_search != -1:
            self._highlight_current_search(self._search_indices[self._current_search])

    def _on_import(self, path=None):
        must_get_path = (path == None)
        if must_get_path:
            path, _ = QFileDialog.getOpenFileName(self, "Import PO…", "", "PO Files (*.po)")

        is_valid_path = path and os.path.exists(path)
        if is_valid_path:
            self.db.import_po_fast(path)
            self.complete_history_entry_list.clear()
            self.current_page_number = 0
            self._refresh_history_entries()

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export PO…", DEFAULT_EXPORT_PATH, "PO Files (*.po)")
        if path:
            self.db.export_to_po(path)

    def _apply_keyboard_shortcuts(self):
        settings = QSettings("POEditor","Settings")
        for key, (sk, default, btn_name) in KEYBOARD_SHORTCUTS.items():
            seq = settings.value(f"shortcut/{sk}", default)
            btn = getattr(self, btn_name)
            sc = QShortcut(QKeySequence(seq), self.history_table)
            sc.setContext(Qt.ApplicationShortcut)
            sc.activated.connect(btn.click)

    # ─── SEARCH METHODS ───────────────────────────────────────────────────────
    def _on_search_commence(self):
        text = self.search_box.text().strip().lower()
        self._search_indices.clear()
        self._current_search = -1
        if not text:
            self._clear_search()
            return

        # scan all entries
        if not self.complete_history_entry_list:
            self.complete_history_entry_list = self.db.list_entries()

        for idx, (uid, msgid) in enumerate(self.complete_history_entry_list):
            if text in msgid.lower():
                self._search_indices.append(idx)
            else:
                latest = self.db.get_latest_version(uid)
                mstr = (self.db.get_msgstr(uid, latest) or "").lower()
                if text in mstr:
                    self._search_indices.append(idx)

        is_found = bool(self._search_indices)
        if is_found:
            self._current_search = 0
            self._go_to_search_result()
        self.btn_search_next.setEnabled(is_found)
        self.btn_search_prev.setEnabled(is_found)

    def on_search_text_changed(self):
        """Handle text change in the search box."""
        # Enable the "Find" button when there's text in the search box, disable otherwise
        flag = bool(self.search_box.text().strip())
        self.btn_find.setEnabled(flag)

    def on_record_selected(self, global_row_index):
        """Handle the record selection and jump to the corresponding record."""
        # Calculate the page number from the global row index
        self._current_search = global_row_index
        self._go_to_search_result()

    def _go_to_search_result(self):
        # Make sure that _current_search is within bounds
        is_valid = (self._current_search != -1) or self._search_indices
        if not is_valid:
            return  # No search result selected or available

        # Get the global index from _search_indices
        global_row_index = self._search_indices[self._current_search]

        # Jump to the page containing this global row index
        page_index = global_row_index // ENTRIES_PER_PAGE
        self._go_to_page(page_index)  # Go to the page

        # Highlight the current row
        self._highlight_current_search(global_row_index)  # Highlight the row in the table

    def _select_previous_result(self):
        if not self._search_indices: return
        self._current_search = max(0, self._current_search - 1)
        self._go_to_search_result()

    def _select_next_result(self):
        if not self._search_indices: return
        self._current_search = min(len(self._search_indices)-1, self._current_search + 1)
        self._go_to_search_result()

    def _highlight_current_search(self, global_row_index=None):
        """Highlight the current search result in the table."""
        if global_row_index is None:
            global_row_index = self._search_indices[self._current_search]

        # Ensure the row index matches the correct position in the table
        row = global_row_index % ENTRIES_PER_PAGE
        self.history_table.selectRow(row)

    def _clear_search(self):
        self._search_indices.clear()
        self.history_table.clearSelection()
        self.btn_search_next.setEnabled(False)
        self.btn_search_prev.setEnabled(False)
    # ────────────────────────────────────────────────────────────────────────

    def _on_row_selected(self, index: QModelIndex):
        # Get the row index from the QModelIndex
        row = index.row()

        # Now access the record using the row index
        record = self.history_model._data[row]

        # Do something with the record, e.g., store the unique_id
        self.current_unique_id = record.unique_id
        # Add additional logic for the selected row if necessary

        # Trigger edit mode for the cell in the 'msgstr' column (column 2 in this case)
        edit_index = self.history_model.index(row, 2)  # Row, column 2 (msgstr column)
        self.history_table.edit(edit_index)

    def _clear_all(self):
        """
        Clear the model, the database, and reset the UI state.
        """
        # 1) Clear the in-memory model
        self.history_model._data.clear()

        # 2) Clear the DB
        self.db.clear_database()

        # 3) Reset paging & table
        self.current_page_number = 0
        self.complete_history_entry_list.clear()  # so _refresh fetches from DB
        self._refresh_history_entries()

        # 4) Clear any active search
        self._clear_search()

    def _on_edit_entry(self, new: bool):
        if self.current_unique_id is None:
            return  # No entry selected, do nothing

        # Find the selected record by its unique_id from db_record_list
        selected_record = next((record for record in self.db_record_list if record.unique_id == self.current_unique_id),
                               None)
        if not selected_record:
            return  # Handle case where no matching record is found (although it should always exist)

        dlg = _EntryDialog(self,
                           self.db,
                           self.db_record_list,  # Pass the entire list
                           selected_record,  # Pass the selected record
                           self.current_unique_id,
                           is_new=new)

        if dlg.exec() == QDialog.Accepted:
            # After editing, update the model with the new data
            self.history_model.refreshData(self.db_record_list)  # Update the table model with the new data

    def _on_delete_entry(self):
        has_selected_record = self.current_unique_id is not None
        if has_selected_record:
            self.db.delete_entry(self.current_unique_id)
            self.complete_history_entry_list.clear()
            self._refresh_history_entries()

    # ─── DRAG & DROP ────────────────────────────────────────────────────────
    def dragEnterEvent(self, event: QEvent):
        is_accept = False
        has_urls = event.mimeData().hasUrls()
        if has_urls:
            url_list = event.mimeData().urls()
            has_po_files = any(u.toLocalFile().lower().endswith('.po') for u in url_list)
            is_accept = has_po_files

        if is_accept:
            event.acceptProposedAction()
        else:
            event.ignore()


    def dropEvent(self, event: QEvent):
        url_list = event.mimeData().urls()
        for u in url_list:
            path = u.toLocalFile()
            is_po_file = path.lower().endswith('.po')
            if is_po_file:
                self._on_import(path=path)
                return
