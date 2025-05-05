class TranslationHistoryDialog(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = TranslationDB()
        self.current_unique_id: Optional[int] = None
        self._drag_start_pos = QPoint()

        # ─── paging state ────────────────────────────────────────────────
        self.complete_history_entry_list: List[Tuple[int,str]] = []
        self.current_page_number = 0
        self.total_number_of_pages = 1
        # ────────────────────────────────────────────────────────────────

        # ─── build UI ───────────────────────────────────────────────────
        main_layout = QHBoxLayout(self)  # Using QHBoxLayout to split space

        # ─── SEARCH ROW BUILT FROM SPEC ──────────────────────────
        search_row = QHBoxLayout()
        for attr, label, stretch, signal, callback_name in SEARCH_BAR:
            if attr == "search_box":
                widget = QLineEdit(self)
                widget.setPlaceholderText(label)
            else:
                widget = QPushButton(label, self)
            search_row.addWidget(widget, stretch)
            setattr(self, attr, widget)
            if callback_name and signal:
                sig = getattr(widget, signal)
                cb = getattr(self, callback_name)
                sig.connect(cb)
        main_layout.addLayout(search_row)

        # ─── Results count label ───────────────────────────────────────
        self.results_label = QLabel("0 found", self)
        main_layout.addWidget(self.results_label)

        # ─── Add SearchNavBar (Vertical) ────────────────────────────────
        self.navbar = SearchNavBar(self)
        main_layout.addWidget(self.navbar)

        # ─── Table ─────────────────────────────────────────────────────
        self.history_table = QTableWidget(0, len(TABLE_COLUMNS))
        self.history_table.setHorizontalHeaderLabels([h for h, _ in TABLE_COLUMNS])
        hdr = self.history_table.horizontalHeader()
        for i, (_, mode) in enumerate(TABLE_COLUMNS):
            hdr.setSectionResizeMode(i, mode)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.history_table.setDragEnabled(True)
        main_layout.addWidget(self.history_table)

        # ─── Control buttons ───────────────────────────────────────────
        ctrl_row = QHBoxLayout()
        for attr, label, cb in CONTROL_BUTTONS:
            btn = QPushButton(label, self)
            setattr(self, attr, btn)
            btn.clicked.connect(lambda _, f=cb: f(self))
            ctrl_row.addWidget(btn)
        ctrl_row.addStretch()
        main_layout.addLayout(ctrl_row)

        # ─── Pager ──────────────────────────────────────────────────────
        pager_row = QHBoxLayout()
        for attr, label, cb in PAGER_BUTTONS:
            btn = QPushButton(label, self)
            setattr(self, attr, btn)
            btn.clicked.connect(lambda _, f=cb: f(self))
            pager_row.addWidget(btn)
        self.page_info_label = QLabel(self)
        pager_row.insertWidget(2, self.page_info_label)
        pager_row.addStretch()
        main_layout.addLayout(pager_row)

        # ─── Final Layout Setup ────────────────────────────────────────
        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 0)
        main_layout.setStretch(2, 1)

        # wire table & drag/drop
        self.history_table.cellClicked.connect(self._on_row_selected)
        self.setAcceptDrops(True)
        self.history_table.viewport().installEventFilter(self)

        # keyboard shortcuts
        self._apply_keyboard_shortcuts()

        # initial load
        self._refresh_history_entries()

    def _refresh_history_entries(self):
        if not self.complete_history_entry_list:
            self.complete_history_entry_list = self.db.list_entries()

        total = len(self.complete_history_entry_list)
        self.total_number_of_pages = max(1, (total + ENTRIES_PER_PAGE - 1) // ENTRIES_PER_PAGE)

        # Tell the navbar how many slots to draw
        self.navbar.setTotal(total)

        start_idx = self.current_page_number * ENTRIES_PER_PAGE
        end_idx = start_idx + ENTRIES_PER_PAGE
        page_entries = self.complete_history_entry_list[start_idx:end_idx]

        self.history_table.setRowCount(0)

        # Prepare list of row indices to highlight based on search results
        self._highlight_indices_on_page = []

        for idx, (uid, msgid) in enumerate(page_entries):
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            it0 = QTableWidgetItem(str(uid))
            it0.setFlags(it0.flags() ^ Qt.ItemIsEditable)
            self.history_table.setItem(row, 0, it0)
            it1 = QTableWidgetItem(msgid)
            it1.setFlags(it1.flags() ^ Qt.ItemIsEditable)
            self.history_table.setItem(row, 1, it1)

            # Get the latest translation for the entry
            ver = self.db.get_latest_version(uid)
            txt = self.db.get_msgstr(uid, ver) or ""
            combo = QComboBox()
            combo.addItem(f"{ver} ▶ {txt}", ver)
            self.history_table.setCellWidget(row, 2, combo)

            # Check if this row should be highlighted
            global_row_index = start_idx + idx
            if global_row_index in self._search_indices:
                self._highlight_indices_on_page.append(idx)  # Mark the row index for highlighting

        # Update the search result label
        self.results_label.setText(f"{len(self._search_indices)} found")

        # Update the side navigation bar with highlighted results
        self.navbar.setHighlights(self._search_indices)

        # Update page label
        self.page_info_label.setText(f"Page {self.current_page_number + 1} of {self.total_number_of_pages}")

        if self._highlight_indices_on_page:
            self._highlight_current_search()
