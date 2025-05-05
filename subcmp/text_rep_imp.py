# # -*- coding: utf-8 -*-
# from Foundation import NSUserDefaults
# from PySide6.QtWidgets import QTextEdit
# from PySide6.QtCore    import QSettings, Qt
# from PySide6.QtGui     import QTextCursor
#
# import gv  # for the ACCEPTABLE_KEYBOARD_KEYS_FOR_REPLACEMENT constant
# #
# # def load_system_replacements():
# #     """
# #     Return a dict { shortcut: replacement } from macOS System → Keyboard → Text
# #     """
# #     ud = NSUserDefaults.standardUserDefaults()
# #     domain = ud.persistentDomainForName_("NSGlobalDomain") or {}
# #     items = domain.get("NSUserDictionaryReplacementItems", [])
# #     mapping = {}
# #     for item in items:
# #         on  = item.get("replace")
# #         rep = item.get("with")
# #         if on and rep:
# #             mapping[on] = rep
# #     return mapping
#
# class ReplacementTextEdit(QTextEdit):
#     """
#     A QTextEdit that expands your macOS Text Replacements as you type.
#     """
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self._load_replacements()
#
#     def _load_replacements(self):
#         """
#         Load the list of {'replace','with'} dicts from QSettings
#         and build a mapping of shortcut -> replacement.
#         """
#         settings = QSettings("POEditor", "Replacements")
#         raw = settings.value("NSUserDictionaryReplacementItems", [])
#         self._replacements = {}
#         if isinstance(raw, (list, tuple)):
#             for entry in raw:
#                 key = entry.get("replace")
#                 val = entry.get("with")
#                 if key and val:
#                     self._replacements[key] = val
#
#     def keyPressEvent(self, ev):
#         # save cursor position before terminator is inserted
#         old_cursor = self.textCursor()
#         old_pos    = old_cursor.position()
#
#         # insert the key normally
#         super().keyPressEvent(ev)
#
#         # skip any key that isn't one of our terminating keys
#         is_by_passable = ev.key() not in gv.ACCEPTABLE_KEYBOARD_KEYS_FOR_REPLACEMENT
#         if is_by_passable:
#             return
#
#         # reset cursor to before the terminator
#         tc = self.textCursor()
#         tc.setPosition(old_pos)
#
#         # find word start/end
#         tc.movePosition(QTextCursor.StartOfWord, QTextCursor.MoveAnchor)
#         start = tc.position()
#         tc.setPosition(old_pos, QTextCursor.MoveAnchor)
#         tc.movePosition(QTextCursor.EndOfWord, QTextCursor.KeepAnchor)
#         end = tc.position()
#
#         # select the word
#         tc.setPosition(start)
#         tc.setPosition(end, QTextCursor.KeepAnchor)
#         word: str = tc.selectedText()
#         was_title = word.istitle()
#         if was_title:
#             word = word.lower()
#
#         # reload replacements in case they changed
#         self._load_replacements()
#
#         # if it matches, perform replacement
#         if word in self._replacements:
#             full: str = self._replacements[word]
#             if was_title:
#                 full = full.title()
#
#             tc.beginEditBlock()
#             tc.removeSelectedText()
#             tc.insertText(full + ev.text())
#             tc.endEditBlock()
#             self.setTextCursor(tc)

import gv
import re
from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QKeyEvent, QTextCursor
from .replacement_base import ReplacementBase

class ReplacementTextEdit(QTextEdit, ReplacementBase):
    def __init__(self, parent=None):
        QTextEdit.__init__(self, parent)
        ReplacementBase.__init__(self)
        self.setFont(gv.DEFAULT_LARGE_FONT)

    def _match_case(self, replacement: str, original: str) -> str:
        if original.isupper():      return replacement.upper()
        if original.islower():      return replacement.lower()
        if original.istitle():      return replacement.title()
        if original[0].isupper() and original[1:].islower(): return replacement.capitalize()
        return replacement

    def keyPressEvent(self, ev: QKeyEvent):
        """
        Overridden keyPressEvent to capture the key press and apply replacements.
        """
        # Skip any key that isn't one of our terminating keys (defined in gv.ACCEPTABLE_KEYBOARD_KEYS_FOR_REPLACEMENT)
        if not gv.is_acceptable_key_for_replacement(ev):
            # If the key isn't acceptable, return early without doing anything
            super().keyPressEvent(ev)
            return

        # Capture the cursor position before the key press
        tc = self.textCursor()
        old_pos = tc.position()

        # Call the parent keyPressEvent to insert the text normally
        super().keyPressEvent(ev)

        # After the key is inserted, get the new cursor position
        tc = self.textCursor()
        new_pos = tc.position()

        # Apply replacement logic if the key press is acceptable
        self.apply_replacement_logic(old_pos, new_pos)

    def apply_replacement_logic(self, old_cursor_pos, new_cursor_pos):
        """
        Handle the replacement logic, find the last word typed, and apply the replacement.
        """
        # Get the current text in the QTextEdit
        current_text = self.toPlainText()

        # Extract the 'prev_text' (text before the cursor) and 'next_text' (text after the cursor)
        prev_text = current_text[:old_cursor_pos]
        next_text = current_text[old_cursor_pos:]

        # Use a regex to find the last word in the 'prev_text' (word boundary logic)
        match = re.search(gv.WORD_BOUNDARY_RE, prev_text)
        if match:
            last_word = match.group(1)
            # Now search for the word in the database and apply the replacement
            updated_word = self.apply_replacement(last_word)
            is_replaced = (last_word != updated_word)
            if not is_replaced:
                return

            updated_word = self._match_case(updated_word, last_word)

            # Replace the last word in prev_text with the updated word
            prev_text = prev_text[:match.start()] + updated_word

            # Join the prev_text with next_text (the part typed after the last word)
            updated_text = prev_text + next_text

            # Set the updated text back to the QTextEdit
            self.setPlainText(updated_text)

            # Now place the cursor after the last character typed
            cursor_pos_after_replacement = old_cursor_pos + len(updated_word) - len(last_word) + 1
            self.set_cursor_position(cursor_pos_after_replacement)

    def set_cursor_position(self, position):
        """
        Set the cursor at the specified position.
        """
        tc = self.textCursor()
        tc.setPosition(position)
        self.setTextCursor(tc)


