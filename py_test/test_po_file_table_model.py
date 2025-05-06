import os
import pytest
from main_utils.po_ed_table_model import POFileTableModel
from polib import pofile

TEST_PO = os.path.join(os.path.dirname(__file__), '../test_data/vi.po')

@pytest.mark.skipif(not os.path.exists(TEST_PO), reason="vi.po not found")
def test_model_loads_po():
    po = pofile(TEST_PO)
    model = POFileTableModel(column_headers=[])
    model.setEntries(po)
    entries = model.entries()
    assert isinstance(entries, list)
    assert len(entries) == len(po)
