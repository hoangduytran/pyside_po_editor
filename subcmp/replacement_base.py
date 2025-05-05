from PySide6.QtCore import QSettings

class ReplacementBase:
    def __init__(self):
        self._replacements = {}
        self._load_replacements()

    def _load_replacements(self):
        """
        Load the replacements from QSettings (or any other source you prefer).
        This method can be customized to load replacements from macOS, a file, or hardcoded.
        """
        settings = QSettings("POEditor", "Replacements")
        raw = settings.value("NSUserDictionaryReplacementItems", [])
        if isinstance(raw, (list, tuple)):
            for entry in raw:
                key = entry.get("replace")
                val = entry.get("with")
                if key and val:
                    self._replacements[key] = val
        sorted_by_key = dict(sorted(self._replacements.items()))
        self._replacements = sorted_by_key

    def apply_replacement(self, word):
        """
        Apply the replacement logic to a word.
        """
        orig_word = str(word)
        search_word = word.lower()
        # Check if the word matches any replacement
        if search_word in self._replacements:
            replacement = self._replacements.get(search_word)
            return replacement
        return word
