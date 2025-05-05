from PySide6.QtWidgets import QStyledItemDelegate, QComboBox
from PySide6.QtCore import QModelIndex
from lg import logger

class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option, index: QModelIndex):
        logger.info("createEditor called")  # Debugging
        editor = QComboBox(parent)
        record = index.model()._data[index.row()]  # Access the row's DatabasePORecord
        # Populate the combo box with msgstr versions
        for version_id, msgstr in record.msgstr_versions:
            editor.addItem(f"{version_id} ▶ {msgstr}", version_id)
        return editor

    def setEditorData(self, editor, index: QModelIndex):
        logger.info("setEditorData called")  # Debugging
        record = index.model()._data[index.row()]
        if record.msgstr_versions:
            current_version = record.msgstr_versions[0][0]  # Default to the first version
            editor.setCurrentText(f"{current_version} ▶ {record.msgstr_versions[0][1]}")

    def setModelData(self, editor, model, index: QModelIndex):
        logger.info("setModelData called")  # Debugging
        selected_version = editor.currentData()  # Get the selected version ID from the QComboBox
        record = index.model()._data[index.row()]

        # Check if the selected version already exists in msgstr_versions
        for version_id, msgstr in record.msgstr_versions:
            if version_id == selected_version:
                # If the selected version already exists, do nothing
                logger.info(f"Version {selected_version} already exists, no update performed.")
                return  # Early exit since no update is needed

        # Now check if the selected msgstr is different from the last version's msgstr
        latest_version_id, latest_msgstr = record.msgstr_versions[-1] if record.msgstr_versions else (None, None)

        # If the selected msgstr is different from the latest version, update
        if latest_msgstr != msgstr:
            record.update_translation_version(msgstr)
            logger.info(f"Updated to new version {selected_version}: {msgstr}")
        else:
            logger.info(f"Selected version {selected_version} is the same as the latest version, no update needed.")
