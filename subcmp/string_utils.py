import difflib
import re

def _normalize(text: str) -> str:
    """
    Lower-case, strip and collapse all whitespace to single spaces.
    """
    return re.sub(r'\s+', ' ', text.strip().lower())

def is_virtually_same(translation: str, threshold: float = 0.85) -> bool:
    """
    Return True if `translation` is “close enough” to any existing version.
    Uses a SequenceMatcher ratio >= threshold.
    """
    t_norm = self._normalize(translation)
    for _, existing in self.msgstr_versions:
        if difflib.SequenceMatcher(None, t_norm, self._normalize(existing)).ratio() >= threshold:
            return True
    return False

def add_version_fuzzy(self, translation: str, threshold: float = 0.85) -> bool:
    """
    Like add_version_mem, but only adds if not virtually the same
    as an existing version. Returns True if added, False otherwise.
    """
    if self.is_virtually_same(translation, threshold):
        return False
    # otherwise append with next sequence number
    next_ver = len(self.msgstr_versions) + 1
    self.msgstr_versions.append((next_ver, translation))
    return True