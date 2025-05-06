# py_test/conftest.py
import os
import sys
import pytest
from PySide6.QtWidgets import QApplication

# ─── Make sure the project root is on sys.path ─────────
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Single QApplication for all Qt tests."""
    return QApplication([])
