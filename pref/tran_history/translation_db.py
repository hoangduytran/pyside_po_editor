# pref/translation_db.py
import os
import sqlite3
from typing import List, Optional, Tuple
from polib import POEntry, POFile, pofile
from local_logging import benchmark
from db_const import DB_PATH, DB_DIR
from pref.tran_history.tran_db_record import DatabasePORecord
from lg import logger

class TranslationDB:
    """
    Encapsulates all SQLite logic for translation history storage.
    Queries always fetch all matching rows before indexing, and handle `context` = None
    by generating separate queries for NULL vs. non-NULL context.
    """
    def __init__(self):
        os.makedirs(DB_DIR, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self._ensure_schema()

    def _ensure_schema(self):
        c = self.conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS english_text (
          unique_id   INTEGER PRIMARY KEY AUTOINCREMENT,
          en_text     TEXT NOT NULL,
          context     TEXT
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS tran_text (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          unique_id   INTEGER NOT NULL,
          version_id  INTEGER NOT NULL,
          tran_text   TEXT NOT NULL,
          changed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(unique_id) REFERENCES english_text(unique_id),
          UNIQUE(unique_id, version_id),
          UNIQUE(unique_id, tran_text)
        )""")
        self.conn.commit()

    def clear_database(self):
        """
        Clears all records from the database.
        """
        c = self.conn.cursor()
        c.execute("PRAGMA foreign_keys = OFF")
        c.execute("DELETE FROM tran_text")
        c.execute("DELETE FROM english_text")
        self.conn.commit()
        c.execute("PRAGMA foreign_keys = ON")
        logger.info("Database has been cleared.")

    # --- Internal Helpers ---
    def _fetch_english(self, msgid: str, context: Optional[str]) -> List[Tuple[int, str, Optional[str]]]:
        c = self.conn.cursor()
        if context is None:
            c.execute(
                "SELECT unique_id, en_text, context FROM english_text"
                " WHERE en_text = ? AND context IS NULL",
                (msgid,)
            )
        else:
            c.execute(
                "SELECT unique_id, en_text, context FROM english_text"
                " WHERE en_text = ? AND context = ?",
                (msgid, context)
            )
        return c.fetchall()

    def _fetch_translations(self, unique_id: int) -> List[Tuple[int, str]]:
        c = self.conn.cursor()
        c.execute(
            "SELECT version_id, tran_text FROM tran_text"
            " WHERE unique_id = ? ORDER BY version_id",
            (unique_id,)
        )
        return c.fetchall()

    # --- Public API ---
    def list_entries(self) -> List[DatabasePORecord]:
        """List all records."""
        c = self.conn.cursor()
        c.execute("SELECT unique_id, en_text, context FROM english_text ORDER BY unique_id")
        rows = c.fetchall()
        records: List[DatabasePORecord] = []
        for uid, en, ctx in rows:
            record = DatabasePORecord(unique_id=uid, msgid=en, msgctxt=ctx)
            # filter out empty or identical-to-msgid translations
            mid_lower = en.strip().lower()
            record.msgstr_versions = [
                (ver, txt) for ver, txt in self._fetch_translations(uid)
                if txt.strip() and txt.strip().lower() != mid_lower
            ]
            records.append(record)
        return records

    def get_entry(self, msgid: str, context: Optional[str] = None) -> DatabasePORecord:
        """Retrieve or raise if missing."""
        rows = self._fetch_english(msgid, context)
        if not rows:
            raise ValueError(f"No entry for msgid={msgid!r}, context={context!r}")
        unique_id, en_text, ctx = rows[0]
        record = DatabasePORecord(unique_id=unique_id, msgid=en_text, msgctxt=ctx)
        # filter translations
        mid_lower = en_text.strip().lower()
        record.msgstr_versions = [
            (ver, txt) for ver, txt in self._fetch_translations(unique_id)
            if txt.strip() and txt.strip().lower() != mid_lower
        ]
        return record

    def add_entry(self, msgid: str, context: Optional[str] = None, initial: Optional[str] = None) -> DatabasePORecord:
        """Insert new english_text and optional first translation."""
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO english_text(en_text, context) VALUES(?,?)",
            (msgid, context)
        )
        self.conn.commit()
        uid = c.lastrowid
        if initial is not None:
            self.add_version(uid, initial)
        return self.get_entry(msgid, context)

    def update_entry(self, unique_id: int, new_msgid: str, new_ctx: Optional[str] = None) -> DatabasePORecord:
        c = self.conn.cursor()
        c.execute(
            "UPDATE english_text SET en_text = ?, context = ? WHERE unique_id = ?",
            (new_msgid, new_ctx, unique_id)
        )
        self.conn.commit()
        return self.get_entry(new_msgid, new_ctx)

    def add_version(self, unique_id: int, msgstr: str, version: Optional[int] = None) -> DatabasePORecord:
        """
        Insert a new version row directly, then return a fully-populated record.
        """
        c = self.conn.cursor()

        # 1) Compute next version_id if not given:
        if version is None:
            c.execute(
                "SELECT COALESCE(MAX(version_id), 0) + 1 FROM tran_text WHERE unique_id = ?",
                (unique_id,)
            )
            version = c.fetchone()[0]

        # 2) Insert the new translation (UNIQUE(unique_id, tran_text) will skip duplicates)
        c.execute(
            "INSERT OR IGNORE INTO tran_text(unique_id, version_id, tran_text) VALUES(?, ?, ?)",
            (unique_id, version, msgstr)
        )
        self.conn.commit()

        # 3) Now fetch back the updated DatabasePORecord in one go:
        #    (this handles filtering out blank/identical‐to‐msgid versions for you)
        return self.get_entry_by_id(unique_id)

    def get_entry_by_id(self, unique_id: int) -> DatabasePORecord:
        """
        Load a record by its unique_id (skipping the msgid/context lookup).
        """
        c = self.conn.cursor()
        c.execute(
            "SELECT en_text, context FROM english_text WHERE unique_id = ?",
            (unique_id,)
        )
        msgid, ctx = c.fetchone()
        rec = DatabasePORecord(unique_id=unique_id, msgid=msgid, msgctxt=ctx)
        # copy & filter translations:
        mid = msgid.strip().lower()
        rec.msgstr_versions = [
            (ver, txt)
            for ver, txt in self._fetch_translations(unique_id)
            if txt.strip() and txt.strip().lower() != mid
        ]
        return rec

    def delete_entry(self, unique_id: int):
        c = self.conn.cursor()
        c.execute("DELETE FROM tran_text WHERE unique_id = ?", (unique_id,))
        c.execute("DELETE FROM english_text WHERE unique_id = ?", (unique_id,))
        self.conn.commit()

    def delete_version(self, unique_id: int, version_id: int):
        c = self.conn.cursor()
        c.execute(
            "DELETE FROM tran_text WHERE unique_id = ? AND version_id = ?",
            (unique_id, version_id)
        )
        self.conn.commit()

    def insert_po_entry(self, entry: POEntry) -> DatabasePORecord:
        """
        Insert a single POEntry into the DB using optimized logic:
        1) INSERT OR IGNORE into english_text to skip duplicates.
        2) SELECT the unique_id for (msgid, context).
        3) SELECT MAX(version_id) → next_version = max+1.
        4) INSERT into tran_text(unique_id, next_version, msgstr).
        5) RETURN the fully populated DatabasePORecord.
        """
        c = self.conn.cursor()
        # 1) Ensure source row exists
        c.execute(
            "INSERT OR IGNORE INTO english_text(en_text, context) VALUES(?, ?)",
            (entry.msgid, entry.msgctxt)
        )
        self.conn.commit()
        # 2) Fetch its unique_id
        if entry.msgctxt is None:
            c.execute(
                "SELECT unique_id FROM english_text WHERE en_text = ? AND context IS NULL",
                (entry.msgid,)
            )
        else:
            c.execute(
                "SELECT unique_id FROM english_text WHERE en_text = ? AND context = ?",
                (entry.msgid, entry.msgctxt)
            )
        unique_id = c.fetchone()[0]
        # 3) Compute next version
        c.execute(
            "SELECT COALESCE(MAX(version_id), 0) FROM tran_text WHERE unique_id = ?",
            (unique_id,)
        )
        last = c.fetchone()[0] or 0
        next_ver = last + 1
        # 4) Insert the new translation version
        c.execute(
            "INSERT INTO tran_text(unique_id, version_id, tran_text) VALUES(?, ?, ?)",
            (unique_id, next_ver, entry.msgstr)
        )
        self.conn.commit()
        # 5) Return the fresh record
        return self.get_entry(entry.msgid, entry.msgctxt)

    def get_entry_from_po_entry(self, entry: POEntry) -> DatabasePORecord:
        """
        Safely get or create a DatabasePORecord from a POEntry:
        - If no english_text row exists, insert it (with initial translation if provided).
        - If a record exists, ensure its translations are loaded.
        - If the POEntry has a non-empty msgstr:
            - If the record has no translations yet, insert this as version 1.
            - Else if it differs from the latest, append a new version.
        - Return the fully populated record.
        """
        msgid = entry.msgid
        ctx = entry.msgctxt  # may be None
        po_has_tran = bool(entry.msgstr and entry.msgstr.strip())
        tran_text = entry.msgstr if po_has_tran else ""

        # 1) Try to fetch existing record
        try:
            record = self.get_entry(msgid, ctx)
        except ValueError:
            # No existing record: create one with initial translation if present
            record = self.add_entry(msgid, ctx, initial=tran_text or None)
            return record

        # 2) Existing record: load its current translations
        record.msgstr_versions = self._fetch_translations(record.unique_id)
        rec_has_sugg = bool(record.msgstr_versions)

        # 3) If POEntry has translation, decide whether to insert a new version
        if po_has_tran:
            if not rec_has_sugg:
                # record has none yet: insert as version 1
                record = self.add_version(record.unique_id, tran_text, version=1)
            else:
                # compare to latest
                latest_txt = record.msgstr_versions[-1][1]
                if tran_text != latest_txt:
                    record = self.add_version(record.unique_id, tran_text)
        # else: PO has no translation → nothing to do

        return record

    @benchmark
    def import_po_fast(self, path: str):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("PRAGMA journal_mode = MEMORY;")
        c.execute("PRAGMA synchronous = OFF;")
        po_list = pofile(path)

        # bulk english_text
        lives = [(e.msgid, e.msgctxt) for e in po_list]
        conn.execute("BEGIN;")
        c.executemany(
            "INSERT OR IGNORE INTO english_text(en_text,context) VALUES(?,?);",
            lives
        )

        # fetch map
        c.execute("SELECT unique_id,en_text,context FROM english_text;")
        id_map = {(en, ct): uid for uid, en, ct in c.fetchall()}

        # build translations
        trans = []
        for e in po_list:
            uid = id_map[(e.msgid, e.msgctxt)]
            c.execute("SELECT MAX(version_id) FROM tran_text WHERE unique_id=?;", (uid,))
            last = c.fetchone()[0] or 0
            trans.append((uid, last + 1, e.msgstr))

        c.executemany(
            "INSERT INTO tran_text(unique_id,version_id,tran_text) VALUES(?,?,?);",
            trans
        )
        conn.commit()

    def export_po(self, out_path: str):
        po = POFile()
        for rec in self.list_entries():
            if rec.msgstr_versions:
                ver, txt = rec.msgstr_versions[-1]
            else:
                ver, txt = 0, ""
            po.append(POEntry(msgid=rec.msgid, msgstr=txt))
        po.save(out_path)

db = TranslationDB()
