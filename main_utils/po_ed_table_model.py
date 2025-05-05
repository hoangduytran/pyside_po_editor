from polib import POEntry
from typing import List, Optional
from PySide6.QtCore    import Qt, QAbstractTableModel, QModelIndex
from polib             import POEntry

class POFileTableModel(QAbstractTableModel):
    """
    Table model for displaying PO entries with columns:
      0: msgid, 1: msgctxt, 2: msgstr, 3: fuzzy, 4: linenum
    """
    def __init__(
        self,
        entries: Optional[List[POEntry]] = None,
        parent=None,
        column_headers: List[str] = None
    ):
        super().__init__(parent)
        self._entries = entries or []
        self.column_headers = column_headers or []
        self.FUZZY_COL = 3

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._entries)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.column_headers)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None

        entry = self._entries[index.row()]
        col   = index.column()

        # 1) Qt will only draw a checkbox if you handle this role:
        if role == Qt.CheckStateRole and col == self.FUZZY_COL:
            return Qt.Checked if entry.fuzzy else Qt.Unchecked

        # 2) Your existing text for other columns:
        if role == Qt.DisplayRole:
            if col == 0:
                return entry.msgid
            elif col == 1:
                return entry.msgctxt or ""
            elif col == 2:
                return entry.msgstr
            elif col == self.FUZZY_COL:
                # we don’t return anything here for the checkbox
                return None
            elif col == 4:
                return entry.linenum
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return None
        return self.column_headers[section] if 0 <= section < len(self.column_headers) else None

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.NoItemFlags

        base = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if index.column() == self.FUZZY_COL:
            # make it a checkbox
            return base | Qt.ItemIsUserCheckable
        # everything else stays read-only
        return base

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if not index.isValid():
            return False

        # # 1) handle clicks on the checkbox
        if index.column() == self.FUZZY_COL and role == Qt.CheckStateRole:
            entry = self._entries[index.row()]
            entry.fuzzy = (value == Qt.Checked)
            self.dataChanged.emit(index, index, [Qt.CheckStateRole])
            return True

        # # 2) your existing msgstr edit
        # if index.column() == 2 and role == Qt.EditRole:
        #     entry = self._entries[index.row()]
        #     entry.msgstr = value
        #     self.dataChanged.emit(index, index, [Qt.DisplayRole])
        #     return True
        return False

    def setEntries(self, entries: List[POEntry]):
        self.beginResetModel()
        self._entries = entries
        self.endResetModel()

    def entries(self) -> List[POEntry]:
        return self._entries
