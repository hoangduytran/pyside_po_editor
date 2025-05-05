from PySide6.QtWidgets import QTabBar
from PySide6.QtCore    import Qt

class LeftAlignedTabBar(QTabBar):
    def tabLayoutChange(self):
        # 1) Let Qt do its normal layout work first
        super().tabLayoutChange()

        # 2) Grab the internal layout
        bar_layout = self.layout()
        if bar_layout is None:
            # not installed yet – skip until next time
            return

        # 3) Zero out margins & spacing, then force left alignment
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setSpacing(0)
        bar_layout.setAlignment(Qt.AlignLeft)
