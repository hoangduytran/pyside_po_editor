from PySide6.QtCore import Qt, QItemSelectionModel
from PySide6.QtWidgets import QTableView, QMessageBox
from gv import main_gv

class SelectableTable(QTableView):
    def mousePressEvent(self, ev):
        if ev.modifiers() & Qt.ControlModifier:
            idx = self.indexAt(ev.pos())
            if idx.isValid():
                sel = self.selectionModel()
                sel.select(idx, QItemSelectionModel.Toggle | QItemSelectionModel.Rows)
                # manually fire currentChanged so editors + fuzzy update too
                self.currentRowChanged.emit(idx.row(), idx.row())
            return
        super().mousePressEvent(ev)

def on_translation_save():
    action = main_gv.window.get_action('on_translation_changed')
    action()

def on_delete_entry():
    tbl = main_gv.table
    sel = tbl.selectionModel().selectedRows()
    if not sel: return

    rows = sorted((idx.row() for idx in sel), reverse=True)
    answer = QMessageBox.question(
        main_gv.window, "Delete Entry",
        f"Really delete {len(rows)} entr{'y' if len(rows)==1 else 'ies'}?",
        QMessageBox.Yes|QMessageBox.No
    )
    if answer != QMessageBox.Yes:
        return

    for r in rows:
        if main_gv.po and 0 <= r < len(main_gv.po):
            main_gv.po.pop(r)
    main_gv.window.table_model.setEntries(main_gv.po)
    main_gv.current_po_row = None
    main_gv.table.clearSelection()
    main_gv.source_edit.clear()
    main_gv.translation_edit.clear()
    main_gv.fuzzy_toggle.setChecked(False)
    main_gv.comments_edit.clear()
