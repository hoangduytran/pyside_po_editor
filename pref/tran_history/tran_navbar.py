import random
from PySide6.QtCore    import Qt, Signal
from PySide6.QtGui     import QColor
from PySide6.QtWidgets import (
    QDockWidget,
    QListWidget,
    QListWidgetItem,
)

class NavBar(QDockWidget):
    # ─── class‐level constants for your two colors ────────────────
    MARKED_COLOR   = QColor("lightgreen")
    UNMARKED_COLOR = QColor("lightgray")

    # signal that fires with the row number when a marked item is clicked
    item_selected = Signal(int)

    def __init__(self, title="Navigation", parent=None, width=15):
        super().__init__(title, parent)
        self.total_slots = 0

        # allow docking on left or right
        self.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )

        # internal storage of (row, is_marked)
        self._items = []

        # the list widget
        self._list = QListWidget()
        self.setWidget(self._list)

        # fix the width
        self.setFixedWidth(width)

        # forward clicks
        self._list.itemClicked.connect(self._on_item_clicked)

    def setHighlights(self, item_list: list):
        pass

    def setTotal(self, total: int):
        self.total_slots = total
        self.update()

    def _on_item_clicked(self, item: QListWidgetItem):
        # extract row and emit only if marked
        row = int(item.text().split()[1])
        self.item_selected.emit(row)

    def set_items(self, items: list[tuple[int, bool]]):
        """Replace the contents with a new list of (row, is_marked)."""
        self._items = items
        self._list.clear()

        for row, is_marked in items:
            lw_item = QListWidgetItem(f"Row {row}")
            if is_marked:
                lw_item.setBackground(self.MARKED_COLOR)
                lw_item.setFlags(
                    lw_item.flags()
                    | Qt.ItemIsSelectable
                    | Qt.ItemIsEnabled
                )
            else:
                lw_item.setBackground(self.UNMARKED_COLOR)
                lw_item.setFlags(Qt.NoItemFlags)  # not clickable
            self._list.addItem(lw_item)

    def get_items(self) -> list[tuple[int, bool]]:
        """Return the current list of (row, is_marked)."""
        return self._items

    def clear(self):
        """Remove all items."""
        self._items = []
        self._list.clear()
