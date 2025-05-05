#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module: resources.py
Contains emoji and color constants for useEMOJI_OPEN_FILE throughout the application.
"""
from enum import Enum
import tkinter as tk

class Emojis(Enum):
    # Emoji Constants
    EMOJI_OPEN_FILE1 = "📂1"
    EMOJI_OPEN_FILE2 = "📂2"
    EMOJI_ARROW_RIGHT_TO_LEFT = "⬅️"
    EMOJI_ARROW_LEFT_TO_RIGHT = "➡️"
    EMOJI_ARROW_ALL_LEFT_TO_RIGHT = "⏩"
    EMOJI_ARROW_ALL_RIGHT_TO_LEFT = "⏪"
    EMOJI_JUMP_TO_BEGIN = "⏮"
    EMOJI_JUMP_TO_END = "⏭"
    EMOJI_RESTORE_FROM_DB = "🔄"
    EMOJI_SAVE = "💾"
    EMOJI_CLEAR = "🧹"
    EMOJI_FONT_PLUS = "🔠"
    EMOJI_FONT_MINUS = "🔡"
    EMOJI_PREV_PAGE = "⬆️"
    EMOJI_NEXT_PAGE = "⬇️"
    EMOJI_MERGE = "🔀"
    EMOJI_EXIT = "❌"
    EMOJI_FILE1 = "📄"
    EMOJI_FILE2 = "📄"
    EMOJI_EDIT = "✏️"
    EMOJI_FINISH = "✅"
    EMOJI_UNDO = "↩️"
    EMOJI_REDO = "↪️"
    EMOJI_SORT_ORDER = "🔃"
    EMOJI_SORT_BY = "⇅"

    # Color Constants
    COLOR_TOOLTIP_BG = "#ffffe0"         # Tooltip background color
    COLOR_TOOLBAR_BG = "#f0f0f0"           # Toolbar background
    COLOR_HILIGHT_BG = "#FFF59D"              # highlighting background
    COLOR_DETAIL_HILIGHT_BG = "#FFC0CB"
    COLOR_MARKER_CANVAS_BG = "white"       # Marker canvas background

def get_emoji_size(emoji_text, font_family="Arial", font_size=12):
    """
    Return (width, height) in pixels for the given emoji_text using the given font.
    We create a hidden Tk root and Label, measure the label, then destroy the root.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the po_cmp_main window
    label = tk.Label(root, text=emoji_text, font=(font_family, font_size))
    label.pack()
    root.update_idletasks()
    width = label.winfo_width()
    height = label.winfo_height()
    root.destroy()
    return (width, height)

class SortOption(Enum):
    LINE_NUMBER = "🔢 Line number"
    MSGID = "🆔 Msgid"
    MSGSTR = "💬 Msgstr"
    HASH_VALUE = "🔑 Hash value"
    DIFFERENCE = "⚖️ Difference"
    NON_TRANSLATED = "🌐 Non Translated"
    FUZZY = "❓ Fuzzy"

    @classmethod
    def from_value(cls, value: str):
        """Convert a string value to the corresponding SortOption enum member."""
        return next((option for option in cls if option.value == value), None)

    def sort_key(self, diff):
        """
        Return a composite sorting key for a given diff.
        The primary key is based on the selected sort option.
        The secondary key is the line number (0 if None).
        """
        # Compute a secondary key from lineno.
        try:
            lineno = int(diff[1].lineno) if diff[1].lineno not in [None, ""] else 0
        except Exception:
            lineno = 0

        if self == SortOption.LINE_NUMBER:
            # For line number sorting, use lineno as the primary key.
            return (lineno, 0)
        elif self == SortOption.MSGID:
            msgid = diff[1].id
            if isinstance(msgid, (list, tuple)):
                primary = " ".join(str(x) for x in msgid)
            else:
                primary = str(msgid)
            return (primary, lineno)
        elif self == SortOption.MSGSTR:
            msgstr = diff[1].string
            if isinstance(msgstr, (list, tuple)):
                primary = " ".join(str(x) for x in msgstr)
            else:
                primary = str(msgstr)
            return (primary, lineno)
        elif self == SortOption.HASH_VALUE:
            primary = diff[1].hash_key
            return (primary, lineno)
        elif self == SortOption.DIFFERENCE:
            primary = 0 if diff[3] else 1
            return (primary, lineno)
        elif self == SortOption.NON_TRANSLATED:
            # Non-translated messages have an empty string.
            primary = 0 if len(diff[1].string.strip()) == 0 else 1
            return (primary, lineno)
        elif self == SortOption.FUZZY:
            primary = 0 if diff[1].fuzzy else 1
            return (primary, lineno)
        else:
            return (0, lineno)

class SortOrder(Enum):
    ASCENDING = "🔼 Ascending"
    DESCENDING = "🔽 Descending"

    @classmethod
    def from_value(cls, value: str):
        """Convert a string value to the corresponding SortOrder enum member."""
        return next((order for order in cls if order.value == value), None)

    @classmethod
    def from_value(cls, value):
        """Return the enum member matching the given value, or None if not found."""
        return next((order for order in cls if order.value == value), None)

