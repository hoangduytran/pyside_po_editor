# sugg/suggestion_controller.py
from PySide6.QtCore import QModelIndex, QSignalBlocker
from polib import POEntry
from gv import main_gv
from sugg.translate import translate_suggestion
from lg import logger

class SuggestionController:
    """
    Handles suggestion logic on table row changes and integrates with the translation history DB.
    """
    def __init__(self, window, suggestion_model):
        self.window = window
        self.model = suggestion_model

    def on_row_change(self, current: QModelIndex, previous: QModelIndex):
        """
        Called when the main-table selection changes.
        - Persists edits to the previous suggestion.
        - Updates global PO state.
        - Loads the new entry into editors & suggestion pane.
        - Triggers async translation for the new entry.
        """
        # 1) Commit any edits on previous suggestion
        if previous.isValid() and main_gv.current_suggestion_record:
            self._commit_previous_suggestion(previous)

        # 2) Update main_gv state for PO entries
        self._update_global_po_state(current, previous)

        # 3) If a new row is selected, load it; else clear UI
        if current.isValid():
            self._load_new_entry(current)
        else:
            self._clear_all_panes()

    def _commit_previous_suggestion(self, previous: QModelIndex):
        """
        Save edits from the suggestion pane back into the DB.
        """
        from pref.tran_history.translation_db import db
        from pref.tran_history.tran_db_record import DatabasePORecord

        sugg_rec: DatabasePORecord = main_gv.current_suggestion_record
        new_text = self.window.translation_edit.toPlainText().strip()

        # if not new_text or sugg_rec.is_virtually_same(new_text):
        has_new_text = bool(new_text)
        if not has_new_text:
            return

        if not previous.isValid():
            return


        previous_row = previous.row()
        parent_entry: POEntry = main_gv.po[previous_row]
        parent_entry.msgstr = new_text

        logger.info(
            f'previous record: parent_entry (main_gv.po[previous_row]) is now: \n{parent_entry}\n'
            f'flags:{parent_entry.flags}\n'
            f'fuzzy:{parent_entry.fuzzy}\n'
        )

        # parent_entry: POEntry = main_gv.old_po_rec
        # If no DB record exists for suggestions, create it
        is_my_parent = (sugg_rec.is_my_parent(parent_entry))
        is_sugg_rec_empty = not bool(sugg_rec.unique_id)
        is_adding_new_po_entry = is_my_parent and is_sugg_rec_empty
        if is_adding_new_po_entry:
            sugg_rec = db.insert_po_entry(parent_entry)

        is_new_text = not sugg_rec.has_tran_text(new_text)
        can_update = (is_my_parent and is_new_text)
        if can_update:
            sugg_rec.add_version_mem(new_text)
            sugg_rec.update_record_with_changes()

        self.model.setRecord(sugg_rec)
        main_gv.current_suggestion_record = sugg_rec

    def _update_global_po_state(self, current: QModelIndex, previous: QModelIndex):
        # stash old PO row & record
        if previous.isValid():
            main_gv.old_po_row = previous.row()
            main_gv.old_po_rec = main_gv.po[previous.row()]
        else:
            main_gv.old_po_row = None
            main_gv.old_po_rec = None

        # stash current PO row & record
        if current.isValid():
            main_gv.current_po_row = current.row()
            main_gv.current_po_rec = main_gv.po[current.row()]
        else:
            main_gv.current_po_row = None
            main_gv.current_po_rec = None

    def _populate_editors(self, entry: POEntry):
        win = self.window
        # source always readonly, so set directly
        win.source_edit.setPlainText(entry.msgid)

        # the three widgets we used to blocker-set in three places:
        with QSignalBlocker(win.translation_edit):
            win.translation_edit.setPlainText(entry.msgstr)

        with QSignalBlocker(win.fuzzy_toggle):
            win.fuzzy_toggle.setChecked(bool(entry.fuzzy))

        with QSignalBlocker(win.comments_edit):
            win.comments_edit.setPlainText(entry.comment or "")

    def _load_new_entry(self, current: QModelIndex):
        """
        Populate editors and suggestion pane for the newly selected POEntry.
        """
        from pref.tran_history.translation_db import db
        from pref.tran_history.tran_db_record import DatabasePORecord

        entry: POEntry = main_gv.current_po_rec
        logger.info(
            f'new record: entry (main_gv.current_po_rec) is: \n{entry}\n'
            f'flags:{entry.flags}\n'
            f'fuzzy:{entry.fuzzy}\n'
        )
        self._populate_editors(entry)

        # Load suggestions from DB
        try:
            rec = db.get_entry(entry.msgid, entry.msgctxt)
        except ValueError:
            rec = DatabasePORecord(msgid=entry.msgid, msgctxt=entry.msgctxt)
        self.model.setRecord(rec)
        main_gv.current_suggestion_record = rec
        main_gv.current_suggestion_row = None
        translate_suggestion(entry.msgid)

    def _clear_all_panes(self):
        from pref.tran_history.tran_db_record import DatabasePORecord
        win = self.window
        win.source_edit.clear()
        win.translation_edit.clear()
        win.fuzzy_toggle.setChecked(False)
        win.comments_edit.clear()
        empty = DatabasePORecord(msgstr_versions=[])
        self.model.setRecord(empty)
        main_gv.current_suggestion_record = None
        main_gv.current_suggestion_row = None
