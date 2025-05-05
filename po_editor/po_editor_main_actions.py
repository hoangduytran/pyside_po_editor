from main_utils.actions_factory import get_actions
from main_utils.table_widgets import SelectableTable
from main_utils.table_widgets import on_translation_save, on_delete_entry
# …plus whatever imports your top‐level GUI needs…

# then in your GUI setup you just:
# acts = get_actions(main_gv)
# self.table.clicked.connect(lambda idx: acts['on_table_selection'](idx.row(), idx.column()))
# self.table.selectionModel().currentChanged.connect(self.sugg_ctrl.on_row_change)
# and so on…
