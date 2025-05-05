# toolbars/search/toolbar_search_replace_settings.py

from PySide6.QtCore import QSettings

ORGANIZATION = "com.poeditor"
APPLICATION  = "Settings"

DEFAULT_INCLUDE = ["*.po"]
DEFAULT_EXCLUDE = ["*.png", "*.jpg", "*.bin", ".*"]  # binaries, images, dot-files

def load_include_exclude():
    """
    Returns (include_list, exclude_list), reading from QSettings or creating defaults.
    """
    settings = QSettings(QSettings.NativeFormat, QSettings.UserScope,
                         ORGANIZATION, APPLICATION)
    inc = settings.value("fileInclude")
    exc = settings.value("fileExclude")
    # if missing or not list, initialize them
    changed = False
    if not isinstance(inc, list):
        inc = DEFAULT_INCLUDE
        settings.setValue("fileInclude", inc)
        changed = True
    if not isinstance(exc, list):
        exc = DEFAULT_EXCLUDE
        settings.setValue("fileExclude", exc)
        changed = True
    if changed:
        settings.sync()
    return inc, exc

def save_include_exclude(include_list, exclude_list):
    settings = QSettings(QSettings.NativeFormat, QSettings.UserScope,
                         ORGANIZATION, APPLICATION)
    settings.setValue("fileInclude", include_list)
    settings.setValue("fileExclude", exclude_list)
    settings.sync()
