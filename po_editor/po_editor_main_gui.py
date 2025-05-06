
from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QWidget,
    QTableWidget, QTextEdit, QCheckBox, QLabel, QVBoxLayout, QHBoxLayout, QAbstractItemView, QAbstractSlider,
    QSizePolicy, QTableView, QToolBar
)
from PySide6.QtGui import (
    QKeySequence, QAction, QShortcut,
)
from PySide6.QtCore import (
    QSettings, QEvent, Qt, QItemSelectionModel, QSize, QTimer,
)

from gv import main_gv, MAIN_GUI_ACTION_SPECS, apply_table_shortcuts
from po_editor.po_editor_main_actions import get_actions, SelectableTable
from subcmp.text_rep_imp import ReplacementTextEdit
from sugg.translate import suggestor
from main_utils.po_ed_table_model import POFileTableModel
from pref.tran_history.versions.tran_edit_version_tbl_model import VersionTableModel
from pref.tran_history.tran_db_record import DatabasePORecord
from sugg.suggestion_controller import SuggestionController
from po_editor.po_editor_main_menu import POEditorMainMenu

from PySide6.QtWidgets import QHeaderView
from gv import MAIN_TABLE_COLUMNS

# from workspace.search_dock import SearchDock
# import resources_rc

class POEditorWindow(QMainWindow):
    def __init__(self, path:str = None):
        super().__init__()
        # self.setWindowTitle("PO File Editor")
        # Containers for dynamically created QActions
        self.qactions = {}

        # Build GUI
        self._create_widgets()
        self._create_actions()
        self.main_menu = POEditorMainMenu(self)

        self._connect_actions()

        # Load persisted shortcuts and apply them
        get_actions(main_gv)['on_apply_fonts']()
        self.apply_shortcuts()
        self.showMaximized()

        if path:
            # ─── finally, if we were given a path, defer loading it ─────
            actions = get_actions(main_gv)
            
            # wait until the event loop is running, so all widgets are fully ready
            QTimer.singleShot(20, lambda: actions['on_do_load_file'](path))

    # … inside class POEditorWindow …

    def _create_widgets(self):
        # 1) Create the Find/Replace bar (initially hidden)
        from workspace.find_replace_bar import FindReplaceBar
        self.findbar = FindReplaceBar(self)
        self.findbar.hide()

        # ─── Main table setup ────────────────────────────────────────
        self.table_model = POFileTableModel(
            column_headers=[name for (name, mode) in MAIN_TABLE_COLUMNS]
        )
        self.table = SelectableTable()
        self.table.setModel(self.table_model)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(
            QTableView.DoubleClicked
            | QTableView.SelectedClicked
            | QTableView.EditKeyPressed
            | QTableView.AnyKeyPressed
        )
        for col, (_hdr, mode) in enumerate(MAIN_TABLE_COLUMNS):
            self.table.horizontalHeader().setSectionResizeMode(col, mode)

        # ─── Editors / Translation panel ────────────────────────────
        self.source_edit = QTextEdit(readOnly=True, fixedHeight=60)
        self.translation_edit = ReplacementTextEdit()
        self.fuzzy_toggle = QCheckBox("Needs Work")
        trans_panel = QWidget()
        vlay = QVBoxLayout(trans_panel)
        vlay.addWidget(self.translation_edit)
        hlay = QHBoxLayout();
        hlay.addStretch();
        hlay.addWidget(self.fuzzy_toggle)
        vlay.addLayout(hlay)

        # ─── Suggestions + Comments ─────────────────────────────────
        empty_rec = DatabasePORecord(msgstr_versions=[])
        self.suggestion_model = VersionTableModel(empty_rec, parent=self)
        self.suggestion_version_table = QTableView()
        self.suggestion_version_table.setModel(self.suggestion_model)
        self.suggestion_version_table.setWordWrap(True)
        self.suggestion_version_table.resizeRowsToContents()
        self.suggestion_version_table.setSelectionBehavior(QTableView.SelectRows)
        self.suggestion_version_table.setSelectionMode(QAbstractItemView.SingleSelection)
        hdr2 = self.suggestion_version_table.horizontalHeader()
        hdr2.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr2.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr2.setStretchLastSection(True)
        self.suggestion_version_table.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.comments_edit = QTextEdit()

        # ─── Layout splitters ────────────────────────────────────────
        left_top = self.table
        left_bottom = QSplitter(Qt.Vertical)
        left_bottom.addWidget(self.source_edit)
        left_bottom.addWidget(trans_panel)
        left_bottom.setStretchFactor(0, 1)
        left_bottom.setStretchFactor(1, 1)

        self.left_splitter = QSplitter(Qt.Vertical)
        self.left_splitter.addWidget(left_top)
        self.left_splitter.addWidget(left_bottom)
        self.left_splitter.setStretchFactor(0, 3)
        self.left_splitter.setStretchFactor(1, 1)

        # Put the findbar *above* the suggestions table
        sugg_panel = QWidget()
        sp_layout = QVBoxLayout(sugg_panel)
        sp_layout.setContentsMargins(0, 0, 0, 0)
        sp_layout.setSpacing(2)
        sp_layout.addWidget(self.findbar)  # ← Find/Replace bar
        sp_layout.addWidget(QLabel("Suggestions"))
        sp_layout.addWidget(self.suggestion_version_table)

        comm_panel = QWidget()
        cp_layout = QVBoxLayout(comm_panel)
        cp_layout.addWidget(QLabel("Comments"))
        cp_layout.addWidget(self.comments_edit)

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(sugg_panel)
        right_splitter.addWidget(comm_panel)
        right_splitter.setStretchFactor(0, 1)
        right_splitter.setStretchFactor(1, 1)

        self.outer_splitter = QSplitter(Qt.Horizontal)
        self.outer_splitter.addWidget(self.left_splitter)
        self.outer_splitter.addWidget(right_splitter)
        self.outer_splitter.setStretchFactor(0, 3)
        self.outer_splitter.setStretchFactor(1, 1)

        # ─── Side‐toolbar tabs (unchanged) ─────────────────────────
        self.side_toolbar = QToolBar("Tabs", self)
        self.side_toolbar.setOrientation(Qt.Vertical)
        self.side_toolbar.setIconSize(QSize(24, 24))
        self.side_toolbar.setMovable(False)
        self.addToolBar(Qt.LeftToolBarArea, self.side_toolbar)

        # ─── Container & central widget ─────────────────────────────
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.outer_splitter)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("")

        self.setCentralWidget(container)
        self.set_gv_vars()
        self._resize_editors()


    def _on_show_findbar(self):
        """Called by Ctrl+F to reopen the find bar."""
        self.findbar.show()
        self.findbar.find_edit.setFocus()

    def on_cell_edited(self, topLeft, bottomRight, roles):
        # topLeft.row() and topLeft.column() point at the edited cell
        if topLeft.column() == 2:
            entry = self.table_model.entries()[topLeft.row()]
            # entry.msgstr is already updated
            # do whatever you like now — e.g.:
            self.setWindowTitle(f"* Edited: {entry.msgid}")

    def _resize_editors(self):
        """Ensure both the source and translation text editors have the same width."""
        self.source_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.translation_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Resize the splitter widget for both to have equal width
        self.left_splitter.setStretchFactor(1, 2)  # This makes both editors resize equally

    def _create_actions(self):
        """
        Instantiate all QActions as per ACTION_SPECS and store in self.qactions.
        """
        for menu_name, items in MAIN_GUI_ACTION_SPECS:
            for item in items:
                # Separator
                if item[0] == 'sep':
                    continue
                # Submenu
                if isinstance(item[1], list):
                    for sub in item[1]:
                        key, text, callback = sub
                        act = QAction(text, self)
                        self.qactions[key] = act
                else:
                    key, text, callback = item
                    act = QAction(text, self)
                    self.qactions[key] = act

    def _create_menu(self):
        """
        Build menu bar and submenus from ACTION_SPECS, inserting QActions appropriately.
        """
        menubar = self.menuBar()
        menu_objects = {}
        # Top-level menus
        for menu_name, items in MAIN_GUI_ACTION_SPECS:
            menu_objects[menu_name] = menubar.addMenu(menu_name)
        # Populate menus
        for menu_name, items in MAIN_GUI_ACTION_SPECS:
            menu = menu_objects[menu_name]
            for item in items:
                if item[0] == 'sep':
                    menu.addSeparator()
                elif isinstance(item[1], list):  # submenu
                    submenu_name = item[0]
                    submenu = menu.addMenu(submenu_name)
                    for sub in item[1]:
                        key = sub[0]
                        submenu.addAction(self.qactions[key])
                else:
                    key = item[0]
                    menu.addAction(self.qactions[key])

    def _connect_actions(self):
        """
        Connect QAction signals and widget-specific actions to their callbacks.
        """
        acts = get_actions(main_gv)
        for key, action in self.qactions.items():
            cb_name = None
            # find callback name from ACTION_SPECS
            for menu_name, items in MAIN_GUI_ACTION_SPECS:
                for item in items:
                    if isinstance(item[1], list):
                        for sub in item[1]:
                            if sub[0] == key:
                                cb_name = sub[2]
                    elif item[0] == key:
                        cb_name = item[2]
            if cb_name == 'close':
                action.triggered.connect(self.close)
            elif cb_name and cb_name in acts:
                action.triggered.connect(acts[cb_name])

        self.sugg_ctrl = SuggestionController(self, self.suggestion_model)
        self.table.selectionModel().currentRowChanged.connect(self.sugg_ctrl.on_row_change)
        self.table.clicked.connect(self._on_table_click)

        self.fuzzy_toggle.clicked.connect(acts['on_fuzzy_changed'])
        self.comments_edit.textChanged.connect(acts['on_comments_changed'])

        # --- custom context menu ---
        self.suggestion_version_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.suggestion_version_table.customContextMenuRequested.connect(
            acts['on_suggestion_context_menu']
        )
        # inside _connect_actions(), after your other .connect() calls
        self.suggestion_version_table.doubleClicked.connect(
            acts['on_suggestion_double_click']
        )

        self.suggestion_version_table.clicked.connect(
            acts['on_suggestion_selected']
        )

        # Wire suggestor signals
        suggestor.clearSignal.connect(acts['on_suggestions_clear'])
        suggestor.addSignal.connect(acts['on_suggestions_received'])

        # Table delete & save-translation
        delete_seq = QSettings("POEditor", "Settings").value("shortcut/delete", "Del")
        delete_act = QAction(self.table)
        delete_act.setShortcut(QKeySequence(delete_seq))
        delete_act.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        delete_act.triggered.connect(acts['on_delete_table_entry'])
        self.table.addAction(delete_act)

        save_tr_seq = QSettings("POEditor", "Settings").value("shortcut/save_translation", "Ctrl+Return")
        save_tr_act = QAction(self.translation_edit)
        save_tr_act.setShortcut(QKeySequence(save_tr_seq))
        save_tr_act.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        save_tr_act.triggered.connect(acts['on_save_translation'])
        self.translation_edit.addAction(save_tr_act)

        # ─── Findbar show/hide wiring ───────────────────────────────
        # when the bar’s “×” is clicked, hide it
        self.findbar.closeRequested.connect(self.findbar.hide)

        self.find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.find_shortcut.activated.connect(self._on_show_findbar)

    def _on_table_click(self, idx):
        # existing work
        acts = get_actions(main_gv)
        row, col = idx.row(), idx.column()
        acts['on_table_selection'](row, col)  # your existing logic (translate_suggestion, etc.)
        entry = main_gv.po[row]
        self.sugg_ctrl._populate_editors(entry)


    def apply_shortcuts(self):
        """
        Load and apply custom shortcuts for menu actions from QSettings.
        """
        settings = QSettings("POEditor", "Settings")
        for key, action in self.qactions.items():
            seq = settings.value(f"shortcut/{key}")
            if seq:
                action.setShortcut(QKeySequence(seq))

        # now wire your table shortcuts
        apply_table_shortcuts(self.table, {
            'page_up': self.prev_page,
            'page_down': self.next_page,
            'first_row': self.go_first_row,
            'last_row': self.go_last_row,
            'select_shift_up': self.shift_select_up,
            'select_shift_down': self.shift_select_down,
            'select_ctrl_shift': self.ctrl_click_select,
        })

    def set_gv_vars(self):
        """
        Store widget references in the global state.
        """
        gv = main_gv
        gv.table = self.table
        gv.table_model = self.table_model
        gv.source_edit = self.source_edit
        gv.translation_edit = self.translation_edit
        gv.fuzzy_toggle = self.fuzzy_toggle
        gv.suggestion_version_table = self.suggestion_version_table
        gv.suggestion_model = self.suggestion_model
        gv.comments_edit = self.comments_edit
        gv.status_bar = self.status_bar


    def showEvent(self, event):
        super().showEvent(event)
        w, h = self.width(), self.height()
        self.outer_splitter.setSizes([int(w*0.8), int(w*0.2)])
        self.left_splitter.setSizes([int(h*0.7), int(h*0.3)])

    def closeEvent(self, event: QEvent):
        if hasattr(main_gv, 'threads'):
            for thr in main_gv.threads:
                thr.quit(); thr.wait()
            main_gv.threads.clear()
        super().closeEvent(event)

    def prev_page(self):
        # e.g. scroll table up by a page
        self.table.verticalScrollBar().triggerAction(
            QAbstractSlider.SliderPageStepSub
        )

    def next_page(self):
        self.table.verticalScrollBar().triggerAction(
            QAbstractSlider.SliderPageStepAdd
        )

    def go_first_row(self):
        self.table.selectRow(0)
        self.table.scrollToItem(self.table.item(0, 0))

    def go_last_row(self):
        last = self.table.rowCount() - 1
        self.table.selectRow(last)
        self.table.scrollToItem(self.table.item(last, 0))

    def shift_select_up(self):
        # extend selection up one row
        idx = self.table.currentIndex()
        sel = self.table.selectionModel()
        sel.select(
            idx.sibling(idx.row() - 1, idx.column()),
            sel.Select | sel.Rows
        )

    def shift_select_down(self):
        idx = self.table.currentIndex()
        sel = self.table.selectionModel()
        sel.select(
            idx.sibling(idx.row() + 1, idx.column()),
            sel.Select | sel.Rows
        )

    def ctrl_click_select(self):
        # toggle current row
        row = self.table.currentRow()
        item = self.table.item(row, 0)
        self.table.selectionModel().select(
            item.index(),
            QItemSelectionModel.Toggle | QItemSelectionModel.Rows
        )

