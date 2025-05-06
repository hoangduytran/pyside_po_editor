import pytest

modules = [
    'main_utils.actions_factory',
    'main_utils.collapsible_section',
    'main_utils.import_worker',
    'main_utils.left_tab_bar',
    'main_utils.main_button_enum',
    'main_utils.main_editor_tab',
    'main_utils.main_editor_tab_manager',
    'main_utils.main_toolbar_manager',
    'main_utils.po_ed_table_model',
    'main_utils.popup_mnu',
    'main_utils.safe_emit',
    'main_utils.table_widgets',
    'po_editor.po_editor_widget',
    'po_editor.po_editor_main_menu',
    'po_editor.po_editor_main_gui',
    'po_editor.po_editor_main_actions',
    'po_editor.tab_record',
    'workspace.file_search_tab',
    'workspace.find_replace_bar',
    'workspace.search_dock',
    'workspace.workspace_tab',
    'search.fast_search',
    'search.fast_search_open_ext_editor',
]

@pytest.mark.parametrize('mod', modules)
def test_import_module(mod):
    __import__(mod)
