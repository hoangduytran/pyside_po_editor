import sqlite3, time, os
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QFileDialog, QMessageBox
from polib import pofile, POEntry
from gv import main_gv
from db_const import DB_PATH
from lg import logger

class ImportWorker(QObject):
    progress = Signal(int, int)
    finished = Signal()
    error    = Signal(str)

    def __init__(self, path: str):
        super().__init__()
        self.path = path

    @Slot()
    def run(self):
        from pref.tran_history.translation_db import db
        try:
            po_list = pofile(self.path)
            total   = len(po_list)
            for idx, msg in enumerate(po_list, start=1):
                db.create_sugg_from_po_entry(msg)
                self.progress.emit(idx, total)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


def import_po_fast(path: str):
    conn = sqlite3.connect(DB_PATH)
    c    = conn.cursor()
    c.execute("PRAGMA journal_mode = MEMORY;")
    c.execute("PRAGMA synchronous = OFF;")

    po_list = pofile(path)
    eng_rows = [(e.msgid, e.msgctxt) for e in po_list]

    conn.execute("BEGIN;")
    c.executemany(
        "INSERT OR IGNORE INTO english_text(en_text,context) VALUES(?,?);",
        eng_rows
    )

    c.execute("SELECT unique_id,en_text,context FROM english_text;")
    id_map = {(en,ctx): uid for uid,en,ctx in c.fetchall()}

    tran_rows = []
    for e in po_list:
        uid = id_map[(e.msgid, e.msgctxt)]
        c.execute("SELECT COALESCE(MAX(version_id),0) FROM tran_text WHERE unique_id=?;", (uid,))
        last = c.fetchone()[0] or 0
        tran_rows.append((uid, last+1, e.msgstr))

    c.executemany(
        "INSERT INTO tran_text(unique_id,version_id,tran_text) VALUES(?,?,?);",
        tran_rows
    )
    conn.commit()
    conn.close()


def on_import_po():
    path, _ = QFileDialog.getOpenFileName(
        main_gv.window, "Import translations from PO", "", "PO Files (*.po)"
    )
    if not path:
        return

    start = time.time()
    try:
        import_po_fast(path)
    except Exception as e:
        QMessageBox.critical(main_gv.window, "Import Error", str(e))
        return

    main_gv.window.load_entries()
    elapsed = time.time() - start
    QMessageBox.information(
        main_gv.window,
        "Import Complete",
        f"Imported {os.path.basename(path)} in {elapsed:.2f} seconds."
    )
