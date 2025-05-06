import os
from search.fast_search import find_all_files

def test_find_all_files(tmp_path):
    root = tmp_path / "root"
    sub  = root / "sub"
    root.mkdir()
    sub.mkdir()
    file1 = sub / "f1.txt"
    file1.write_text("hello")
    files = find_all_files(str(root), None)
    assert str(file1) in files
