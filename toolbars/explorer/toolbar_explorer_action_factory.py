# toolbars/explorer/toolbar_explorer_action_factory.py

import os
from PySide6.QtWidgets import QFileDialog, QTextEdit, QMessageBox
from po_editor.po_editor_main_gui import POEditorWindow


def get_explorer_actions(window, editor_manager):
    """
    Return a dict of Explorer-related callbacks.

    - 'on_open_path': open a file or drill into directory
    """

    def on_open_path(path: str):
        """
        Called when ExplorerPanel signals a file or directory to open.
        If directory, let the panel drill in (handled elsewhere).
        If file, open a POEditorWindow if .po, otherwise a QTextEdit.
        """
        ext = os.path.splitext(path)[1].lower()
        if ext == ".po":
            editor = POEditorWindow(path)
        else:
            editor = QTextEdit()
            try:
                with open(path, "r", encoding="utf-8") as f:
                    editor.setPlainText(f.read())
            except Exception as e:
                QMessageBox.critical(window, "Error", f"Failed to load file:\n{e}")
        editor_manager.add_tab(editor, path)

    return {
        'on_open_path': on_open_path,
    }

