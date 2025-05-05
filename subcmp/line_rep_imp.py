import gv
import re
from PySide6.QtWidgets import QLineEdit
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import Qt
from .replacement_base import ReplacementBase

class ReplacementLineEdit(QLineEdit, ReplacementBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        ReplacementBase.__init__(self)  # Initialize ReplacementBase

    def keyPressEvent(self, ev: QKeyEvent):
        """
        Overridden keyPressEvent to capture the key press and apply replacements.
        """
        # First, check if the key is acceptable for replacement using the new method from gv
        if not gv.is_acceptable_key_for_replacement(ev):
            # If the key isn't in the acceptable pattern, return early and let the normal event handle it
            super().keyPressEvent(ev)
            return

        # Save the old cursor position before performing any action
        old_cursor_pos = self.cursorPosition()

        # Call the parent keyPressEvent to insert the text normally
        super().keyPressEvent(ev)

        # Recalculate the cursor position after the text insertion
        new_cursor_pos = self.cursorPosition()

        # Apply replacements based on the key press (e.g., for shortcuts like Ctrl+R)
        self.apply_replacement_in_text(old_cursor_pos, new_cursor_pos)

        # Reposition the cursor after replacement (restore position if needed)
        self.setCursorPosition(new_cursor_pos)

    def apply_replacement_logic(self, old_cursor_pos, new_cursor_pos):
        """
        Handle the replacement logic, find the last word typed, and apply the replacement.
        """
        # Get the current text in the QLineEdit
        current_text = self.text()

        # Extract the 'prev_text' (text before the cursor) and 'next_text' (text after the cursor)
        prev_text = current_text[:old_cursor_pos]
        next_text = current_text[old_cursor_pos:]

        # Use a regex to find the last word in the 'prev_text' (word boundary logic)
        match = re.search(gv.WORD_BOUNDARY_PAT, prev_text)
        if match:
            last_word = match.group(1)
            # Now search for the word in the database and apply the replacement
            updated_word = self.apply_replacement(last_word)
            is_replaced = (last_word != updated_word)
            if not is_replaced:
                return

            # Replace the last word in prev_text with the updated word
            prev_text = prev_text[:match.start()] + updated_word

            # Join the prev_text with next_text (the part typed after the last word)
            updated_text = prev_text + next_text

            # Set the updated text back to the QLineEdit
            self.setText(updated_text)

            # Now place the cursor after the last character typed
            cursor_pos_after_replacement = old_cursor_pos + len(updated_word) - len(last_word) + 1
            self.set_cursor_position(cursor_pos_after_replacement)

    def set_cursor_position(self, position):
        """
        Set the cursor at the specified position.
        """
        cursor = self.textCursor()
        cursor.setPosition(position)
        self.setTextCursor(cursor)
