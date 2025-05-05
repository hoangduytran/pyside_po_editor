# po_editor/tab_record.py

from dataclasses import dataclass, field
from typing    import Optional, List, Any
from polib     import POFile, POEntry
from PySide6.QtWidgets import (
    QTableWidget,
    QTextEdit,
    QCheckBox,
    QTableView,
)
from main_utils.po_ed_table_model import POFileTableModel

@dataclass
class TabRecord:
    """
    Holds all per-tab state for a single .po file editor instance.
    """

    # — File on disk & naming —
    file_path:      Optional[str]            = None  # full path to the .po file
    file_name:      Optional[str]            = None  # base name for the tab label
    po_file:        Optional[POFile]         = None  # parsed polib POFile object
    current_dir:    Optional[str]            = None  # directory containing the file

    # — Table & model —
    table:          Optional[QTableWidget]   = None
    table_model:    Optional[POFileTableModel]= None
    current_row:    Optional[int]            = None  # currently selected row
    current_entry:  Optional[POEntry]        = None  # the POEntry at current_row

    # — Recently opened files in this tab (if you track them) —
    opened_files:   List[str]                = field(default_factory=list)

    # — Search/replace flags (per-tab history) —
    exclude_flags:  List[str]                = field(default_factory=list)
    include_flags:  List[str]                = field(default_factory=list)
    find_patterns:  List[str]                = field(default_factory=list)
    replace_patterns:List[str]               = field(default_factory=list)

    # — Suggestion pane —
    suggestion_model: Optional[Any]          = None  # e.g. VersionTableModel
    suggestion_view:  Optional[QTableView]   = None
    current_sugg_row: Optional[int]          = None
    current_sugg_rec: Optional[Any]          = None

    # — Editors & controls —
    source_edit:      Optional[QTextEdit]    = None
    translation_edit: Optional[QTextEdit]    = None
    comments_edit:    Optional[QTextEdit]    = None
    fuzzy_toggle:     Optional[QCheckBox]    = None

    # — The widget instance itself —
    widget:           Any                    = None  # your POEditorWidget

    # — Dirty/unsaved-changes flag —
    dirty:           bool                    = False
