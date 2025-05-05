import os
import sys
import re
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

from .replacement_engine import ReplacementEngine, ReplacementRecord

# Define a cross-platform settings key
SETTINGS_KEY = "TextReplacements"


def _default_export_target():
    """
    Determine default export format and path based on OS.
    """
    user = os.path.expanduser('~')
    system = sys.platform
    if system == 'darwin':
        return 'plist', os.path.join(user, 'Library/Preferences/com.apple.TextReplacement.plist')
    elif system.startswith('win'):
        # AutoHotkey script
        return 'ahk', os.path.join(user, 'text_replacements.ahk')
    else:
        # Assume Linux: Bamboo macro
        conf = os.path.join(user, '.config/ibus-bamboo')
        os.makedirs(conf, exist_ok=True)
        return 'macro', os.path.join(conf, 'ibus-bamboo.macro.text')


class ReplacementActions:
    def __init__(self, dialog):
        self.dialog = dialog
        self.matches = []
        self.match_index = -1

    @staticmethod
    def import_file(dialog, path):
        """
        Generic import: detect format by extension, load into internal store.
        """
        fmt = os.path.splitext(path)[1].lstrip('.')
        try:
            records = ReplacementEngine.import_file(fmt, path)
            # Store into QSettings under SETTINGS_KEY
            dialog.settings.setValue(
                SETTINGS_KEY,
                [r.to_dict() for r in records]
            )
            dialog._replacement_refresh_table()
        except Exception as e:
            print(f"Failed to import '{path}' as {fmt}: {e}")

    @staticmethod
    def clear_search(dialog):
        dialog.search_field.clear()

    @staticmethod
    def export_current(dialog, out_path=None, fmt=None):
        """
        Export current entries to system-specific default or given file.
        """
        raw = dialog.settings.value(SETTINGS_KEY) or []
        records = [ReplacementRecord.from_dict(item) for item in raw]

        if not fmt and not out_path:
            fmt, out_path = _default_export_target()
        elif fmt and not out_path:
            ext = fmt
            out_path = os.path.join(os.getcwd(), f"replacements_export.{ext}")
        elif out_path and not fmt:
            fmt = os.path.splitext(out_path)[1].lstrip('.')

        try:
            ReplacementEngine.export_file(fmt, records, out_path)
            print(f"Exported {len(records)} entries to {out_path} (format: {fmt})")
        except Exception as e:
            print(f"Failed to export replacements: {e}")

    @staticmethod
    def save_edit(dialog):
        raw = dialog.settings.value(SETTINGS_KEY) or []
        idx = getattr(dialog, 'current_edit_row', None)
        if isinstance(idx, int) and 0 <= idx < len(raw):
            raw[idx]['replace'] = dialog.edit_shortcut.text()
            raw[idx]['with'] = dialog.edit_replacement.text()
            dialog.settings.setValue(
                SETTINGS_KEY, raw
            )
            dialog._replacement_refresh_table()
        dialog.editor_panel.hide()

    @staticmethod
    def delete_selected(dialog):
        selected = dialog.table.selectionModel().selectedRows()
        if not selected:
            return
        indices = sorted(r.row() for r in selected)
        raw = dialog.settings.value(SETTINGS_KEY) or []
        for idx in reversed(indices):
            if 0 <= idx < len(raw):
                raw.pop(idx)
        dialog.settings.setValue(
            SETTINGS_KEY, raw
        )
        dialog._replacement_refresh_table()

    def on_search_text_changed(self,
                               text: str,
                               scope: str = "both",
                               match_case: bool = False,
                               boundary: bool = False,
                               regex: bool = False):
        """Search with optional case-sensitivity, whole-word, or regex."""
        self.matches.clear()
        self.match_index = -1
        self._update_buttons_state()

        search_text = text.strip().lower()
        if not search_text:
            return

        # choose how to match
        def match_cell(cell: str) -> bool:
            hay = cell if match_case else cell.lower()
            pat = text if match_case else text.lower()

            if regex:
                try:
                    return bool(re.search(pat, hay))
                except re.error:
                    return False
            elif boundary:
                # simple whole‐word: pad and look for “ pat ”
                words = hay.split()
                return pat in words
            else:
                return pat in hay

        n_rows = self.dialog.table.rowCount()
        if scope == "shortcut":
            cols = [0]
        elif scope == "replacement":
            cols = [1]
        else:  # both
            cols = [0, 1]

        # scan in order
        seen = set()
        for col in cols:
            for row in range(n_rows):
                if row in seen:
                    continue
                cell = self.dialog.table.item(row, col).text()
                if match_cell(cell):
                    self.matches.append(row)
                    seen.add(row)

        self._update_buttons_state()

    def on_find(self):
        if self.matches:
            self.match_index = 0
            self._highlight_match()

    def on_prev_match(self):
        if self.match_index > 0:
            self.match_index -= 1
            self._highlight_match()

    def on_next_match(self):
        if self.match_index < len(self.matches) - 1:
            self.match_index += 1
            self._highlight_match()

    def _highlight_match(self):
        for row in range(self.dialog.table.rowCount()):
            self.dialog.table.item(row, 0).setBackground(Qt.white)
            self.dialog.table.item(row, 1).setBackground(Qt.white)
        if 0 <= self.match_index < len(self.matches):
            row = self.matches[self.match_index]
            self.dialog.table.item(row, 0).setBackground(QColor(255, 255, 0))
            self.dialog.table.item(row, 1).setBackground(QColor(255, 255, 0))
            self.dialog.table.scrollToItem(
                self.dialog.table.item(row, 0)
            )

    def _update_buttons_state(self):
        has_text = bool(self.dialog.search_field.text().strip())
        self.dialog.find_btn.setEnabled(has_text)
        has_match = bool(self.matches)
        self.dialog.prev_btn.setEnabled(has_match)
        self.dialog.next_btn.setEnabled(has_match)

    @staticmethod
    def on_add(dialog, shortcut, replacement):
        raw = dialog.settings.value(SETTINGS_KEY) or []
        raw.append({"replace": shortcut, "with": replacement})
        dialog.settings.setValue(
            SETTINGS_KEY, raw
        )
        dialog._replacement_refresh_table()

    @staticmethod
    def on_delete(dialog, shortcut, replacement):
        raw = dialog.settings.value(SETTINGS_KEY) or []
        new_raw = [e for e in raw if not (e.get('replace') == shortcut and e.get('with') == replacement)]
        dialog.settings.setValue(
            SETTINGS_KEY, new_raw
        )
        dialog._replacement_refresh_table()
