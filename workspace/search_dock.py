# # workspace/search_dock.py
#
# from PySide6.QtWidgets import QDockWidget, QTabWidget
# from PySide6.QtCore    import Qt
# from .workspace_tab    import WorkspaceTab
# from .file_search_tab  import FileSearchTab
# # workspace/search_dock.py

from PySide6.QtWidgets import (
    QDockWidget, QWidget, QHBoxLayout, QVBoxLayout,
    QToolButton, QStackedWidget, QLineEdit, QLabel,
    QListWidget, QCheckBox, QPushButton, QSizePolicy
)
from PySide6.QtCore    import Qt, Signal
from PySide6.QtGui     import QIcon

class SearchDock(QDockWidget):
    """
    A dockable, slide-out panel with:
     • A black vertical icon bar on the left
     • A StackedWidget on the right whose pages you can swap in/out
    """
    # expose the search page’s “hit clicked” for your main window
    hitActivated = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__("Search", parent)
        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        # ─── root widget & layout ───────────────────────────────
        root = QWidget(self)
        hlay = QHBoxLayout(root)
        hlay.setContentsMargins(0,0,0,0)
        hlay.setSpacing(0)

        # ─── left sidebar ────────────────────────────────────────
        self.sidebar = QWidget(root)
        self.sidebar.setStyleSheet("background: #222;")  # dark background
        self.sidebar.setFixedWidth(40)
        vbar = QVBoxLayout(self.sidebar)
        vbar.setContentsMargins(0,8,0,8)
        vbar.setSpacing(4)

        # icon buttons
        self.btn_search = QToolButton(self.sidebar)
        icon_image = QIcon(":/icons/workspace.svg")
        self.btn_search.setIcon(icon_image)
        self.btn_search.setCheckable(True)
        self.btn_search.setToolTip("Workspace Search")
        vbar.addWidget(self.btn_search)

        # spacer so further buttons go to top
        vbar.addStretch()

        hlay.addWidget(self.sidebar)

        # ─── right stack ─────────────────────────────────────────
        self.stack = QStackedWidget(root)
        hlay.addWidget(self.stack, 1)

        # build pages
        self._build_search_page()
        # you can call self._build_another_page() and self.stack.addWidget(page)

        # wiring
        self.btn_search.toggled.connect(lambda on: self._show_page(0) if on else self.hide())
        self.hide()  # initially closed

        self.setWidget(root)

    def _build_search_page(self):
        """Page 0: in-document search / replace."""
        pg = QWidget()
        v = QVBoxLayout(pg)
        v.setContentsMargins(8,8,8,8)
        v.setSpacing(6)

        # --- Find / Replace row with options ---
        row = QHBoxLayout()
        self.find_edit = QLineEdit();    self.find_edit.setPlaceholderText("Find")
        self.replace_edit = QLineEdit(); self.replace_edit.setPlaceholderText("Replace")
        self.match_case_cb    = QCheckBox("Aa")
        self.word_boundary_cb = QCheckBox(r"\b")
        self.regex_cb         = QCheckBox(".*")
        row.addWidget(self.find_edit, 2)
        row.addWidget(self.replace_edit, 2)
        row.addWidget(self.match_case_cb)
        row.addWidget(self.word_boundary_cb)
        row.addWidget(self.regex_cb)
        v.addLayout(row)

        # --- Include / Exclude fields ---
        inc_row = QHBoxLayout()
        self.inc_edit = QLineEdit(); self.inc_edit.setPlaceholderText("Files to include")
        self.exc_edit = QLineEdit(); self.exc_edit.setPlaceholderText("Files to exclude")
        inc_row.addWidget(self.inc_edit)
        inc_row.addWidget(self.exc_edit)
        v.addLayout(inc_row)

        # --- Results list ---
        self.hit_list = QListWidget()
        self.hit_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        v.addWidget(self.hit_list, 1)

        # connect click → emit absolute row/col
        self.hit_list.itemClicked.connect(self._on_hit_clicked)

        self.stack.addWidget(pg)

    def _show_page(self, index: int):
        # uncheck all sidebar buttons
        for btn in (self.btn_search,):
            btn.setChecked(btn is self.btn_search and index==0)
        self.stack.setCurrentIndex(index)
        self.show()

    def _on_hit_clicked(self, item):
        # parse "Row X, Col Y"
        parts = item.text().split()
        row = int(parts[1].rstrip(","))
        col = int(parts[3])
        self.hitActivated.emit(row, col)
