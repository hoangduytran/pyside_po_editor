#!/usr/bin/env python3
import resources_rc  # <<<<<<<<<< registers :/rs/styles.css
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSplitter,
    QTabWidget,
    QStackedWidget,
    QLabel,
    QSizePolicy,
)
from PySide6.QtCore import (
    Qt,
    QFile,
    QSettings,
    QDir,
    QFileInfo,
    QTimer,
)
from PySide6.QtGui import (
    QKeySequence,
    QShortcut,
)

from main_utils.main_button_enum        import ButtonEnum
from main_utils.main_toolbar_manager    import ToolbarManager
from main_utils.main_editor_tab_manager import EditorTabManager

from toolbars.explorer.toolbar_explorer_panel         import ExplorerPanel
from toolbars.explorer.toolbar_explorer_action_factory import get_explorer_actions
from toolbars.search.toolbar_search_replace_main      import FindReplaceMain
from toolbars.search.toolbar_search_replace_actions   import get_search_actions
from main_utils.actions_factory import get_actions
from po_editor.po_editor_main_menu import POEditorMainMenu

from lg import logger
from gv import main_gv


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ─── 0) Global shortcuts ───────────────────────────────
        zoom_in = QShortcut(QKeySequence.ZoomIn, self)
        zoom_in.setContext(Qt.ApplicationShortcut)
        zoom_in.activated.connect(self._zoom_in)

        zoom_out = QShortcut(QKeySequence.ZoomOut, self)
        zoom_out.setContext(Qt.ApplicationShortcut)
        zoom_out.activated.connect(self._zoom_out)

        zoom_reset = QShortcut(QKeySequence("Ctrl+0"), self)
        zoom_reset.setContext(Qt.ApplicationShortcut)
        zoom_reset.activated.connect(self._zoom_reset)

        # ─── 1) Restore last‐used path & file ──────────────────
        settings  = QSettings("com.poeditor", "POEditor")
        last_dir  = settings.value("lastDirectory", type=str)
        last_file = settings.value("lastFile",      type=str)
        self.setWindowTitle("PO Editor IDE")

        if not last_dir or not QDir(last_dir).exists():
            last_dir = QDir.homePath()
        if last_file and not QFileInfo(last_file).exists():
            last_file = None

        main_gv.current_dir  = last_dir
        main_gv.current_file = last_file

        self.main_menu = POEditorMainMenu(self)

        # ─── 2) Editor Tabs ────────────────────────────────────
        self.tab_widget     = QTabWidget()
        self.editor_manager = EditorTabManager(self.tab_widget)

        # ─── 3) Toolbar & Panel Stack ──────────────────────────
        button_bar = QWidget()
        button_bar.setObjectName("LeftToolBar")               # for #LeftToolBar QSS
        button_bar.setAttribute(Qt.WA_StyledBackground, True)
        button_bar.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        button_bar.setMinimumWidth(50)

        self.panel_stack = QStackedWidget()
        self.panel_stack.hide()

        # ─── 4) Populate side panels ───────────────────────────
        explorer_actions = get_explorer_actions(self, self.editor_manager)
        for idx, btn_enum in enumerate(ButtonEnum):
            if btn_enum is ButtonEnum.EXPLORER:
                panel = ExplorerPanel(explorer_actions['on_open_path'])
                panel.setObjectName("ExplorerPanel")            # <<< ensure #ExplorerPanel QTreeView matches
            elif btn_enum is ButtonEnum.SEARCH:
                search_panel  = FindReplaceMain(self)
                search_actions = get_search_actions(
                    window         = self,
                    find_widget    = search_panel.toggle_widget,
                    editor_manager = self.editor_manager,
                    get_root_path  = lambda: main_gv.current_dir
                )
                fp = search_panel.toggle_widget
                fp.toggle_btn.toggled.connect(search_actions["on_toggle"])
                fp.find_edit.returnPressed.connect(search_actions["on_find"])
                fp.btn_prev_found.clicked.connect(search_actions["on_prev_found"])
                fp.btn_next_found.clicked.connect(search_actions["on_next_found"])
                fp.btn_close.clicked.connect(search_actions["on_close"])
                fp.replace_edit.returnPressed.connect(search_actions["on_replace_current"])
                fp.btn_replace_current.clicked.connect(search_actions["on_replace_current"])
                fp.btn_replace_all.clicked.connect(search_actions["on_replace_all"])
                search_panel.include_edit.flag_use_settings.toggled.connect(search_actions['on_toggle'])
                search_panel.exclude_edit.flag_search_opened.toggled.connect(search_actions['on_toggle'])
                panel = search_panel
            else:
                panel = QWidget()
                ph_layout = QVBoxLayout(panel)
                ph_layout.addWidget(QLabel(f"{btn_enum.tooltip} Panel"))

            panel.setStyleSheet("background-color: #f0f0f0;")
            self.panel_stack.addWidget(panel)

        # ─── 5) Main layout ─────────────────────────────────────
        container = QWidget()
        h_layout  = QHBoxLayout(container)
        h_layout.setContentsMargins(0,0,0,0)
        h_layout.setSpacing(0)

        h_layout.addWidget(button_bar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.panel_stack)
        splitter.addWidget(self.tab_widget)
        splitter.setStretchFactor(1,1)
        h_layout.addWidget(splitter)

        h_layout.setStretch(0,0)
        h_layout.setStretch(1,1)

        self.setCentralWidget(container)

        # ─── 6) Build toolbar (in main_toolbar_manager.py) ───────
        self.toolbar_manager = ToolbarManager(self, button_bar, self.panel_stack)
        self.toolbar_buttons = self.toolbar_manager.buttons
        # remove any inline styles so our global CSS can apply
        for btn in self.toolbar_buttons:
            btn.setStyleSheet("")
            btn.setAttribute(Qt.WA_Hover, True)

    def toggle_panel(self, index: int):
        if self.panel_stack.isVisible() and self.panel_stack.currentIndex() == index:
            self.panel_stack.hide()
            self.toolbar_buttons[index].setChecked(False)
        else:
            for i, btn in enumerate(self.toolbar_buttons):
                btn.setChecked(i == index)
            self.panel_stack.setCurrentIndex(index)
            self.panel_stack.show()


    def _zoom_in(self):
        f = QApplication.instance().font()
        f.setPointSize(f.pointSize() + 1)
        QApplication.instance().setFont(f)

    def _zoom_out(self):
        f = QApplication.instance().font()
        f.setPointSize(max(f.pointSize() - 1, 1))
        QApplication.instance().setFont(f)

    def _zoom_reset(self):
        f = QApplication.instance().font()
        f.setPointSize(10)
        QApplication.instance().setFont(f)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # ─── Load & apply the QSS from your resources ───────────────
    rs_stylesheet = QFile(":/rs/styles.css")
    if not rs_stylesheet.open(QFile.ReadOnly | QFile.Text):
        print("⚠️ Could not load :/rs/styles.css")
    else:
        raw = rs_stylesheet.readAll()
        # convert to Python str
        try:
            qss = raw.data().decode("utf-8")
        except AttributeError:
            qss = str(raw)
        app.setStyleSheet(qss)
        rs_stylesheet.close()

    window = MainWindow()
    window.show()

    actions = get_actions(main_gv)
    QTimer.singleShot(20, actions['on_load_recent_files'])

    sys.exit(app.exec())
