from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex

class HistoryTableModel(QAbstractTableModel):
    def __init__(self, data=None, columns=None):
        """
        Initialize the model with a list of DatabasePORecord objects.

        :param data: List of DatabasePORecord instances
        :param columns: List of tuples defining column headers and behaviors
        """
        super().__init__()
        self._data = data if data else []
        self._columns = columns or []

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._columns)

    def flags(self, index: QModelIndex):
        flags = super().flags(index)
        if index.column() == 2:  # For column 2 (msgstr)
            flags |= Qt.ItemIsEditable  # Mark as editable
        return flags

    def data(self, index, role=Qt.DisplayRole):
        """
        Return the data for a specific item in the model, depending on the role.
        """
        if index.isValid():
            record = self._data[index.row()]
            column = index.column()

            if role == Qt.DisplayRole:
                # Display appropriate data based on the column
                if column == 0:  # ID
                    return record.unique_id
                elif column == 1:  # msgid
                    return record.msgid
                elif column == 2:  # msgstr
                    try:
                        return f"{record.msgstr_versions[0][0]}, {record.msgstr_versions[0][1]}"
                    except Exception as e:
                        pass
            elif role == Qt.ToolTipRole:
                # Optionally, you can add tooltips for extra information (e.g., for msgstr versions)
                if column == 2 and record.msgstr_versions:
                    return "\n".join([f"Version {v[0]}: {v[1]}" for v in record.msgstr_versions])

        return None

    def setData(self, index, value, role=Qt.EditRole):
        """
        Update data in the model. If the column is msgstr, update the corresponding DatabasePORecord.
        """
        if index.isValid() and role == Qt.EditRole:
            record = self._data[index.row()]
            column = index.column()

            if column == 2:  # msgstr
                record.update_translation_version(value)  # Update translation version in the DatabasePORecord
                self.dataChanged.emit(index, index)  # Notify that the data has changed
                return True
        return False

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Return the header data for the table. We use _columns to get the headers.
        """
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._columns[section][0]
            else:
                return str(section + 1)
        return None

    def insertRow(self, row, record):
        """
        Insert a new DatabasePORecord into the model at the specified row index.
        """
        self.beginInsertRows(Qt.QModelIndex(), row, row)
        self._data.insert(row, record)
        self.endInsertRows()

    def removeRow(self, row):
        """
        Remove a DatabasePORecord from the model at the specified row index.
        """
        self.beginRemoveRows(Qt.QModelIndex(), row, row)
        self._data.pop(row)
        self.endRemoveRows()

    def refreshData(self, data):
        """
        Refresh the model data with a new list of DatabasePORecord instances.
        """
        self.beginResetModel()
        self._data = data  # Replace old data with new records
        self.endResetModel()

    def getData(self):
        return self._data

    def getColumns(self):
        return self._columns

    # def setHeaderData(self, table_view):
    #     """ Set header behavior like ResizeToContents or Stretch from TABLE_COLUMNS """
    #     header = table_view.horizontalHeader()
    #     for col, (_, header_behavior) in enumerate(self._columns):
    #         if header_behavior == QHeaderView.ResizeToContents:
    #             header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
    #         elif header_behavior == QHeaderView.Stretch:
    #             header.setSectionResizeMode(col, QHeaderView.Stretch)
