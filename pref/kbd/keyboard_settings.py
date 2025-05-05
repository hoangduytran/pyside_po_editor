# pref/keyboard_settings.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QKeySequenceEdit
)
from PySide6.QtGui     import QKeySequence, QAction
from PySide6.QtWidgets import QHeaderView, QTableWidget
from PySide6.QtCore    import QSettings, Qt
from typing import List, Tuple, Dict
# ─── Table keyboard shortcuts ──────────────────────────────────────────────────

# List of (action_key, description, default_sequence)
TABLE_ACTIONS: List[Tuple[str, str, str]] = [
    ("page_up",           "Previous Page",      "PageUp"),
    ("page_down",         "Next Page",          "PageDown"),
    ("first_row",         "First Row",          "Home"),
    ("last_row",          "Last Row",           "End"),
    ("select_shift_up",   "Select (Shift+Up)",  "Shift+Up"),
    ("select_shift_down", "Select (Shift+Down)","Shift+Down"),
    ("select_ctrl_shift", "Select (Ctrl+Click)","Ctrl+Shift"),
]


# ─── Shortcut helper ──────────────────────────────────────────────────────────

def get_shortcuts_map() -> Dict[str, str]:
    """
    Read all keys under "shortcut/" in QSettings("POEditor","Settings")
    and return a dict mapping <action_key> -> <sequence string>.
    """
    settings = QSettings("POEditor", "Settings")
    out: Dict[str, str] = {}
    for full_key in settings.allKeys():
        if full_key.startswith("shortcut/"):
            action_key = full_key.split("/", 1)[1]
            out[action_key] = settings.value(full_key)
    return out

SHORTCUTS = get_shortcuts_map()

class KeyboardSettingsTab(QWidget):
    """
    A tab that shows all the remappable keyboard shortcuts in a tree:
      - File Menu
      - Table
    Each child row has an Action name and an editable QKeySequenceEdit.
    Saves/loads to QSettings("POEditor","Settings") under "shortcut/<key>".
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("POEditor", "Settings")
        self._widgets = {}     # key -> QKeySequenceEdit

        layout = QVBoxLayout(self)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Action", "Shortcut"])

        # Stretch both columns equally (50/50)
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        layout.addWidget(self.tree)

        self._populate_tree()
        self.tree.expandAll()

    def _populate_tree(self):
        # File Menu category
        file_root = QTreeWidgetItem(self.tree, ["File Menu"])
        file_actions = [
            ("open",   "Open File",      "Ctrl+O"),
            ("save",   "Save File",      "Ctrl+S"),
            ("saveas", "Save As...",     "Ctrl+Shift+S"),
            ("prefs",  "Preferences…",   "Ctrl+,"),
            ("exit",   "Exit",           "Ctrl+Q"),
        ]
        for key, label, default in file_actions:
            self._add_action_item(file_root, key, label, default)

        # Table category
        table_root = QTreeWidgetItem(self.tree, ["Table"])
        for key, label, default in TABLE_ACTIONS:
            self._add_action_item(table_root, key, label, default)

        # ── Sort category ──────────────────────────────────────────────
        sort_root = QTreeWidgetItem(self.tree, ["Sort"])
        sort_items = [
            ("sort_untranslated", "Untranslated Items", "Ctrl+0"),
            ("sort_fuzzy", "Fuzzy Items", "Ctrl+1"),
            ("sort_by_linenum", "By Line Number", "Ctrl+2"),
            ("sort_by_id", "By ID", "Ctrl+3"),
            ("sort_by_string", "By String", "Ctrl+4"),
        ]
        for key, label, default_seq in sort_items:
            self._add_action_item(sort_root, key, label, default_seq)

    def _add_action_item(self, parent, key, label, default_seq):
        item = QTreeWidgetItem(parent, [label])
        seq_str = self.settings.value(f"shortcut/{key}", default_seq)
        editor = QKeySequenceEdit(QKeySequence(seq_str), self.tree)
        self.tree.setItemWidget(item, 1, editor)
        self._widgets[key] = editor

    def load_settings(self):
        """Populate each QKeySequenceEdit from QSettings."""
        for key, editor in self._widgets.items():
            seq = self.settings.value(f"shortcut/{key}")
            if seq:
                editor.setKeySequence(QKeySequence(seq))

    def save_settings(self):        
        """Write each edited sequence back into QSettings."""
        global SHORTCUTS
        for key, editor in self._widgets.items():
            seq = editor.keySequence().toString()
            self.settings.setValue(f"shortcut/{key}", seq)

        SHORTCUTS = get_shortcuts_map()