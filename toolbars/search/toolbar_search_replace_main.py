# toolbars/search/toolbar_search_replace_main.py

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout
)
from PySide6.QtCore    import (
    Qt, QEvent,
)

from .toolbar_search_replace_symbol   import ButtonSymbol
from .toolbar_search_replace_settings import load_include_exclude, save_include_exclude
from .toolbar_search_replace_widget   import ToggleFindReplace
from .toolbar_search_replace_flag_line_edit import FlagLineEdit
from gv import main_gv

class FindReplaceMain(QWidget):
    """
    Top: ToggleFindReplace (find/replace + flags)
    Bottom: two FlagLineEdits for 'Files to include' and 'Files to exclude'
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # ─── Top: existing find/replace widget ──────────────────
        self.toggle_widget = ToggleFindReplace(self)

        # ─── Bottom: include/exclude lines ──────────────────────
        inc, exc = load_include_exclude()
        self.include_edit = FlagLineEdit([ButtonSymbol.USE_SETTINGS], self)
        self.include_edit.setPlaceholderText("files to include")
        self.include_edit.setText(",".join(main_gv.include_flag_list or inc))

        self.exclude_edit = FlagLineEdit([ButtonSymbol.SEARCH_OPENED], self)
        self.exclude_edit.setPlaceholderText("files to exclude")
        self.exclude_edit.setText(",".join(main_gv.exclude_flag_list or exc))

        # Alt+Up/Down bindings to cycle history
        self._bind_history(self.include_edit,  "include_flag_list")
        self._bind_history(self.exclude_edit,  "exclude_flag_list")
        self._bind_history(self.toggle_widget.find_edit,    "find_pattern_list")
        self._bind_history(self.toggle_widget.replace_edit, "replace_pattern_list")

        # Bottom fields already exist as self.include_edit, self.exclude_edit
        self.include_edit.returnPressed.connect(self._on_include_enter)
        self.exclude_edit.returnPressed.connect(self._on_exclude_enter)

        bottom = QWidget(self)
        h = QVBoxLayout(bottom)
        h.setContentsMargins(0,0,0,0)
        h.setSpacing(4)
        h.addWidget(self.include_edit)
        h.addWidget(self.exclude_edit)

        # ─── Layout ─────────────────────────────────────────────
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0,0,0,0)
        main_lay.setSpacing(6)
        main_lay.addWidget(self.toggle_widget)
        main_lay.addWidget(bottom)

        # save initial include/exclude back to gv
        main_gv.include_flag_list = self.include_edit.text().split(",")
        main_gv.exclude_flag_list = self.exclude_edit.text().split(",")

        # when user edits include/exclude, write back to QSettings immediately
        self.include_edit.editingFinished.connect(self._save_include)
        self.exclude_edit.editingFinished.connect(self._save_exclude)

    def _on_include_enter(self):
        val = self.include_edit.text().strip()
        if not val:
            return
        hist = main_gv.include_flag_list or []
        if val not in hist:
            hist.append(val)
            main_gv.include_flag_list = hist
            # persist to QSettings
            from .toolbar_search_replace_settings import save_include_exclude, load_include_exclude
            _, exc = load_include_exclude()
            save_include_exclude(hist, exc)

    def _on_exclude_enter(self):
        val = self.exclude_edit.text().strip()
        if not val:
            return
        hist = main_gv.exclude_flag_list or []
        if val not in hist:
            hist.append(val)
            main_gv.exclude_flag_list = hist
            from .toolbar_search_replace_settings import save_include_exclude, load_include_exclude
            inc, _ = load_include_exclude()
            save_include_exclude(inc, hist)

    def _bind_history(self, line_edit, gv_attr):
        """
        Bind Alt+Up/Down to cycle through the list stored in main_gv.<gv_attr>.
        """
        def step(delta):
            history = getattr(main_gv, gv_attr) or []
            if not history:
                return
            try:
                idx = history.index(line_edit.text())
            except ValueError:
                idx = -1
            idx = (idx + delta) % len(history)
            line_edit.setText(history[idx])

        le = line_edit
        le.installEventFilter(self)
        # store per-widget handlers
        setattr(self, f"_{gv_attr}_step", step)

    def eventFilter(self, obj, event):
        # catch Alt+Up / Alt+Down
        if event.type() == QEvent.KeyPress:
            if event.modifiers() == Qt.AltModifier:
                if event.key() == Qt.Key_Up:
                    for attr in ("include_flag_list",
                                 "exclude_flag_list",
                                 "find_pattern_list",
                                 "replace_pattern_list"):
                        if obj is getattr(self, attr.replace("_list","") + "_edit", None):
                            getattr(self, f"_{attr}_step")(-1)
                            return True
                if event.key() == Qt.Key_Down:
                    for attr in ("include_flag_list",
                                 "exclude_flag_list",
                                 "find_pattern_list",
                                 "replace_pattern_list"):
                        if obj is getattr(self, attr.replace("_list","") + "_edit", None):
                            getattr(self, f"_{attr}_step")(+1)
                            return True
        return super().eventFilter(obj, event)

    def _save_include(self):
        inc = [p.strip() for p in self.include_edit.text().split(",") if p.strip()]
        main_gv.include_flag_list = inc
        _, exc = load_include_exclude()
        save_include_exclude(inc, exc)

    def _save_exclude(self):
        _, exc = load_include_exclude()
        ex = [p.strip() for p in self.exclude_edit.text().split(",") if p.strip()]
        main_gv.exclude_flag_list = ex
        save_include_exclude(*load_include_exclude(), exclude_list=ex)
