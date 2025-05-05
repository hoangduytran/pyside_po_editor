from PySide6.QtWidgets import QWidget, QDockWidget, QListWidget, QListWidgetItem, QVBoxLayout, QLabel, QSizePolicy, QToolTip
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from lg import logger

BG_COLOR = "white"
HL_COLOR = "#bec8b7"

class SearchNavBar(QDockWidget):
    """
    A custom navigation bar that displays a list of found record indices.
    Clicking on an item will emit a signal to jump to that record.
    It is dockable in the main window.
    """

    # Signal to notify when a specific record (index) is selected
    record_selected = Signal(int)
    # Signal to notify when the navigation bar is closed
    navbar_closed = Signal()
    # Signal to notify when a specific record (index) is selected
    record_selected = Signal(int)

    def __init__(self, title="Search Results", parent=None):
        super().__init__(title, parent)

        self.found_indices = []  # List of indices for found records
        self.total_rows = 0  # Total number of rows in the dataset

        # Create the layout for the widget
        widget = QWidget(self)
        layout = QVBoxLayout(widget)

        # Create a QListWidget for displaying found records (indices)
        self.list_widget = QListWidget(self)
        self.list_widget.setStyleSheet(f"background-color: {BG_COLOR};")
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(self.list_widget)

        # Connect item clicked event to jump to that record (external call)
        self.list_widget.itemClicked.connect(self.on_item_clicked)

        # Set the widget in the QDockWidget
        self.setWidget(widget)

        self.setMinimumWidth(15)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  # Ensure width doesn't expand

    def setTotal(self, total_rows: int):
        """Set the total number of rows in the dataset."""
        self.total_rows = total_rows
        # No need to redraw here as the list is updated on found records change

    def setFoundRecords(self, found_indices: list[int]):
        """Set the indices of found records and update the list."""
        self.found_indices = found_indices
        self.updateList()  # Update the list with found indices

    def updateList(self):
        """Update the QListWidget with the found record indices."""
        self.list_widget.clear()  # Clear previous items

        for idx in self.found_indices:
            item = QListWidgetItem(f"Row {idx+1}")
            # Highlight the found record items with a different color
            item.setBackground(QColor(HL_COLOR))
            self.list_widget.addItem(item)

    def on_item_clicked(self, item: QListWidgetItem):
        """Called when a user clicks an item in the list, to jump to the record."""
        item_txt = item.text()
        int_value = int(item_txt.split()[1])-1 # subtract 1 to match the original

        # Get the index from found_indices, ensure it maps correctly to the page
        global_index = self.found_indices.index(int_value)

        # Emit the signal with the correct global index
        self.record_selected.emit(global_index)  # Emit the signal with the selected index
        logger.info(f'selected {global_index}')

    def closeEvent(self, event):
        """Override the close event to emit the navbar_closed signal."""
        self.navbar_closed.emit()  # Emit the custom signal when closing
        event.accept()  # Proceed with closing the widget

