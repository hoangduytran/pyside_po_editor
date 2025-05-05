class POEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PO File Editor")

        # Containers for dynamically created QActions
        self.qactions = {}

        # Build GUI
        self._create_widgets()
        self._create_actions()
        self._create_menu()
        self._connect_actions()

        # Load persisted shortcuts and apply them
        get_actions(main_gv)['on_apply_fonts']()
        self.apply_shortcuts()

        self.showMaximized()

    def _create_widgets(self):
        # Table
        self.table = SelectableTable(0, 3)
        self.table.setHorizontalHeaderLabels([
            "Source (msgid)",
            "Translation (msgstr)",
            "ID Lineno"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        # Editors and panels
        self.source_edit = QTextEdit(readOnly=True, fixedHeight=60)
        self.translation_edit = ReplacementTextEdit()
        self.fuzzy_toggle = QCheckBox("Needs Work")
        trans_panel = QWidget()
        vlay = QVBoxLayout(trans_panel)
        vlay.addWidget(self.translation_edit)
        hlay = QHBoxLayout(); hlay.addStretch(); hlay.addWidget(self.fuzzy_toggle)
        vlay.addLayout(hlay)

        # Suggestions and comments
        self.suggestions_list = QListWidget()
        self.suggestions_list.setWordWrap(True)
        self.suggestions_list.setUniformItemSizes(False)
        self.suggestions_list.setResizeMode(QListView.Adjust)
        self.comments_edit = QTextEdit()

        # Wire suggestor signals
        suggestor.clearSignal.connect(self.suggestions_list.clear)
        suggestor.addSignal.connect(self.suggestions_list.addItem)

        # Layout splitters
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

        sugg_panel = QWidget(); sp_layout = QVBoxLayout(sugg_panel)
        sp_layout.addWidget(QLabel("Suggestions")); sp_layout.addWidget(self.suggestions_list)
        comm_panel = QWidget(); cp_layout = QVBoxLayout(comm_panel)
        cp_layout.addWidget(QLabel("Comments")); cp_layout.addWidget(self.comments_edit)
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

        container = QWidget(); main_layout = QVBoxLayout(container)
        main_layout.addWidget(self.outer_splitter)
        self.setCentralWidget(container)

        self.set_gv_vars()

        # Ensure the bottom editors have the same width and resize together
        self._resize_editors()

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

        # Widget signals
        self.table.cellClicked.connect(acts['on_cell_clicked'])
        self.translation_edit.textChanged.connect(acts['on_translation_changed'])
        self.fuzzy_toggle.stateChanged.connect(acts['on_fuzzy_changed'])
        self.comments_edit.textChanged.connect(acts['on_comments_changed'])
        self.suggestions_list.itemDoubleClicked.connect(
            lambda itm: self.translation_edit.setPlainText(itm.text())
        )
        # Table delete & save-translation
        delete_seq = QSettings("POEditor", "Settings").value("shortcut/delete", "Del")
        delete_act = QAction(self.table)
        delete_act.setShortcut(QKeySequence(delete_seq))
        delete_act.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        delete_act.triggered.connect(on_delete_entry)
        self.table.addAction(delete_act)

        save_tr_seq = QSettings("POEditor", "Settings").value("shortcut/save_translation", "Ctrl+Return")
        save_tr_act = QAction(self.translation_edit)
        save_tr_act.setShortcut(QKeySequence(save_tr_seq))
        save_tr_act.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        save_tr_act.triggered.connect(on_translation_save)
        self.translation_edit.addAction(save_tr_act)

    # Other functions remain unchanged...
