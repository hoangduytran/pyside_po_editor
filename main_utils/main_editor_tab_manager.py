# main_utils/main_editor_tab_manager.py

import os
from PySide6.QtWidgets import QFileDialog
from po_editor.po_editor_main_gui import POEditorWindow

from main_utils.main_editor_tab import EditorTab

class EditorTabManager:
    def __init__(self, tab_widget):
        self.tab_widget = tab_widget
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self._on_close)
        self.tabs = []

    def open_po_file(self, parent=None):
        path, _ = QFileDialog.getOpenFileName(
            parent,
            "Open PO File",
            filter="PO Files (*.po)"
        )
        if not path:
            return
        editor = POEditorWindow(path)
        self.add_tab(editor, path)

    def add_tab(self, widget, path):
        name = os.path.basename(path)
        self.tab_widget.addTab(widget, name)
        idx = self.tab_widget.indexOf(widget)
        self.tab_widget.setTabToolTip(idx, path)
        self.tabs.append(EditorTab(widget, path))
        self.tab_widget.setCurrentIndex(idx)

    def _on_close(self, index):
        widget = self.tab_widget.widget(index)
        self.tabs = [t for t in self.tabs if t.widget is not widget]
        self.tab_widget.removeTab(index)
