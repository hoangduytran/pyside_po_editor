# toolbars/search/toolbar_search_replace_flag_line_edit.py

from PySide6.QtWidgets import (
    QLineEdit,
    QToolButton,
    QWidgetAction,
    QSizePolicy
)
from PySide6.QtCore    import QSize
from .toolbar_search_replace_icon   import icon_from_text
from .toolbar_search_replace_symbol import ButtonSymbol

class FlagLineEdit(QLineEdit):
    """
    A QLineEdit with trailing checkable buttons defined by ButtonSymbol,
    embedded inside the line-edit via QWidgetAction.
    """
    def __init__(self, symbols: list[ButtonSymbol], *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Keep height reasonable and allow horizontal expansion
        self.setMinimumHeight(28)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Embed each initial symbol as a trailing action
        for sym in symbols:
            btn = self.add_flag(sym)
            setattr(self, f"flag_{sym.name.lower()}", btn)

    def add_flag(self, sym: ButtonSymbol) -> QToolButton:
        """
        Create a QToolButton for 'sym', wrap it in a QWidgetAction,
        add it as a trailing action on this QLineEdit, and return the button.
        """
        btn = QToolButton(self)
        btn.setIcon(icon_from_text(sym.symbol))
        btn.setIconSize(QSize(20, 20))
        btn.setToolTip(sym.tooltip)
        btn.setCheckable(True)

        action = QWidgetAction(self)
        action.setDefaultWidget(btn)
        # Place the action inside the QLineEdit on the right
        self.addAction(action, QLineEdit.TrailingPosition)

        # **install** the attribute so you can later do self.flag_<name>
        setattr(self, f"flag_{sym.name.lower()}", btn)
        return btn
