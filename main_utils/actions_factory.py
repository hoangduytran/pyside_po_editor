# main_utils/actions_factory.py

import os
import polib
from polib import POEntry

from PySide6.QtCore    import (
    QSettings,
    QThreadPool,
    QModelIndex,
    Qt,
    QItemSelectionModel,
)
from PySide6.QtGui     import QFont
from PySide6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QTableWidgetItem,
    QDialog,
)

from gv                   import main_gv, MainGlobalVar
from po_editor.tab_record import TabRecord
from lg                   import logger
from main_utils.safe_emit import safe_emit_signal
from sugg.translate       import TranslateTask, suggestor
from main_utils.popup_mnu import get_popup_menu
from pref.preferences     import PreferencesDialog
from main_utils.import_worker import on_import_po


def get_actions(gv: MainGlobalVar):
    """
    Return a dict of all callbacks, each operating on the
    currently active TabRecord (rec).
    """

    def _current_rec():
        """Find the TabRecord whose widget is the active tab."""
        win = gv.window
        widget = win.open_tabs.currentWidget()
        for rec in gv.open_tabs:
            if rec.widget is widget:
                return rec
        return None

    # ─── OPEN / NEW TAB ────────────────────────────────────────
        # ─── 1) Ask for path, then delegate ─────────────────────
    def on_open_file():
        path, _ = QFileDialog.getOpenFileName(
            gv.window, "Open PO File", "", "PO Files (*.po)"
        )
        if not path:
            return
        _do_load_file(path)  # <-- JUST DELEGATE

    # ─── 2) All the heavy lifting of opening/switching tabs ─
    def _do_load_file(path: str):
        """
        Load a file into a new tab, initializing the QTabWidget if necessary.
        """
        # Initialize the QTabWidget if it doesn't exist
        if gv.open_tabs is None:
            gv.open_tabs = QTabWidget()
            gv.window.setCentralWidget(gv.open_tabs)

        # Check if the file is already open
        for i in range(gv.open_tabs.count()):
            tab = gv.open_tabs.widget(i)
            if isinstance(tab, TabRecord) and tab.file_path == path:
                gv.open_tabs.setCurrentWidget(tab.widget)
                return

        # 2) Try to load the .po
        try:
            po_file = polib.pofile(path)
        except Exception as e:
            QMessageBox.critical(gv.window, "Error", f"Failed to open {path}:\n{e}")
            return

        # 3) Instantiate your editor widget (which itself sets up tables, etc.)
        from po_editor.po_editor_widget import POEditorWidget
        editor = POEditorWidget(path)
        name = os.path.basename(path)

        # 4) Now make the TabRecord once, with the freshly loaded po_file
        rec = TabRecord(
            file_path=path,
            file_name=name,
            widget=editor,
            po_file=po_file,
            table=editor.table,
            table_model=editor.table_model,
            source_edit=editor.source_edit,
            translation_edit=editor.translation_edit,
            comments_edit=editor.comments_edit,
            fuzzy_toggle=editor.fuzzy_toggle,
            suggestion_model=editor.suggestion_model,
            suggestion_view=editor.suggestion_version_table,
        )

        gv.open_tabs.addTab(editor, name)
        gv.open_tabs.setCurrentWidget(editor)
        gv.open_tabs.append(rec)

        # 5) Populate the freshly‐added tab with data
        _load_entries()

        # 6) Update your MRU list
        if path in gv.recent_files:
            gv.recent_files.remove(path)
        gv.recent_files.insert(0, path)
        gv.recent_files = gv.recent_files[:10]
        QSettings("POEditor", "Settings").setValue("recentFiles", gv.recent_files)



    # ─── SHARED LOAD LOGIC ─────────────────────────────────────
    # def _do_load_file(path: str):
    #     rec = _current_rec()
    #     if not rec:
    #         return
    #     try:
    #         rec.po_file = polib.pofile(path)
    #         rec.file_path = path
    #         _load_entries()
    #     except Exception as e:
    #         QMessageBox.critical(gv.window, "Error", f"Failed to open {path}:\n{e}")

    def _load_entries():
        rec = _current_rec()
        if not rec:
            return
        rec.table_model.setEntries(rec.po_file)
        rec.source_edit.clear()
        rec.translation_edit.clear()
        rec.fuzzy_toggle.setChecked(False)
        rec.comments_edit.clear()


    # ─── SAVE ───────────────────────────────────────────────────
    def on_save_file():
        rec = _current_rec()
        if not rec or not rec.file_path:
            return on_save_file_as()
        try:
            rec.po_file.save(rec.file_path)
            gv.window.statusBar().showMessage(f"Saved {rec.file_name}", 2000)
            rec.dirty = False
        except Exception as e:
            QMessageBox.critical(gv.window, "Error", f"Failed to save:\n{e}")

    def on_save_file_as():
        rec = _current_rec()
        if not rec:
            return
        path, _ = QFileDialog.getSaveFileName(
            gv.window, "Save PO File As", "", "PO Files (*.po)"
        )
        if not path:
            return
        rec.file_path = path
        rec.file_name = os.path.basename(path)
        on_save_file()


    # ─── PREFERENCES ───────────────────────────────────────────
    def on_open_preferences():
        rec = _current_rec()
        if not rec:
            return
        dlg = PreferencesDialog(gv.window)
        if dlg.exec() == QDialog.Accepted:
            dlg.save_settings()
            on_apply_fonts()
            gv.window.apply_shortcuts()


    # ─── TABLE SELECTION ────────────────────────────────────────
    def on_table_selection(row, col):
        rec = _current_rec()
        if not rec:
            return
        rec.current_row = row
        rec.current_entry = rec.po_file[row]


    # ─── FUZZY TOGGLE ──────────────────────────────────────────
    def on_fuzzy_changed(checked: bool):
        rec = _current_rec()
        if not rec or not rec.po_file:
            return
        entry = rec.po_file[rec.current_row]
        entry.fuzzy = checked

        # update model
        idx = rec.table_model.index(rec.current_row, 3)
        rec.table_model.setData(
            idx,
            Qt.Checked if checked else Qt.Unchecked,
            Qt.CheckStateRole
        )


    # ─── TRANSLATION EDIT ──────────────────────────────────────
    def on_translation_changed():
        rec = _current_rec()
        if not rec or rec.current_row is None:
            return
        text = rec.translation_edit.toPlainText()
        rec.po_file[rec.current_row].msgstr = text
        rec.table.blockSignals(True)
        rec.table.setItem(rec.current_row, 1, QTableWidgetItem(text))
        rec.table.blockSignals(False)
        safe_emit_signal(suggestor.clearSignal)
        safe_emit_signal(suggestor.addSignal, "new_translation")


    # ─── COMMENTS EDIT ─────────────────────────────────────────
    def on_comments_changed():
        rec = _current_rec()
        if not rec or rec.current_row is None:
            return
        rec.po_file[rec.current_row].comment = rec.comments_edit.toPlainText()


    # ─── TRANSLATE SUGGESTION ──────────────────────────────────
    def translate_suggestion(msgid):
        rec = _current_rec()
        if not rec:
            return
        settings = QSettings("POEditor", "Settings")
        target = settings.value("targetLanguage", "vi")
        task = TranslateTask(msgid, target)
        QThreadPool.globalInstance().start(task)


    # ─── APPLY FONTS ────────────────────────────────────────────
    def on_apply_fonts():
        settings = QSettings("POEditor", "Settings")
        tbl_font = QFont()
        tbl_font.fromString(settings.value("tableFont", tbl_font.toString()))
        for rec in gv.open_tabs:
            rec.table.setFont(tbl_font)

        txt_font = QFont()
        txt_font.fromString(settings.value("textFont", txt_font.toString()))
        for rec in gv.open_tabs:
            for w in (rec.source_edit, rec.translation_edit, rec.comments_edit):
                w.setFont(txt_font)


    # ─── TABLE NAVIGATION ──────────────────────────────────────
    def on_select_shift_up():
        rec = _current_rec()
        if not rec:
            return
        tbl = rec.table
        row = tbl.currentRow()
        if row > 0:
            tbl.setCurrentCell(row-1, 0)
            tbl.selectionModel().select(
                tbl.model().index(row-1, 0),
                QItemSelectionModel.Select | QItemSelectionModel.Rows
            )
            rec.current_row = row-1

    def on_select_shift_down():
        rec = _current_rec()
        if not rec:
            return
        tbl = rec.table
        row = tbl.currentRow()
        if row < tbl.rowCount()-1:
            tbl.setCurrentCell(row+1, 0)
            tbl.selectionModel().select(
                tbl.model().index(row+1, 0),
                QItemSelectionModel.Select | QItemSelectionModel.Rows
            )
            rec.current_row = row+1


    # ─── SORTING ───────────────────────────────────────────────
    def on_sort_untranslated():
        _sort_and_reload(lambda e: bool(e.msgstr))

    def on_sort_fuzzy():
        _sort_and_reload(lambda e: not e.fuzzy)

    def on_sort_by_linenum():
        _sort_and_reload(lambda e: e.linenum or 0)

    def on_sort_by_id():
        _sort_and_reload(lambda e: e.msgid.lower())

    def on_sort_by_string():
        _sort_and_reload(lambda e: e.msgstr.lower())


    def _sort_and_reload(keyfunc):
        rec = _current_rec()
        if not rec:
            return
        # remember current entry
        prev_entry = rec.po_file[rec.current_row] if rec.current_row is not None else None
        # sort
        rec.po_file.sort(key=keyfunc)
        # reload
        _load_entries()
        # restore selection
        if prev_entry in rec.po_file:
            new_idx = rec.po_file.index(prev_entry)
            rec.current_row = new_idx
            rec.table.selectRow(new_idx)
            on_table_selection(new_idx, 0)


    # ─── TRANSLATION HISTORY ───────────────────────────────────
    def add_translation_version(msgid, msgctx, new_translation):
        from pref.tran_history.translation_db import db
        db.update_translation_version(msgid, msgctxt=msgctx, new_translation=new_translation)
        rec = _current_rec()
        if not rec:
            return
        rec.po_file[rec.current_row].msgstr = new_translation
        rec.table.blockSignals(True)
        rec.table.setItem(rec.current_row, 1, QTableWidgetItem(new_translation))
        rec.table.blockSignals(False)


    # ─── SUGGESTIONS ───────────────────────────────────────────
    def on_suggestion_selected(index: QModelIndex):
        rec = _current_rec()
        if not rec:
            return
        rec.current_sugg_row = index.row()
        rec.current_sugg_rec = rec.suggestion_model.record()

    def on_suggestions_clear():
        rec = _current_rec()
        if not rec:
            return
        # nothing special here

    def on_suggestions_received(machine_text: str):
        rec = _current_rec()
        if not rec:
            return
        from pref.tran_history.tran_db_record import DatabasePORecord
        from pref.tran_history.translation_db import db

        is_valid = bool(machine_text)
        if not is_valid:
            return

        idx = rec.suggestion_view.selectionModel().currentIndex()
        if not idx.isValid():
            return

        entry: POEntry = rec.po_file[rec.current_row]
        msgid, msgctx = entry.msgid, entry.msgctx
        try:
            db_rec: DatabasePORecord = db.get_entry(msgid, msgctx)
        except:
            db_rec = DatabasePORecord(msgid=msgid, msgctxt=msgctx)

        if not db_rec.is_my_parent(entry):
            return

        rec.suggestion_model.setRecord(db_rec)

    def on_suggestion_context_menu(pos):
        rec = _current_rec()
        if not rec:
            return
        tbl = rec.suggestion_view
        db_rec = rec.suggestion_model.record()
        if not db_rec.is_my_parent(rec.po_file[rec.current_row]):
            return
        global_pos = tbl.viewport().mapToGlobal(pos)
        menu = get_popup_menu(gv.window)
        menu.show_for(tbl, global_pos)

    def on_suggestion_double_click(index: QModelIndex):
        rec = _current_rec()
        if not rec:
            return
        db_rec = rec.suggestion_model.record()
        if not db_rec.is_my_parent(rec.po_file[rec.current_row]):
            return
        _, text = db_rec.msgstr_versions[index.row()]
        rec.table_model.setData(
            rec.table_model.index(rec.current_row, 2),
            text,
            Qt.EditRole
        )
        rec.po_file[rec.current_row].msgstr = text
        rec.translation_edit.setPlainText(text)
        rec.current_sugg_rec = db_rec

    # ─── DELETE ENTRY ─────────────────────────────────────────
    def on_delete_table_entry():
        rec = _current_rec()
        if not rec:
            return
        tbl = rec.table
        sel = tbl.selectionModel().selectedRows()
        if not sel:
            return
        ans = QMessageBox.question(
            gv.window,
            "Delete Entry",
            f"Really delete {len(sel)} entr{'y' if len(sel)==1 else 'ies'}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans != QMessageBox.Yes:
            return
        for ix in sorted((r.row() for r in sel), reverse=True):
            rec.po_file.pop(ix)
        _load_entries()

    # ─── SAVE TRANSLATION ─────────────────────────────────────
    def on_save_translation():
        rec = _current_rec()
        if not rec or rec.current_row is None:
            return
        new_txt = rec.translation_edit.toPlainText()
        rec.po_file[rec.current_row].msgstr = new_txt
        rec.table_model.setData(
            rec.table_model.index(rec.current_row, 1),
            new_txt,
            Qt.EditRole
        )
        gv.window.statusBar().showMessage("Translation saved", 2000)

    # ─── TABLE DATA CHANGED ───────────────────────────────────
    def on_table_data_changed(topLeft: QModelIndex,
                              bottomRight: QModelIndex,
                              roles: list[int] = None):
        rec = _current_rec()
        if not rec:
            return
        if topLeft.column() != 3:
            return
        rec.current_row = topLeft.row()
        entry = rec.po_file[topLeft.row()]
        rec.fuzzy_toggle.setChecked(bool(entry.fuzzy))

    def ws_open_file_in_editor():
        # no-op or implement as needed
        pass

    def on_load_recent_files():
        # Load the MRU list from disk
        files = QSettings("POEditor", "Settings").value("recentFiles", [])
        if not files:
            return
        gv.recent_files = files
        for path in files:
            _do_load_file(path)

    return {
        'on_open_file':               on_open_file,
        'on_load_recent_files':       on_load_recent_files,
        'on_do_load_file':            _do_load_file,
        'on_save_file':               on_save_file,
        'on_save_file_as':            on_save_file_as,
        'on_open_preferences':        on_open_preferences,
        'on_table_selection':         on_table_selection,
        'on_fuzzy_changed':           on_fuzzy_changed,
        'on_translation_changed':     on_translation_changed,
        'on_comments_changed':        on_comments_changed,
        'translate_suggestion':       translate_suggestion,
        'on_apply_fonts':             on_apply_fonts,
        'on_select_shift_up':         on_select_shift_up,
        'on_select_shift_down':       on_select_shift_down,
        'on_sort_untranslated':       on_sort_untranslated,
        'on_sort_fuzzy':              on_sort_fuzzy,
        'on_sort_by_linenum':         on_sort_by_linenum,
        'on_sort_by_id':              on_sort_by_id,
        'on_sort_by_string':          on_sort_by_string,
        'add_translation_version':    add_translation_version,
        'on_suggestion_selected':     on_suggestion_selected,
        'on_suggestions_clear':       on_suggestions_clear,
        'on_suggestions_received':    on_suggestions_received,
        'on_suggestion_context_menu': on_suggestion_context_menu,
        'on_suggestion_double_click': on_suggestion_double_click,
        'on_delete_table_entry':      on_delete_table_entry,
        'on_save_translation':        on_save_translation,
        'on_table_data_changed':      on_table_data_changed,
        'ws_open_file_in_editor':     ws_open_file_in_editor,
        'on_import_po':               on_import_po,
    }

