from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from pref.tran_history.tran_db_record import DatabasePORecord  # adjust import as needed

class VersionTableModel(QAbstractTableModel):
    """
    Table model for displaying the msgstr_versions of a DatabasePORecord:
    column 0 = version_id, column 1 = translation text.
    """
    def __init__(self, record: DatabasePORecord, parent=None):
        super().__init__(parent)
        self._record = record

    def rowCount(self, parent=QModelIndex()):
        return len(self._record.msgstr_versions)

    def columnCount(self, parent=QModelIndex()):
        return 2  # version_id, translation_text

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.EditRole):
            return None

        version_id, text = self._record.msgstr_versions[index.row()]
        if index.column() == 0:
            return version_id
        elif index.column() == 1:
            return text
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return ("Version", "Translation")[section]
        return None

    def clear(self):
        """
        Remove all entries from the model.
        """
        self.beginResetModel()
        # if you wrap a DatabasePORecord:
        if hasattr(self, '_record'):
            # clear the record’s versions
            self._record.msgstr_versions = []
        else:
            # older style: if you kept a list on self._versions
            self._versions = []
        self.endResetModel()

    def setRecord(self, record: DatabasePORecord):
        """
        Switch the model to a different DatabasePORecord and refresh the view.
        """
        self.beginResetModel()
        self._record = record
        self.endResetModel()

    def record(self) -> DatabasePORecord:
        """Return the current DatabasePORecord."""
        return self._record

    def refresh(self):
        """
        Re‐load the record’s versions from the database (if needed)
        and notify any attached views.
        """
        # If your record supports re‐loading from the DB:
        try:
            self._record.retrieve_from_db()
        except Exception:
            pass

        # Tell Qt that the model has radically changed
        self.beginResetModel()
        self.endResetModel()
