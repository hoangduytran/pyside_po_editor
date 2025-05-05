# workspace/button_symbols.py

from enum import Enum

class ButtonSymbol(Enum):
    TOGGLE                    = ("▶",  "Show/Hide Replace")
    MATCH_CASE                = ("Aa", "Match case")
    WORD_BOUNDARY             = ("[a]", "Whole-word only")
    REGEX                     = (".*", "Use regular expressions")
    PRESERVE_CASE             = ("Æ", "Preserve case on replace")
    FIND                      = ("🔍", "Find action")
    FIND_RESULT               = ("No results", "Find result counts")
    PREV_FOUND                = ("↑",  "Go to previous match")
    NEXT_FOUND                = ("↓",  "Go to next match")
    SELECTION_ONLY            = ("☰",  "Restrict search to selection")
    CLOSE                     = ("❌",  "Close find/replace panel")
    # REPLACE_CURRENT           = ("🔄", "Replace current match")
    # REPLACE_ALL               = ("🔁", "Replace all matches")
    REPLACE_CURRENT           = ("♦", "Replace current match")  # single-cycle arrow
    REPLACE_ALL               = ("♻", "Replace all matches")

    def __init__(self, sym, tip):
        self.symbol  = sym
        self.tooltip = tip