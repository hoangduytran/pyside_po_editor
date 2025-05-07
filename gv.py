# gv.py
# Global variables and constants for the PO Editor

from polib import (POEntry, POFile)
from PySide6.QtCore import (QSettings, Qt)
from PySide6.QtGui import (QFont, QKeyEvent, QKeySequence, QAction)
from PySide6.QtWidgets import (QTableWidget, QHeaderView)
from typing import (Optional, Any, List, Dict, Tuple, Pattern)
from pref.tran_history.translation_db import (TranslationDB)
from pref.kbd.keyboard_settings import (TABLE_ACTIONS)
from po_editor.tab_record import (TabRecord)
import re

# ─── Database & Logging ───────────────────────────────────────────────────────
db = TranslationDB()


# ─── Table Columns ────────────────────────────────────────────────────────────
MAIN_TABLE_COLUMNS: List[Tuple[str, int]] = [
    ("Message ID",   QHeaderView.Stretch),
    ("Context",      QHeaderView.ResizeToContents),
    ("Translation",  QHeaderView.Stretch),
    ("Fuzzy",        QHeaderView.ResizeToContents),
    ("Line No",      QHeaderView.ResizeToContents),
]


# ─── Default Fonts ────────────────────────────────────────────────────────────
DEFAULT_FONT       = QFont("Helvetica Neue", 18)
DEFAULT_LARGE_FONT = QFont("Helvetica Neue", 24)


# ─── Global GUI State ─────────────────────────────────────────────────────────
class MainGlobalVar:
    """
    App‐wide registry: only MRU + open tabs.
    """
    def __init__(self):
        self.window = None
        self.open_tabs: QTabWidget = None
        self.current_tab: TabRecord = None
        self.recent_files: List[str]       = []
        self.opened_file_list:   Optional[List[str]] = None
        self.exclude_flag_list:  Optional[List[str]] = None
        self.include_flag_list:  Optional[List[str]] = None     # <— add this
        self.find_pattern_list:  Optional[List[str]] = None
        self.replace_pattern_list: Optional[List[str]] = None

# singleton
main_gv = MainGlobalVar()


# ─── Replacement-Trigger Keys & Patterns ──────────────────────────────────────
ACCEPTABLE_KEYS_FOR_REPLACEMENT: Tuple[int, ...] = (
    Qt.Key_Space,
    Qt.Key_Return,
    Qt.Key_Enter,
    Qt.Key_Tab,
)

# any whitespace or punctuation that should trigger a replacement
WORD_BOUNDARY_RE: Pattern[str] = re.compile(r'(\w+)$')
TRIGGER_CHAR_RE:   Pattern[str] = re.compile(r'[\s\.,!\(\){}<>]')


def is_acceptable_key_for_replacement(ev: QKeyEvent) -> bool:
    """
    Return True if the typed character should trigger a replacement.
    """
    text = ev.text()
    return bool(TRIGGER_CHAR_RE.match(text))


# ─── Main GUI Menu & Action Specs ──────────────────────────────────────────────
# Each entry: (Menu Name, [ (action_key, label, callback_name), ... ])
MAIN_GUI_ACTION_SPECS: List[Tuple[str, List[Tuple[str, str, str]]]] = [
    (
        "File",
        [
            # ("load_startup", "Load Last File at Startup", "on_load_file_startup"),
            ("open",         "&Open…",                  "on_open_file"),
            ("save",         "&Save",                   "on_save_file"),
            ("saveas",       "Save &As…",               "on_save_file_as"),
            ("import_po",    "Import PO…",              "on_import_po"),
            ("sep",          None,                      None),
            ("prefs",        "Preferences…",            "on_open_preferences"),
            ("sep",          None,                      None),
            ("exit",         "E&xit",                   "close"),
        ],
    ),
    (
        "Edit",
        [
            (
                "Sort",
                [
                    ("sort_untranslated", "Untranslated Items", "on_sort_untranslated"),
                    ("sort_fuzzy",        "Fuzzy Items",         "on_sort_fuzzy"),
                    ("sort_lineno",       "By Line Number",      "on_sort_by_linenum"),
                    ("sort_id",           "By ID",               "on_sort_by_id"),
                    ("sort_str",          "By String",           "on_sort_by_string"),
                ],
            ),
        ],
    ),
]


def apply_table_shortcuts(
    table: QTableWidget,
    slots: Dict[str, callable]
) -> None:
    """
    Installs a QAction for each key in TABLE_ACTIONS on `table`,
    reading user shortcuts from QSettings.
    `slots` maps action_key → handler function.
    """
    settings = QSettings("POEditor", "Settings")
    for action_key, text, default_seq in TABLE_ACTIONS:
        seq = settings.value(f"shortcut/{action_key}", default_seq)
        act = QAction(text, table)
        act.setShortcut(QKeySequence(seq))
        act.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        if action_key in slots:
            act.triggered.connect(slots[action_key])
        table.addAction(act)

