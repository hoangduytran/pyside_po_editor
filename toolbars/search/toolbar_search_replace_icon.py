# toolbars/search/toolbar_search_replace_icon.py

from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import Qt, QSize

def icon_from_text(txt: str, size: int = 18) -> QIcon:
    """
    Render a text symbol into a QIcon of the given size.
    """
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
    icon = QIcon(pix)
    return icon
