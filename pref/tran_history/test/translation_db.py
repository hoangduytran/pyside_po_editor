# pref/translation_db.py

import os, sqlite3
from PySide6.QtWidgets import (
    QTableWidgetItem,
    QFileDialog,
)
from pref.repl.replacement_gui import ReplacementsDialog  # your base class
from polib import POEntry, pofile
from pref.tran_history.test.db_po_rec import DatabasePORecord
from typing import List

DB_DIR  = os.path.join(os.getcwd(), "tran_db")
DB_PATH = os.path.join(DB_DIR, "translations.db")

class TranslationHistoryDialog(ReplacementsDialog):
    """
    Re‑uses the same structure as ReplacementsDialog but
    operates on an SQLite DB under ./tran_db/translations.db.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        os.makedirs(DB_DIR, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self._ensure_schema()
        # swap out the table headers
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Version", "Translation"])
        # hide the search / editor panel until we know an unique_id
        self.search_field.setEnabled(False)
        self.import_btn .setText("Import PO…")
        self.export_btn .setText("Export DB…")
        # hook import/export
        self.import_btn.clicked.disconnect()
        self.export_btn.clicked.disconnect()
        self.import_btn.clicked.connect(self._import_po)
        self.export_btn.clicked.connect(self._export_db)

    # override drag/drop events on the dialog
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith(".po"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith(".po"):
                self._import_po(path)
                break

    # also override drag/drop on the table itself
    def _forward_drag_enter(self, event):
        # simply forward to the dialog handler
        return self.dragEnterEvent(event)

    def _forward_drop(self, event):
        return self.dropEvent(event)

    def _ensure_schema(self):
        c = self.conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS english_text (
          unique_id   INTEGER PRIMARY KEY AUTOINCREMENT,
          en_text     TEXT    NOT NULL,
          context     TEXT    
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS tran_text (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          unique_id   INTEGER NOT NULL,
          version_id  INTEGER NOT NULL,
          tran_text   TEXT    NOT NULL,
          changed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(unique_id) REFERENCES english_text(unique_id),
          UNIQUE(unique_id, version_id)
        )""")
        self.conn.commit()

    # after the super().__init__, wire the table’s events
    def showEvent(self, ev):
        super().showEvent(ev)
        # install our drag/drop on the table widget
        self.table.dragEnterEvent = self._forward_drag_enter
        self.table.dropEvent = self._forward_drop

    def load_msg(self, msg: POEntry):
        en_text = msg.msgid
        context = msg.msgctxt  # might be None

        c = self.conn.cursor()
        # insert the row (allowing NULL if context is None)
        c.execute("""
            INSERT INTO english_text(en_text, context)
                 VALUES (?, ?)
        """, (en_text, context))
        uid = c.lastrowid

        # now insert the new translation version
        c.execute("""
            SELECT tran_text
              FROM tran_text
             WHERE unique_id=?
          ORDER BY version_id DESC
             LIMIT 1
        """, (uid,))
        last = c.fetchone()
        last_version = (last[0] if last else 0)

        c.execute("""
            INSERT INTO tran_text(unique_id, version_id, tran_text)
                 VALUES (?, ?, ?)
        """, (uid, last_version + 1, msg.msgstr))
        self.conn.commit()

        # refresh your UI
        self._replacement_refresh_table()

    def load_for_entry(self, unique_id, en_text, context):
        """
        Call this whenever the user clicks on a PO row;
        it will insert into english_text if needed, then
        load the versions into the table.
        """
        c = self.conn.cursor()
        # ensure the english_text row exists
        c.execute("""
          INSERT OR IGNORE INTO english_text(en_text,context)
          VALUES(?,?)
        """, (en_text, context))
        self.conn.commit()

        # look up its ID
        c.execute("""
          SELECT unique_id FROM english_text
           WHERE en_text=? AND context=?
        """, (en_text, context))
        uid = c.fetchone()[0]
        self.current_unique_id = uid

        # now populate versions
        self._replacement_refresh_table()

    def _replacement_refresh_table(self):
        self.table.setRowCount(0)
        if not hasattr(self, 'current_unique_id'):
            return

        c = self.conn.cursor()
        c.execute("""
          SELECT version_id, tran_text
            FROM tran_text
           WHERE unique_id=?
          ORDER BY version_id DESC
        """, (self.current_unique_id,))

        for vid, txt in c.fetchall():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(vid)))
            self.table.setItem(row, 1, QTableWidgetItem(txt))

    def _save_edit(self):
        """
        When the user edits in the bottom panel and hits Save,
        insert a new version if the text has changed.
        """
        new_txt = self.edit_replacement.text().strip()
        if not new_txt:
            return

        # get the latest version_id
        c = self.conn.cursor()
        c.execute("""
           SELECT MAX(version_id) FROM tran_text
            WHERE unique_id=?
        """, (self.current_unique_id,))
        last = c.fetchone()[0] or 0
        # only insert if different
        c.execute("""
          INSERT INTO tran_text(unique_id,version_id,tran_text)
          VALUES(?,?,?)
        """, (self.current_unique_id, last+1, new_txt))
        self.conn.commit()
        self._replacement_refresh_table()
        self.editor_panel.hide()

    def _import_po(self, path=None):
        """
        If called with a path, load that PO.
        Otherwise, open a file dialog.
        """
        if path is None:
            path, _ = QFileDialog.getOpenFileName(
                self, "Import translations from PO", "", "PO Files (*.po)")
            if not path:
                return

        msg: POEntry = None
        po_list = pofile(path)
        for msg in po_list:
            self.load_msg(msg)

        print(f"Imported {len(po_list)} PO records from {path!r}")

    def _export_db(self):
        # dump all translations to a .po named translation_db.po
        out = os.path.join(os.getcwd(), "translation_db.po")
        # walk english_text & tran_text to write a polib POFile
        # (left as an exercise)

    def list_records(self) -> List[DatabasePORecord]:
        """
        Return a list of DatabasePORecord objects, each representing an entry.
        """
        c = self.conn.cursor()
        c.execute("SELECT unique_id, en_text, context FROM english_text ORDER BY unique_id")
        rows = c.fetchall()

        records = []
        for row in rows:
            unique_id, msgid, msgctx = row
            record = DatabasePORecord(unique_id, msgid, msgctx)
            record.retrieve_from_db()  # Populate msgstr_versions
            records.append(record)

        return records