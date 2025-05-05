# pref/tran_history/db_po_rec.py

import hashlib
import difflib
import re
import sqlite3
from typing import List, Optional
from polib import POEntry
from gv import DB_PATH, logger
from pref.tran_history.translation_db import db as translation_db


class DatabasePORecord:
    """
    In-memory representation of a PO entry and its translation history.
    Backed by the TranslationDB singleton (`translation_db`).
    """
    def __init__(
        self,
        unique_id: Optional[int] = None,
        msgid: Optional[str] = None,
        msgctxt: Optional[str] = None,
        msgstr_versions: Optional[List[tuple]] = None
    ):
        self.unique_id = unique_id
        self.msgid = msgid
        self.msgctxt = msgctxt
        # List of (version_id, translation_text)
        self.msgstr_versions = msgstr_versions or []

    def __repr__(self):
        vs = ', '.join(f"({v}, '{t}')" for v, t in self.msgstr_versions)
        return (
            f"DatabasePORecord(unique_id={self.unique_id}, msgid={self.msgid!r}, "
            f"msgctxt={self.msgctxt!r}, msgstr_versions=[{vs}])"
        )

    # ─── In-Memory Queries and Utilities ─────────────────────────────────────
    def has_tran_text(self, translation: str) -> bool:
        """Return True if `translation` exists in the in-memory versions."""
        return any(txt == translation for _, txt in self.msgstr_versions)

    @staticmethod
    def _normalize(text: str) -> str:
        """Lower-case, strip, collapse whitespace to single spaces."""
        return re.sub(r"\s+", " ", text.strip().lower())

    def is_virtually_same(self, translation: str, threshold: float = 0.85) -> bool:
        """
        Return True if `translation` is similar (>= threshold) to any existing version.
        """
        t_norm = self._normalize(translation)
        for _, existing in self.msgstr_versions:
            if difflib.SequenceMatcher(None, t_norm, self._normalize(existing)).ratio() >= threshold:
                return True
        return False

    # ─── Version Filtering and Deduplication ─────────────────────────────────
    def _filter_versions(self, versions: List[tuple]) -> List[str]:
        """
        Remove empty strings and ones equal to the source `msgid`.
        Returns a list of cleaned translation texts.
        """
        mid = (self.msgid or "").strip().lower()
        return [t.strip() for _, t in versions if t.strip() and t.strip().lower() != mid]

    def _dedupe_versions(self, texts: List[str]) -> List[str]:
        """
        Remove exact duplicates, preserving first occurrence order.
        """
        seen = set(); unique = []
        for t in texts:
            if t not in seen:
                seen.add(t)
                unique.append(t)
        return unique

    def _fuzzy_dedupe(self, texts: List[str], threshold: float) -> List[str]:
        """
        Remove near-duplicates using SequenceMatcher similarity >= threshold.
        """
        def similar(a, b):
            return difflib.SequenceMatcher(None, self._normalize(a), self._normalize(b)).ratio() >= threshold

        result = []
        for t in texts:
            if not any(similar(t, u) for u in result):
                result.append(t)
        return result

    # ─── Persistence Operations ──────────────────────────────────────────────
    def retrieve_from_db(self) -> None:
        """
        Load this record from the DB (msgid+msgctxt) into memory.
        """
        rec = translation_db.get_entry(self.msgid, self.msgctxt)
        self.unique_id = rec.unique_id
        self.msgid = rec.msgid
        self.msgctxt = rec.msgctxt
        self.msgstr_versions = rec.msgstr_versions

    def insert_to_db(self) -> None:
        """
        Insert a new english_text row (and optional initial translation)
        into the DB, then reload versions.
        """
        initial = self.msgstr_versions[0][1] if self.msgstr_versions else None
        rec = translation_db.add_entry(self.msgid, self.msgctxt, initial=initial)
        self.unique_id = rec.unique_id
        self.msgstr_versions = rec.msgstr_versions

    def update_translation_version(self, translation: str) -> None:
        """
        Append a new translation version in the DB (skips duplicates).
        Refresh in-memory versions.
        """
        rec = translation_db.add_version(self.unique_id, translation)
        self.msgstr_versions = rec.msgstr_versions

    def delete_record(self) -> None:
        """Delete this record entirely from the DB and clear memory."""
        translation_db.delete_entry(self.unique_id)
        self.unique_id = None
        self.msgid = None
        self.msgctxt = None
        self.msgstr_versions = []

    def _persist_versions(self, texts: List[str]) -> None:
        """
        Wipe all tran_text rows for this unique_id and reinsert `texts`.
        """
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM tran_text WHERE unique_id = ?", (self.unique_id,))
        for idx, t in enumerate(texts, start=1):
            c.execute(
                "INSERT INTO tran_text(unique_id, version_id, tran_text) VALUES(?, ?, ?)",
                (self.unique_id, idx, t)
            )
        conn.commit(); conn.close()
        logger.info(f"Persisted {len(texts)} versions for record {self.unique_id}")

    def update_record_with_changes(self, fuzzy_threshold: Optional[float] = None) -> bool:
        """
        Apply in-memory changes to the DB:
          1. Filter and dedupe versions (exact + optional fuzzy).
          2. If record is new, insert source+versions; otherwise overwrite all.
        Returns True if a new english_text row was created.
        """
        is_new = self.unique_id is None
        # 1) Filter
        filtered = self._filter_versions(self.msgstr_versions)
        # 2) Exact dedupe
        unique = self._dedupe_versions(filtered)
        # 3) Optional fuzzy dedupe
        if fuzzy_threshold is not None:
            unique = self._fuzzy_dedupe(unique, fuzzy_threshold)
        # 4) Renumber in-memory
        self.msgstr_versions = [(i, t) for i, t in enumerate(unique, start=1)]

        if is_new:
            self.insert_to_db()
            # append any remaining versions
            for _, t in self.msgstr_versions[1:]:
                self.update_translation_version(t)
        else:
            self._persist_versions(unique)

        return is_new

    # ─── In-Memory CRUD for msgstr_versions ────────────────────────────────
    def add_version_mem(self, translation: str) -> None:
        """
        Append a new in-memory translation version if not already present.
        """
        is_valid = bool(translation)
        if not is_valid:
            return False

        temp_dict = dict(self.msgstr_versions)
        temp_txt_list = list(set(temp_dict.values()))
        is_new = (translation not in temp_txt_list)
        if is_new:
            temp_txt_list.append(translation)

        new_msgstr = [(i, txt) for (i, txt) in enumerate(temp_txt_list)]
        is_changed = (self.msgstr_versions != new_msgstr)
        if is_changed:
            self.msgstr_versions = new_msgstr
        return is_changed

    def delete_version_mem(self, version_id: int) -> None:
        """Remove an in-memory version by its ID and renumber."""
        self.msgstr_versions = [v for v in self.msgstr_versions if v[0] != version_id]
        self._renumber_versions()

    def reverse_versions_mem(self) -> None:
        """Reverse the in-memory version list and renumber."""
        texts = [txt for _, txt in self.msgstr_versions][::-1]
        self.msgstr_versions = [(i, t) for i, t in enumerate(texts, start=1)]

    def _renumber_versions(self) -> None:
        """Ensure version IDs are sequential starting at 1."""
        self.msgstr_versions = [(i, txt) for i, (_, txt) in enumerate(self.msgstr_versions, start=1)]
