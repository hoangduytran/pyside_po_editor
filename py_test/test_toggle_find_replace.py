import pytest
from workspace.find_replace_bar import FindReplaceBar

def test_toggle_behavior(qapp):
    bar = FindReplaceBar(None)
    # Must show the widget so children visibility changes register
    bar.show()
    qapp.processEvents()

    # Initially replace row is hidden
    assert not bar.replace_container.isVisible()

    # Toggle on
    bar.toggle_btn.setChecked(True)
    qapp.processEvents()
    assert bar.replace_container.isVisible()

    # Toggle off
    bar.toggle_btn.setChecked(False)
    qapp.processEvents()
    assert not bar.replace_container.isVisible()

