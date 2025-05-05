# main_utils/collapsible_section.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolButton
from PySide6.QtCore    import Qt

class CollapsibleSection(QWidget):
    def __init__(self, title: str, content: QWidget, parent=None):
        super().__init__(parent)
        self.content = content

        # 1) Header: a QToolButton with both arrow and text
        self.header_btn = QToolButton(self)
        self.header_btn.setText(title)
        self.header_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.header_btn.setArrowType(Qt.RightArrow)               # ← starts closed
        self.header_btn.setCheckable(True)
        self.header_btn.setChecked(False)

        # 2) Main layout
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0)
        lay.setSpacing(0)
        lay.addWidget(self.header_btn)
        lay.addWidget(self.content)

        # 3) Start closed
        self.content.setVisible(False)

        # 4) Toggle arrow + content
        self.header_btn.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked: bool):
        # flip the arrow
        self.header_btn.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
        # show/hide the content
        self.content.setVisible(checked)
