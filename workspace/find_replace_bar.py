# workspace/find_replace_bar.py

import sys
from enum import Enum
from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout,
    QLineEdit, QToolButton, QWidgetAction,
    QSizePolicy, QHBoxLayout
)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont

from workspace.button_symbols import ButtonSymbol

@dataclass
class FindRequest:
    pattern: str
    replace_with: str
    match_case: bool
    word_boundary: bool
    use_regex: bool
    selection_only: bool


def icon_from_text(txt: str, size: int = 18) -> QIcon:
    """Render a Unicode symbol into a QIcon."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setPen(QColor("black"))
    font = QFont()
    font.setPointSize(int(size * 0.8))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pix.rect(), Qt.AlignCenter, txt)
    painter.end()
    return QIcon(pix)


class FlagLineEdit(QLineEdit):
    """A QLineEdit with trailing flag buttons."""
    def __init__(self, symbols: list[ButtonSymbol], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimumHeight(28)
        for sym in symbols:
            btn = QToolButton(self)
            btn.setIcon(icon_from_text(sym.symbol))
            btn.setIconSize(QSize(20, 20))
            btn.setToolTip(sym.tooltip)
            btn.setCheckable(sym in (
                ButtonSymbol.MATCH_CASE,
                ButtonSymbol.WORD_BOUNDARY,
                ButtonSymbol.REGEX,
                ButtonSymbol.PRESERVE_CASE,
                ButtonSymbol.SELECTION_ONLY
            ))
            action = QWidgetAction(self)
            action.setDefaultWidget(btn)
            self.addAction(action, QLineEdit.TrailingPosition)
            setattr(self, f"flag_{sym.name.lower()}", btn)


class FindReplaceBar(QWidget):
    """Collapsible Find/Replace bar with flags and navigation."""
    findRequested       = Signal(object)
    replaceOneRequested = Signal(object)
    replaceAllRequested = Signal(object)
    jumpRequested       = Signal(int)
    toggleSelectionOnly = Signal(bool)
    closeRequested      = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # whether replace row is expanded
        self.is_replacing = False
        self._build_ui()
        self._connect_signals()
        # start collapsed
        self._collapse_replace_row()
        self._lock_to_one_row()
        # sync widths after initial layout
        QTimer.singleShot(0, self._sync_widths)

    def _build_ui(self):
        grid = QGridLayout(self)
        grid.setContentsMargins(2,2,2,2)
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(2)

        # toggle expand/collapse
        self.toggle_btn = QToolButton()
        self.toggle_btn.setIcon(icon_from_text(ButtonSymbol.TOGGLE.symbol))
        self.toggle_btn.setIconSize(QSize(20, 20))
        self.toggle_btn.setToolTip(ButtonSymbol.TOGGLE.tooltip)
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(False)
        self.toggle_btn.setFixedWidth(24)
        self.toggle_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        grid.addWidget(self.toggle_btn, 0, 0, 2, 1)

        # find row
        self.find_edit = FlagLineEdit([
            ButtonSymbol.MATCH_CASE,
            ButtonSymbol.WORD_BOUNDARY,
            ButtonSymbol.REGEX
        ])
        self.find_edit.setPlaceholderText("Find")
        grid.addWidget(self.find_edit, 0, 1, 1, 6)

        self.lbl_find_result = QToolButton()
        self.lbl_find_result.setText(ButtonSymbol.FIND_RESULT.symbol)
        self.lbl_find_result.setToolTip(ButtonSymbol.FIND_RESULT.tooltip)
        self.lbl_find_result.setEnabled(False)
        grid.addWidget(self.lbl_find_result, 0, 7)

        self.btn_prev = QToolButton()
        self.btn_prev.setIcon(icon_from_text(ButtonSymbol.PREV_FOUND.symbol))
        self.btn_prev.setToolTip(ButtonSymbol.PREV_FOUND.tooltip)
        grid.addWidget(self.btn_prev, 0, 8)

        self.btn_next = QToolButton()
        self.btn_next.setIcon(icon_from_text(ButtonSymbol.NEXT_FOUND.symbol))
        self.btn_next.setToolTip(ButtonSymbol.NEXT_FOUND.tooltip)
        grid.addWidget(self.btn_next, 0, 9)

        self.btn_selection_only = QToolButton()
        self.btn_selection_only.setIcon(icon_from_text(ButtonSymbol.SELECTION_ONLY.symbol))
        self.btn_selection_only.setToolTip(ButtonSymbol.SELECTION_ONLY.tooltip)
        self.btn_selection_only.setCheckable(True)
        grid.addWidget(self.btn_selection_only, 0, 10)

        self.btn_close = QToolButton()
        self.btn_close.setIcon(icon_from_text(ButtonSymbol.CLOSE.symbol))
        self.btn_close.setToolTip(ButtonSymbol.CLOSE.tooltip)
        grid.addWidget(self.btn_close, 0, 11)

        # replace row container
        self.replace_container = QWidget(self)
        replace_layout = QHBoxLayout(self.replace_container)
        replace_layout.setContentsMargins(0,0,0,0)
        replace_layout.setSpacing(4)

        # replace edit
        self.replace_edit = FlagLineEdit([ButtonSymbol.PRESERVE_CASE])
        self.replace_edit.setPlaceholderText("Replace")
        replace_layout.addWidget(self.replace_edit)

        # replace buttons
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0,0,0,0)
        btn_layout.setSpacing(4)
        btn_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.btn_preserve = self.replace_edit.flag_preserve_case
        self.btn_replace = QToolButton()
        self.btn_replace.setIcon(icon_from_text(ButtonSymbol.REPLACE_CURRENT.symbol))
        self.btn_replace.setToolTip(ButtonSymbol.REPLACE_CURRENT.tooltip)
        btn_layout.addWidget(self.btn_replace)

        self.btn_replace_all = QToolButton()
        self.btn_replace_all.setIcon(icon_from_text(ButtonSymbol.REPLACE_ALL.symbol))
        self.btn_replace_all.setToolTip(ButtonSymbol.REPLACE_ALL.tooltip)
        btn_layout.addWidget(self.btn_replace_all)

        replace_layout.addLayout(btn_layout)
        replace_layout.addStretch(1)
        grid.addWidget(self.replace_container, 1, 1, 1, 11, Qt.AlignLeft)

        grid.setColumnStretch(1, 1)
        self.setLayout(grid)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._on_toggle(self.is_replacing)

    def _connect_signals(self):
        self.toggle_btn.clicked.connect(self._on_toggle_clicked)
        self.btn_close.clicked.connect(lambda: self.closeRequested.emit())
        self.find_edit.returnPressed.connect(self._emit_find)
        self.btn_next.clicked.connect(lambda: self.jumpRequested.emit(+1))
        self.btn_prev.clicked.connect(lambda: self.jumpRequested.emit(-1))
        self.btn_selection_only.toggled.connect(
            lambda on: self.toggleSelectionOnly.emit(on)
        )
        self.btn_replace.clicked.connect(lambda: self._emit_replace(True))
        self.btn_replace_all.clicked.connect(lambda: self._emit_replace(False))

    def _on_toggle_clicked(self):
        """Flip replace state and call toggle logic."""
        self.is_replacing = not self.is_replacing
        self.toggle_btn.setChecked(self.is_replacing)
        # update icon and layout
        self._on_toggle(self.is_replacing)

    def _on_toggle(self, on: bool):
        """Handle expand/collapse based on flag."""
        self.toggle_btn.setIcon(icon_from_text("▼" if on else "▶"))
        if on:
            self.replace_container.setVisible(True)
            self.layout().setRowStretch(1, 1)
            self.setMinimumHeight(0)
            self.setMaximumHeight(16777215)
        else:
            self.replace_container.setVisible(False)
            self._collapse_replace_row()
            self._lock_to_one_row()

    def _lock_to_one_row(self):
        self.adjustSize()
        h = self.sizeHint().height()
        self.setFixedHeight(h)

    def _collapse_replace_row(self):
        self.layout().setRowStretch(1, 0)

    def _sync_widths(self):
        w = self.find_edit.width()
        self.replace_edit.setMinimumWidth(w)
        self.replace_edit.setMaximumWidth(w)

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_widths()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_widths()

    def _emit_find(self):
        req = FindRequest(
            pattern=self.find_edit.text(),
            replace_with=self.replace_edit.text(),
            match_case=self.find_edit.flag_match_case.isChecked(),
            word_boundary=self.find_edit.flag_word_boundary.isChecked(),
            use_regex=self.find_edit.flag_regex.isChecked(),
            selection_only=self.btn_selection_only.isChecked()
        )
        self.findRequested.emit(req)

    def _emit_replace(self, one: bool):
        req = FindRequest(
            pattern=self.find_edit.text(),
            replace_with=self.replace_edit.text(),
            match_case=self.find_edit.flag_match_case.isChecked(),
            word_boundary=self.find_edit.flag_word_boundary.isChecked(),
            use_regex=self.find_edit.flag_regex.isChecked(),
            selection_only=self.btn_selection_only.isChecked()
        )
        if one:
            self.replaceOneRequested.emit(req)
        else:
            self.replaceAllRequested.emit(req)

    def setStatus(self, text: str):
        self.lbl_find_result.setText(text)


# Demo usage
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = QMainWindow()
    bar = FindReplaceBar()
    w.setCentralWidget(bar)
    w.resize(600, 120)
    w.show()
    sys.exit(app.exec())






# # workspace/find_replace_bar.py
#
# from PySide6.QtCore    import Qt, Signal
# from dataclasses        import dataclass
# import re
# from workspace.button_symbols import ButtonSymbol
#
# from PySide6.QtWidgets import (
#     QGridLayout, QLineEdit, QToolButton, QPushButton,
#     QLabel, QSizePolicy,  QWidget,
# )
# from workspace.button_symbols import ButtonSymbol
#
#
# @dataclass
# class FindRequest:
#     pattern: str
#     replace_with: str
#     match_case: bool
#     word_boundary: bool
#     use_regex: bool
#     selection_only: bool
#
# class FindReplaceBar(QWidget):
#     # signals
#     findRequested         = Signal(object)   # FindRequest
#     replaceOneRequested   = Signal(object)
#     replaceAllRequested   = Signal(object)
#     jumpRequested         = Signal(int)      # +1 or -1
#     toggleSelectionOnly   = Signal(bool)
#     closeRequested        = Signal()
#
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self._build_ui()
#         self._connect_signals()
#         self._show_replace = True
#
#     def _build_ui(self):
#         grid = QGridLayout(self)
#         grid.setContentsMargins(2, 2, 2, 2)
#         grid.setHorizontalSpacing(4)
#         grid.setVerticalSpacing(2)
#
#         # ─── collapse/expand button in col 0, spans 2 rows ─────────
#         self.toggle_btn = QToolButton(text=ButtonSymbol.TOGGLE_COLLAPSE.symbol)
#         self.toggle_btn.setToolTip(ButtonSymbol.TOGGLE_COLLAPSE.tooltip)
#         self.toggle_btn.setFixedWidth(20)
#         self.toggle_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
#         grid.addWidget(self.toggle_btn, 0, 0, 2, 1)
#
#         # ─── Row 0: Find row ────────────────────────────────────────
#         self.find_edit = QLineEdit()
#         self.find_edit.setPlaceholderText("Find")
#         grid.addWidget(self.find_edit, 0, 1, 1, 4)  # span through col 4
#
#         self.btn_case = QToolButton(text=ButtonSymbol.MATCH_CASE.symbol)
#         self.btn_case.setCheckable(True)
#         self.btn_case.setToolTip(ButtonSymbol.MATCH_CASE.tooltip)
#         grid.addWidget(self.btn_case, 0, 5)
#
#         self.btn_word = QToolButton(text=ButtonSymbol.WORD_BOUNDARY.symbol)
#         self.btn_word.setCheckable(True)
#         self.btn_word.setToolTip(ButtonSymbol.WORD_BOUNDARY.tooltip)
#         grid.addWidget(self.btn_word, 0, 6)
#
#         self.btn_regex = QToolButton(text=ButtonSymbol.REGEX.symbol)
#         self.btn_regex.setCheckable(True)
#         self.btn_regex.setToolTip(ButtonSymbol.REGEX.tooltip)
#         grid.addWidget(self.btn_regex, 0, 7)
#
#         self.btn_prev = QToolButton(text=ButtonSymbol.PREV_RESULT.symbol)
#         self.btn_prev.setToolTip(ButtonSymbol.PREV_RESULT.tooltip)
#         grid.addWidget(self.btn_prev, 0, 8)
#
#         self.btn_next = QToolButton(text=ButtonSymbol.NEXT_RESULT.symbol)
#         self.btn_next.setToolTip(ButtonSymbol.NEXT_RESULT.tooltip)
#         grid.addWidget(self.btn_next, 0, 9)
#
#         self.btn_sel = QToolButton(text=ButtonSymbol.SELECTION_ONLY.symbol)
#         self.btn_sel.setCheckable(True)
#         self.btn_sel.setToolTip(ButtonSymbol.SELECTION_ONLY.tooltip)
#         grid.addWidget(self.btn_sel, 0, 10)
#
#         self.btn_close = QToolButton(text=ButtonSymbol.CLOSE.symbol)
#         self.btn_close.setToolTip(ButtonSymbol.CLOSE.tooltip)
#         grid.addWidget(self.btn_close, 0, 11)
#
#         # ─── Row 1: Replace row ─────────────────────────────────────
#         self.replace_edit = QLineEdit()
#         self.replace_edit.setPlaceholderText("Replace")
#         grid.addWidget(self.replace_edit, 1, 1, 1, 10)
#
#         self.btn_preserve = QToolButton(text=ButtonSymbol.PRESERVE_CASE.symbol)
#         self.btn_preserve.setCheckable(True)
#         self.btn_preserve.setToolTip(ButtonSymbol.PRESERVE_CASE.tooltip)
#         grid.addWidget(self.btn_preserve, 1, 5)
#
#         # Shrink these to emoji size:
#         btn_w = self.toggle_btn.width()
#         btn_h = self.find_edit.sizeHint().height()
#
#         self.btn_replace = QPushButton(ButtonSymbol.REPLACE_ONE.symbol)
#         self.btn_replace.setToolTip(ButtonSymbol.REPLACE_ONE.tooltip)
#         # self.btn_replace.setFixedSize(btn_w, btn_h)
#         grid.addWidget(self.btn_replace, 1, 6)
#
#         self.btn_replace_all = QPushButton(ButtonSymbol.REPLACE_ALL.symbol)
#         self.btn_replace_all.setToolTip(ButtonSymbol.REPLACE_ALL.tooltip)
#         # self.btn_replace_all.setFixedSize(btn_w, btn_h)
#         grid.addWidget(self.btn_replace_all, 1, 7)
#
#         # ─── Stretch so the edit fields expand ──────────────────────
#         grid.setColumnStretch(1, 2)
#
#     def _connect_signals(self):
#         # toggle replace row
#         self.toggle_btn.clicked.connect(self._on_toggle)
#         # close bar
#         self.btn_close.clicked.connect(lambda: self.closeRequested.emit())
#         # find on Enter
#         self.find_edit.returnPressed.connect(self._emit_find)
#         # next/prev
#         self.btn_next.clicked.connect(lambda: self.jumpRequested.emit(+1))
#         self.btn_prev.clicked.connect(lambda: self.jumpRequested.emit(-1))
#         # selection‐only toggle
#         self.btn_sel.toggled.connect(lambda on: self.toggleSelectionOnly.emit(on))
#         # replace actions
#         self.btn_replace.clicked.connect(lambda: self._emit_replace(one=True))
#         self.btn_replace_all.clicked.connect(lambda: self._emit_replace(one=False))
#
#     def _on_toggle(self):
#         self._show_replace = not self._show_replace
#         self.replace_edit.setVisible(self._show_replace)
#         self.btn_preserve.setVisible(self._show_replace)
#         self.btn_replace.setVisible(self._show_replace)
#         self.btn_replace_all.setVisible(self._show_replace)
#         self.toggle_btn.setText("▼" if self._show_replace else "▶")
#
#     def _current_request(self) -> FindRequest:
#         return FindRequest(
#             pattern=self.find_edit.text(),
#             replace_with=self.replace_edit.text(),
#             match_case=self.btn_case.isChecked(),
#             word_boundary=self.btn_word.isChecked(),
#             use_regex=self.btn_regex.isChecked(),
#             selection_only=self.btn_sel.isChecked()
#         )
#
#     def _emit_find(self):
#         req = self._current_request()
#         self.findRequested.emit(req)
#
#     def _emit_replace(self, one: bool):
#         req = self._current_request()
#         if one:
#             self.replaceOneRequested.emit(req)
#         else:
#             self.replaceAllRequested.emit(req)
#
#     # optional helper: update status text
#     def setStatus(self, text: str):
#         self.status_lbl.setText(text)
