import pytest
from po_editor.tab_record import TabRecord

def test_tab_record_defaults():
    rec = TabRecord()
    assert rec.file_path is None
    assert rec.file_name is None
    assert rec.dirty is False
    assert isinstance(rec.exclude_flags, list) and rec.exclude_flags == []
    assert isinstance(rec.include_flags, list) and rec.include_flags == []

def test_tab_record_kwargs():
    rec = TabRecord(file_path="a.po", file_name="a.po", dirty=True)
    assert rec.file_path == "a.po"
    assert rec.file_name == "a.po"
    assert rec.dirty is True
