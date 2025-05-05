# toolbars/search/toolbar_search_replace_widget.py

from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QToolButton,
    QHBoxLayout,
    QLabel,
    QSizePolicy
)
from PySide6.QtCore    import Qt, QSize
from .toolbar_search_replace_icon    import icon_from_text
from .toolbar_search_replace_symbol  import ButtonSymbol
from .toolbar_search_replace_flag_line_edit import FlagLineEdit

class ToggleFindReplace(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

        # start with the Replace row hidden, collapse it and lock height
        self.replace_container.setVisible(False)
        self._collapse_replace_row()
        self._lock_to_one_row()

        self.toggle_btn.toggled.connect(self._on_toggle)

    def _build_ui(self):
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(2,2,2,2)
        self.grid.setHorizontalSpacing(6)
        self.grid.setVerticalSpacing(1)

        # 1) Toggle button in column 0 spanning rows 0–1
        self.toggle_btn = QToolButton(self)
        ico = icon_from_text(ButtonSymbol.TOGGLE.symbol)
        self.toggle_btn.setIcon(ico)
        self.toggle_btn.setIconSize(QSize(20, 20))
        self.toggle_btn.setToolTip(ButtonSymbol.TOGGLE.tooltip)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setFixedWidth(24)
        self.toggle_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.grid.addWidget(self.toggle_btn, 0, 0, 2, 1)

        # 2) Find row: text field, flags, nav & close buttons
        self.find_container = QWidget(self)
        find_layout = QHBoxLayout(self.find_container)
        find_layout.setContentsMargins(0,0,0,0)
        find_layout.setSpacing(4)

        # — text field with only the three flag-buttons embedded —
        self.find_edit = FlagLineEdit(
            [
                ButtonSymbol.MATCH_CASE,
                ButtonSymbol.WHOLE_WORD,
                ButtonSymbol.REGEX],
            self
        )
        self.find_edit.setPlaceholderText("find")
        self.find_edit.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)  # ← CHANGE
        find_layout.addWidget(self.find_edit)

        # — result count label outside the edit —
        self.lbl_find_result = QLabel(ButtonSymbol.FIND_RESULT.symbol, self)
        self.lbl_find_result.setToolTip(ButtonSymbol.FIND_RESULT.tooltip)
        self.lbl_find_result.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lbl_find_result.adjustSize()
        find_layout.addWidget(self.lbl_find_result)  # ← ADD

        # — nav & close buttons outside the edit —
        for sym in [
            ButtonSymbol.PREV_FOUND,
            ButtonSymbol.NEXT_FOUND,
            ButtonSymbol.MATCHED_WITHIN_SELECTION,
            ButtonSymbol.CLOSE
        ]:
            btn = QToolButton(self)
            ico = icon_from_text(sym.symbol)
            btn.setIcon(ico)
            btn.setToolTip(sym.tooltip)
            btn.setCheckable(False)
            find_layout.addWidget(btn)  # ← ADD
            setattr(self, f"btn_{sym.name.lower()}", btn)

        # — spacer so external buttons stay tight —
        find_layout.addStretch(1)  # ← ADD

        self.grid.addWidget(self.find_container, 0, 1)

        # 3) Replace row: text field, flags, replace buttons
        self.replace_container = QWidget(self)
        replace_layout = QHBoxLayout(self.replace_container)
        replace_layout.setContentsMargins(0,0,0,0)
        replace_layout.setSpacing(4)

        self.replace_edit = FlagLineEdit(
            [ButtonSymbol.PRESERVE_CASE],
            self
        )
        self.replace_edit.setPlaceholderText("replace")
        self.replace_edit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        replace_layout.addWidget(self.replace_edit)

        replace_button_layout = QHBoxLayout()
        replace_button_layout.setContentsMargins(0, 0, 0, 0)
        replace_button_layout.setSpacing(4)
        replace_button_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        for sym in [
            ButtonSymbol.REPLACE_CURRENT,
            ButtonSymbol.REPLACE_ALL
        ]:
            btn = QToolButton(self)
            ico = icon_from_text(sym.symbol)
            btn.setIcon(ico)
            btn.setIconSize(QSize(20, 20))
            btn.setToolTip(sym.tooltip)
            btn.setCheckable(False)
            replace_button_layout.addWidget(btn)
            setattr(self, f"btn_{sym.name.lower()}", btn)

        # insert that sub‐layout into the main replace_layout
        replace_layout.addLayout(replace_button_layout)
        replace_layout.addStretch(1)

        # let the container expand so the stretch has room
        self.replace_container.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed
        )
        self.grid.addWidget(self.replace_container, 1, 1, 1, 1, Qt.AlignLeft)

        # prevent the find/replace column from auto-expanding
        self.grid.setColumnStretch(1, 0)  # ← CHANGE

        # keep this widget at its preferred height only
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)  # ← ADD

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # mirror width so replace matches find on resize
        self.replace_edit.setFixedWidth(self.find_edit.width())  # ← ADD

    def _collapse_replace_row(self):
        self.grid.setRowStretch(1, 0)

    def _lock_to_one_row(self):
        self.adjustSize()
        one_row_h = self.sizeHint().height()
        self.setFixedHeight(one_row_h)

    def _on_toggle(self, on: bool):
        ico = "▼" if on else "▶"
        self.toggle_btn.setIcon(icon_from_text(ico))

        if on:
            self.grid.setVerticalSpacing(0)
            self.replace_container.setVisible(True)
            self.grid.setRowStretch(1, 1)
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
        else:
            self.grid.setVerticalSpacing(1)
            self.replace_container.setVisible(False)
            self._collapse_replace_row()
            self._lock_to_one_row()
