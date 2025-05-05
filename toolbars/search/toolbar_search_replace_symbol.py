# toolbars/search/toolbar_search_replace_symbol.py

from enum import Enum

class ButtonSymbol(Enum):
    TOGGLE                    = ("▶",  "Show/Hide Replace")
    MATCH_CASE                = ("Aa", "Match case")
    WHOLE_WORD                = ("[a]", "Whole-word only")
    REGEX                     = (".*", "Use regular expressions")
    PRESERVE_CASE             = ("Æ", "Preserve case on replace")
    FIND                      = ("🔍", "Find action")
    FIND_RESULT               = ("No results", "Find result counts")
    PREV_FOUND                = ("↑",  "Go to previous match")
    NEXT_FOUND                = ("↓",  "Go to next match")
    MATCHED_WITHIN_SELECTION  = ("☰",  "Restrict search to selection")
    CLOSE                     = ("❌",  "Close find/replace panel")
    REPLACE_CURRENT           = ("♦", "Replace current match")
    REPLACE_ALL               = ("♻", "Replace all matches")
    # ── new buttons for main panel ───────────────────────────
    SEARCH_OPENED = ("⊞", "Search only in opened files")
    USE_SETTINGS = ("⚙", "Use excludes settings and ignore files")

    def __init__(self, sym: str, tip: str):
        self.symbol  = sym
        self.tooltip = tip
