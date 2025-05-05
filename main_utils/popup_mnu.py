# main_utils/popup_mnu.py
from PySide6.QtWidgets import (
    QMenu, QTextEdit, QLineEdit, QListWidget,
    QApplication, QTableView, QDialog
)
from PySide6.QtGui import QAction
from gv import main_gv
from pref.tran_history.translation_db import db
from suggestion_picker_dlg import SuggestionPickerDialog
from pref.tran_history.tran_db_record import DatabasePORecord

class PopupMenuManager(QMenu):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, parent=None):
        super().__init__(parent)

        # Copy / Paste
        self.copy_action  = QAction("Copy", self)
        self.paste_action = QAction("Paste", self)

        # View single suggestion
        self.view_action = QAction("View / Insert…", self)
        # View all suggestions
        self.view_all_action = QAction("View All / Insert…", self)

        # build menu
        self.addAction(self.copy_action)
        self.addAction(self.paste_action)
        self.addSeparator()
        self.addAction(self.view_action)
        self.addAction(self.view_all_action)

        # connect
        self.copy_action.triggered.connect(self._copy)
        self.paste_action.triggered.connect(self._paste)
        self.view_action.triggered.connect(self._view_suggestion)
        self.view_all_action.triggered.connect(self._view_all_suggestions)

        self._target_widget = None
        self._last_global_pos = None

    def show_for(self, widget, global_pos):
        self._target_widget = widget
        self._last_global_pos = global_pos

        # Copy?
        can_copy = False
        if isinstance(widget, QTextEdit):
            can_copy = widget.canCopy()
        elif isinstance(widget, QLineEdit):
            can_copy = widget.canCopy()
        elif isinstance(widget, QListWidget):
            can_copy = widget.currentItem() is not None
        elif isinstance(widget, QTableView) and widget is main_gv.suggestion_version_table:
            can_copy = widget.currentIndex().isValid()
        self.copy_action.setEnabled(can_copy)

        # Paste? allow into text widgets or the suggestions table
        clip = QApplication.clipboard()
        txt = clip.text().strip()
        can_paste = False
        if isinstance(widget, (QTextEdit, QLineEdit)):
            can_paste = bool(txt)
        elif isinstance(widget, QTableView) and widget is main_gv.suggestion_version_table:
            can_paste = bool(txt)
        self.paste_action.setEnabled(can_paste)

        # which table?
        is_sugg_tbl = (
            isinstance(widget, QTableView)
            and widget is main_gv.suggestion_version_table
        )
        self.view_action.setVisible(is_sugg_tbl)
        self.view_all_action.setVisible(is_sugg_tbl)

        self.exec(global_pos)

    def _copy(self):
        w = self._target_widget
        if isinstance(w, (QTextEdit, QLineEdit)):
            w.copy()
        elif isinstance(w, QListWidget):
            item = w.currentItem()
            if item:
                QApplication.clipboard().setText(item.text())
        elif isinstance(w, QTableView) and w is main_gv.suggestion_version_table:
            idx = w.currentIndex()
            if idx.isValid():
                text = w.model().data(w.model().index(idx.row(), 1))
                QApplication.clipboard().setText(text)

    def _paste(self):
        w = self._target_widget

        # Standard paste into text widgets
        if isinstance(w, (QTextEdit, QLineEdit)):
            w.paste()
            return

        # Paste into suggestions table: update or create DatabasePORecord
        if isinstance(w, QTableView) and w is main_gv.suggestion_version_table:
            text = QApplication.clipboard().text().strip()
            if not text:
                return

            # get current record from model
            model = w.model()
            rec: DatabasePORecord = model.record()

            # find existing suggestion in DB or create new
            po_ent = main_gv.current_po_rec
            existing = db.get_entry(po_ent.msgid, po_ent.msgctxt) \
                if hasattr(db, 'get_entry') else None
            if existing and existing.unique_id is not None:
                rec = existing
            else:
                rec = DatabasePORecord(
                    msgid=po_ent.msgid,
                    msgctxt=po_ent.msgctxt,
                    msgstr_versions=[]
                )
                db.add_entry(po_ent.msgid, po_ent.msgctxt, initial=None)

            # append new text if not a duplicate
            versions = [v for _, v in rec.msgstr_versions]
            if text not in versions:
                db.add_version(rec.unique_id, text)
                model.refresh()
            return

    def _view_suggestion(self):
        w = self._target_widget
        if not (isinstance(w, QTableView)
                and w is main_gv.suggestion_version_table):
            return
        local = w.viewport().mapFromGlobal(self._last_global_pos)
        idx = w.indexAt(local)
        if not idx.isValid():
            return

        model = w.model()
        rec: DatabasePORecord = model.record()
        ver, txt = rec.msgstr_versions[idx.row()]

        dlg = SuggestionPickerDialog(main_gv.window, [(ver, txt)])
        dlg.exec()
        if getattr(dlg, 'selected_text', None):
            main_gv.window.translation_edit.setPlainText(dlg.selected_text)

    def _view_all_suggestions(self):
        w = self._target_widget
        if not (isinstance(w, QTableView)
                and w is main_gv.suggestion_version_table):
            return

        model = w.model()
        rec = model.record()
        versions = rec.msgstr_versions

        dlg = SuggestionPickerDialog(main_gv.window, versions)
        if hasattr(dlg, 'list_widget'):
            dlg.list_widget.setWordWrap(True)
            dlg.list_widget.itemDoubleClicked.connect(
                lambda item: self._accept_and_insert(dlg, item.text())
            )

        dlg.exec()
        if getattr(dlg, 'selected_text', None):
            main_gv.window.translation_edit.setPlainText(dlg.selected_text)

    def _accept_and_insert(self, dlg: QDialog, text: str):
        dlg.selected_text = text
        dlg.accept()


_popup_menu: PopupMenuManager = None

def get_popup_menu(parent=None) -> PopupMenuManager:
    global _popup_menu
    if _popup_menu is None:
        _popup_menu = PopupMenuManager(parent)
    return _popup_menu
