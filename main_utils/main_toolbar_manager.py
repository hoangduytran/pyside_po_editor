# main_utils/main_toolbar_manager.py

from PySide6.QtWidgets import QPushButton, QVBoxLayout
from main_utils.main_button_enum import ButtonEnum

class ToolbarManager:
    def __init__(self, parent, button_bar, panel_stack):
        self.parent      = parent
        self.button_bar  = button_bar
        self.panel_stack = panel_stack
        self.buttons     = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self.button_bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        for idx, btn_enum in enumerate(ButtonEnum):
            btn = QPushButton(btn_enum.icon)
            btn.setCheckable(True)
            btn.setFixedSize(40, 40)
            btn.setToolTip(btn_enum.tooltip)
            btn.setStyleSheet(
                "background-color: transparent; "
                "color: white; border: none; font-size: 18px;"
            )
            btn.clicked.connect(lambda checked, i=idx: self.parent.toggle_panel(i))
            layout.addWidget(btn)
            self.buttons.append(btn)

        layout.addStretch()
