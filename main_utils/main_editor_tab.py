# main_utils/main_editor_tab.py

class EditorTab:
    """Wraps an editor widget and its source path."""
    def __init__(self, widget, path):
        self.widget = widget
        self.path   = path
