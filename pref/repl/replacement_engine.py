# replacement_engine.py
import os
import plistlib
import json
import csv
import sqlite3
from typing import List

import yaml  # Requires PyYAML installed


class ReplacementRecord:
    """
    Represents a single text-replacement pair.
    """
    def __init__(self, trigger: str, replacement: str):
        self.trigger = trigger
        self.replacement = replacement

    def to_dict(self) -> dict:
        return {'replace': self.trigger, 'with': self.replacement}

    @classmethod
    def from_dict(cls, data: dict) -> 'ReplacementRecord':
        return cls(data.get('replace', ''), data.get('with', ''))


class BaseHandler:
    """
    Base interface for import/export handlers.
    """
    @staticmethod
    def import_file(path: str) -> List[ReplacementRecord]:
        raise NotImplementedError

    @staticmethod
    def export_file(records: List[ReplacementRecord], path: str) -> None:
        raise NotImplementedError


class PlistHandler(BaseHandler):
    @staticmethod
    def import_file(path: str) -> List[ReplacementRecord]:
        with open(path, 'rb') as f:
            data = plistlib.load(f)
        try:
            rep_list = [ReplacementRecord(item['replace'], item['with']) for item in data]
        except Exception as e:
            rep_list = [ReplacementRecord(item['shortcut'], item['phrase']) for item in data]
        return rep_list

    @staticmethod
    def export_file(records: List[ReplacementRecord], path: str) -> None:
        plist_data = [r.to_dict() for r in records]
        with open(path, 'wb') as f:
            plistlib.dump(plist_data, f)


class JsonHandler(BaseHandler):
    @staticmethod
    def import_file(path: str) -> List[ReplacementRecord]:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [ReplacementRecord(item['replace'], item['with']) for item in data]

    @staticmethod
    def export_file(records: List[ReplacementRecord], path: str) -> None:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump([r.to_dict() for r in records], f, ensure_ascii=False, indent=2)


class CsvHandler(BaseHandler):
    @staticmethod
    def import_file(path: str) -> List[ReplacementRecord]:
        records = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    records.append(ReplacementRecord(row[0], row[1]))
        return records

    @staticmethod
    def export_file(records: List[ReplacementRecord], path: str) -> None:
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for r in records:
                writer.writerow([r.trigger, r.replacement])


class YamlHandler(BaseHandler):
    @staticmethod
    def import_file(path: str) -> List[ReplacementRecord]:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        records = []
        for entry in data.get('matches', []):
            trigger = entry.get('trigger')
            repl = entry.get('replace')
            if trigger and repl:
                records.append(ReplacementRecord(trigger, repl))
        return records

    @staticmethod
    def export_file(records: List[ReplacementRecord], path: str) -> None:
        data = {'matches': [{'trigger': r.trigger, 'replace': r.replacement} for r in records]}
        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f)


class AHKHandler(BaseHandler):
    @staticmethod
    def import_file(path: str) -> List[ReplacementRecord]:
        records = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('::'):
                    parts = line.strip()[2:].split('::', 1)
                    if len(parts) == 2:
                        records.append(ReplacementRecord(parts[0], parts[1]))
        return records

    @staticmethod
    def export_file(records: List[ReplacementRecord], path: str) -> None:
        with open(path, 'w', encoding='utf-8') as f:
            for r in records:
                f.write(f"::{r.trigger}::{r.replacement}\n")


class AclHandler(BaseHandler):
    @staticmethod
    def import_file(path: str) -> List[ReplacementRecord]:
        records = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(None, 1)
                if len(parts) == 2:
                    records.append(ReplacementRecord(parts[0], parts[1]))
        return records

    @staticmethod
    def export_file(records: List[ReplacementRecord], path: str) -> None:
        with open(path, 'w', encoding='utf-8') as f:
            for r in records:
                f.write(f"{r.trigger}\t{r.replacement}\n")


class BambooMacroHandler(BaseHandler):
    @staticmethod
    def import_file(path: str) -> List[ReplacementRecord]:
        records = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(':', 1)
                if len(parts) == 2:
                    records.append(ReplacementRecord(parts[0], parts[1]))
        return records

    @staticmethod
    def export_file(records: List[ReplacementRecord], path: str) -> None:
        with open(path, 'w', encoding='utf-8') as f:
            for r in records:
                f.write(f"{r.trigger}:{r.replacement}\n")


class SqliteHandler(BaseHandler):
    @staticmethod
    def import_file(path: str) -> List[ReplacementRecord]:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("SELECT abbreviation, phrase FROM combos;")
        rows = cursor.fetchall()
        conn.close()
        return [ReplacementRecord(r[0], r[1]) for r in rows]

    @staticmethod
    def export_file(records: List[ReplacementRecord], path: str) -> None:
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS combos (abbreviation TEXT, phrase TEXT);")
        cursor.executemany("INSERT INTO combos (abbreviation, phrase) VALUES (?, ?);",
                           [(r.trigger, r.replacement) for r in records])
        conn.commit()
        conn.close()


class M17nHandler(BaseHandler):
    @staticmethod
    def import_file(path: str) -> List[ReplacementRecord]:
        records = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip().startswith('#') or not line.strip():
                    continue
                parts = line.strip().split(None, 2)
                if len(parts) >= 2:
                    trigger = parts[0]
                    records.append(ReplacementRecord(trigger, parts[-1] if len(parts) == 3 else ''))
        return records

    @staticmethod
    def export_file(records: List[ReplacementRecord], path: str) -> None:
        raise NotImplementedError("Export to m17n format is not supported.")


class ReplacementEngine:
    """
    Main engine to import/export across multiple formats.
    """
    HANDLERS = {
        'plist': PlistHandler,
        'json': JsonHandler,
        'csv': CsvHandler,
        'yml': YamlHandler,
        'yaml': YamlHandler,
        'ahk': AHKHandler,
        'acl': AclHandler,
        'macro': BambooMacroHandler,
        'pexdb': SqliteHandler,
        'sqlite': SqliteHandler,
        'mim': M17nHandler,
    }

    @classmethod
    def import_file(cls, fmt: str, path: str) -> List[ReplacementRecord]:
        handler = cls.HANDLERS.get(fmt.lower())
        if not handler:
            raise ValueError(f"Unsupported format: {fmt}")
        return handler.import_file(path)

    @classmethod
    def export_file(cls, fmt: str, records: List[ReplacementRecord], path: str) -> None:
        handler = cls.HANDLERS.get(fmt.lower())
        if not handler:
            raise ValueError(f"Unsupported format: {fmt}")
        handler.export_file(records, path)

# End of replacement_engine.py
