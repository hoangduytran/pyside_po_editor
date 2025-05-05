# #!/usr/bin/env python3
# import sys
# from enum import Enum
#
# from PySide6.QtWidgets import (
#     QApplication,
#     QMainWindow,
#     QWidget,
#     QVBoxLayout,
#     QHBoxLayout,
#     QSplitter,
#     QPushButton,
#     QStackedWidget,
#     QTabWidget,
#     QLabel,
#     QToolButton,
# )
# from PySide6.QtCore import Qt
# from gv import main_gv
# from main_utils.left_tab_bar import LeftAlignedTabBar
#
# # import your existing POEditorWindow here:
# # from po_editor.main_gui import POEditorWindow
# import sys
#
# # ─── hack the process name via PyObjC Foundation ──────────────────────────────
# try:
#     from Foundation import NSProcessInfo
#     NSProcessInfo.processInfo().setProcessName_("POEditor")
# except ImportError:
#     pass
# # ───────────────────────────────────────────────────────────────────────────────
#
# from PySide6.QtWidgets import QApplication
# from po_editor.main_gui import POEditorWindow
#
# class ButtonEnum(Enum):
#     EXPLORER        = "\U0001F4C2"   # 📂
#     SEARCH          = "\U0001F50D"   # 🔍
#     SOURCE_CONTROL  = "\U0001F500"   # 🔀
#     RUN             = "\u25B6"       # ▶
#     EXTENSIONS      = "\U0001F4E6"   # 📦
#
#     @property
#     def tooltip(self):
#         return self.name.replace("_", " ").title()
#
#
# class POEditorMain(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("PO Editor — VSCode Style")
#
#         # ─── build the left toolbar + panels ──────────────────────────
#         main_splitter = QSplitter(Qt.Horizontal, self)
#
#         side_container = QWidget()
#         side_layout    = QHBoxLayout(side_container)
#         side_layout.setContentsMargins(0,0,0,0)
#         side_layout.setSpacing(0)
#
#         button_bar    = QWidget()
#         button_bar.setStyleSheet("background: #222;")
#         button_layout = QVBoxLayout(button_bar)
#         button_layout.setContentsMargins(0,0,0,0)
#         button_layout.setSpacing(0)
#
#         self.side_buttons = []
#         for idx, sym in enumerate(ButtonEnum):
#             btn = QPushButton(sym.value)
#             btn.setCheckable(True)
#             btn.setFixedSize(40,40)
#             btn.setToolTip(sym.tooltip)
#             btn.setStyleSheet(
#                 "background: transparent; color: white; border: none; font-size: 18px;"
#             )
#             btn.clicked.connect(lambda checked, i=idx: self.toggle_panel(i))
#             button_layout.addWidget(btn)
#             self.side_buttons.append(btn)
#
#         button_layout.addStretch()
#
#         self.panel_stack = QStackedWidget()
#         for sym in ButtonEnum:
#             page = QWidget()
#             lay  = QVBoxLayout(page)
#             lay.addWidget(QLabel(f"{sym.tooltip} Panel"))
#             lay.addStretch()
#             self.panel_stack.addWidget(page)
#         self.panel_stack.hide()
#
#         side_layout.addWidget(button_bar)
#         side_layout.addWidget(self.panel_stack)
#
#         # ─── build the right TabWidget ────────────────────────────────
#         self.tab_widget = QTabWidget()
#         # inject our LeftAlignedTabBar (with the guard!)
#         self.tab_widget.setTabBar(LeftAlignedTabBar())
#         self.tab_widget.setTabPosition(QTabWidget.North)
#         # don’t let tabs auto-stretch
#         self.tab_widget.tabBar().setExpanding(False)
#
#         # put the little back arrow in the top-left corner of the tab bar
#         back_btn = QToolButton(self.tab_widget)
#         back_btn.setArrowType(Qt.LeftArrow)
#         back_btn.setToolTip("Go Back")
#         # back_btn.clicked.connect(self.on_back)  # wire up your slot here
#         self.tab_widget.setCornerWidget(back_btn, Qt.TopLeftCorner)
#
#         # (add your “PO File Editor” first tab here…)
#         # e.g. self.tab_widget.addTab(POEditorWindow(), "PO File Editor")
#         # **HERE**: add your real editor as a tab
#         self.editor = POEditorWindow()
#         self.tab_widget.addTab(self.editor, "PO File Editor")
#         self.tab_widget.setCurrentWidget(self.editor)
#
#         # ─── assemble the rest ──────────────────────────────────────
#         main_splitter = QSplitter(Qt.Horizontal, self)
#         # … add side_container and self.tab_widget …
#         self.setCentralWidget(main_splitter)
#
#         # ─── assemble everything ──────────────────────────────────────
#         main_splitter.addWidget(side_container)
#         main_splitter.addWidget(self.tab_widget)
#         main_splitter.setStretchFactor(1, 1)
#
#         self.setCentralWidget(main_splitter)
#
#     def toggle_panel(self, index: int):
#         """toggle which left-side panel is showing (or hide if already up)"""
#         if self.panel_stack.isVisible() and self.panel_stack.currentIndex() == index:
#             self.side_buttons[index].setChecked(False)
#             self.panel_stack.hide()
#         else:
#             for i, btn in enumerate(self.side_buttons):
#                 btn.setChecked(i == index)
#             self.panel_stack.setCurrentIndex(index)
#             self.panel_stack.show()
#
#     def on_back(self):
#         """your “go back” logic here"""
#         # e.g. hide the panel or switch tab -- up to you
#         pass
#
#     def _add_poeditor_tab(self):
#         """Add your existing POEditorWindow as a new tab."""
#         editor = POEditorWindow()
#         main_gv.app = editor
#         editor.showMaximized()
#         self.tab_widget.addTab(editor, "PO File Editor")
#
#     def close_tab(self, index):
#         self.tab_widget.removeTab(index)
#
#     def toggle_panel(self, index):
#         # clicking the same button hides it
#         if self.panel_stack.isVisible() and self.panel_stack.currentIndex() == index:
#             self.panel_stack.hide()
#             self.side_buttons[index].setChecked(False)
#             return
#
#         # otherwise show that page
#         for i, btn in enumerate(self.side_buttons):
#             btn.setChecked(i == index)
#         self.panel_stack.setCurrentIndex(index)
#         self.panel_stack.show()
#
#
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     window = POEditorMain()
#     window.resize(1000, 600)
#     window.show()
#     sys.exit(app.exec())


#!/usr/bin/env python3
import sys
import os
from enum import Enum
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QPushButton, QStackedWidget, QTabBar, QLabel,
    QFileDialog
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from po_editor.po_editor_main_gui import POEditorWindow

class ButtonEnum(Enum):
    def __new__(cls, icon, tooltip):
        obj = object.__new__(cls)
        obj._value_ = icon
        obj.tooltip = tooltip
        return obj

    EXPLORER       = ("📂", "Explorer")
    SEARCH         = ("🔍", "Search")
    SOURCE_CONTROL = ("🔀", "Source Control")
    RUN            = ("▶",  "Run")
    EXTENSIONS     = ("📦", "Extensions")

PANEL_COLORS = {
    ButtonEnum.EXPLORER:       "#2b2b2b",
    ButtonEnum.SEARCH:         "#1e1e1e",
    ButtonEnum.SOURCE_CONTROL: "#252526",
    ButtonEnum.RUN:            "#007acc",
    ButtonEnum.EXTENSIONS:     "#212121",
}

class ToolbarManager:
    def __init__(self, parent_layout, toggle_callback):
        self.buttons = []
        self.toggle_callback = toggle_callback
        self.button_bar = QWidget()
        self.button_bar.setFixedWidth(40)
        self.button_bar.setStyleSheet("background-color: black;")
        layout = QVBoxLayout(self.button_bar)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        for idx, btn_enum in enumerate(ButtonEnum):
            btn = QPushButton(btn_enum.value)
            btn.setCheckable(True)
            btn.setFixedSize(40,40)
            btn.setToolTip(btn_enum.tooltip)
            btn.setStyleSheet("background-color: transparent; color: white; border: none; font-size: 18px;")
            btn.clicked.connect(lambda checked, index=idx: self.toggle_callback(index))
            layout.addWidget(btn)
            self.buttons.append(btn)
        layout.addStretch()
        parent_layout.addWidget(self.button_bar)

class EditorTabManager(QWidget):
    def __init__(self):
        super().__init__()
        self.tabBar = QTabBar()
        self.tabBar.setExpanding(False)
        self.tabBar.setTabsClosable(True)
        self.tabBar.setMovable(True)
        self.tabBar.tabCloseRequested.connect(self.close_tab)

        self.pages = QStackedWidget()
        self.paths = []
        self.tabBar.currentChanged.connect(self.pages.setCurrentIndex)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        hl = QHBoxLayout()
        hl.addWidget(self.tabBar)
        hl.addStretch()
        layout.addLayout(hl)
        layout.addWidget(self.pages)

    def add_tab_widget(self, widget, name, path=None):
        idx = self.pages.addWidget(widget)
        self.paths.insert(idx, path)
        self.tabBar.insertTab(idx, name)
        self.tabBar.setTabToolTip(idx, path or "Unsaved")
        self.tabBar.setCurrentIndex(idx)

    def close_tab(self, idx):
        self.pages.removeWidget(self.pages.widget(idx))
        self.tabBar.removeTab(idx)
        self.paths.pop(idx)

class MainWindow(QMainWindow):
    def __init__(self, acts):
        super().__init__()
        self.acts = acts
        self.setWindowTitle("PO File Editor")

        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0,0,0,0)
        h_layout.setSpacing(0)

        self.toolbar = ToolbarManager(h_layout, self.toggle_panel)

        splitter = QSplitter(Qt.Horizontal)
        self.panel_stack = QStackedWidget()
        for btn_enum in ButtonEnum:
            panel = QWidget()
            color = PANEL_COLORS.get(btn_enum, "#000000")
            panel.setStyleSheet(f"background-color: {color};")
            pnl_layout = QVBoxLayout(panel)
            pnl_layout.setContentsMargins(8,8,8,8)
            pnl_layout.addWidget(QLabel(f"{btn_enum.tooltip} Panel"))
            self.panel_stack.addWidget(panel)
        self.panel_stack.hide()
        splitter.addWidget(self.panel_stack)

        self.editor_manager = EditorTabManager()
        splitter.addWidget(self.editor_manager)
        splitter.setStretchFactor(1,1)

        h_layout.addWidget(splitter)
        self.setCentralWidget(container)

        # File menu using acts callback
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        open_action = QAction("Open .po", self)
        open_action.triggered.connect(self.acts['on_open_file'])
        file_menu.addAction(open_action)

    def toggle_panel(self, index):
        if self.panel_stack.isVisible() and self.panel_stack.currentIndex() == index:
            self.panel_stack.hide()
            self.toolbar.buttons[index].setChecked(False)
            return
        for i, btn in enumerate(self.toolbar.buttons):
            btn.setChecked(i == index)
        self.panel_stack.setCurrentIndex(index)
        self.panel_stack.show()

# if __name__ == "__main__":
#     # acts dict should define 'on_open_file'
#     def open_po():
#         path, _ = QFileDialog.getOpenFileName(None, "Open Translation File", filter="PO files (*.po)")
#         if path:
#             # use POEditorWindow to open
#             editor = POEditorWindow(path)
#             # add to tab
#             main_win.editor_manager.add_tab_widget(editor, os.path.basename(path), path)
#
#     acts = {'on_open_file': open_po}
#     app = QApplication(sys.argv)
#     main_win = MainWindow(acts)
#     main_win.show()
#     sys.exit(app.exec())
