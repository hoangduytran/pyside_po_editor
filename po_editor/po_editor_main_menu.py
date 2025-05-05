# po_editor/po_editor_main_menu.py

from PySide6.QtWidgets import QMenuBar
from PySide6.QtGui     import QKeySequence, QAction
from PySide6.QtCore    import Qt, QSettings

from gv import MAIN_GUI_ACTION_SPECS, main_gv
from po_editor.po_editor_main_actions import get_actions

class POEditorMainMenu:
    """
    Encapsulates File/Edit/View/... menu creation for the POEditor.
    """

    def __init__(self, parent_window):
        self.window = parent_window
        self.qactions = {}
        self._create_actions()
        self._create_menu_bar()
        self._connect_actions()

    def _create_actions(self):
        for menu_name, items in MAIN_GUI_ACTION_SPECS:
            for item in items:
                if item[0] == 'sep':
                    continue
                if isinstance(item[1], list):
                    for sub in item[1]:
                        key, text, _ = sub
                        self.qactions[key] = QAction(text, self.window)
                else:
                    key, text, _ = item
                    self.qactions[key] = QAction(text, self.window)

    def _create_menu_bar(self):
        menubar = QMenuBar(self.window)
        self.window.setMenuBar(menubar)

        # top-level menus
        menus = {}
        for name, _ in MAIN_GUI_ACTION_SPECS:
            menus[name] = menubar.addMenu(name)

        # populate actions & submenus
        for name, items in MAIN_GUI_ACTION_SPECS:
            menu = menus[name]
            for item in items:
                if item[0] == 'sep':
                    menu.addSeparator()
                elif isinstance(item[1], list):
                    submenu = menu.addMenu(item[0])
                    for sub in item[1]:
                        key = sub[0]
                        submenu.addAction(self.qactions[key])
                else:
                    key = item[0]
                    menu.addAction(self.qactions[key])

    def _connect_actions(self):
        acts = get_actions(main_gv)
        # wire each QAction to its callback
        for key, action in self.qactions.items():
            # find the callback name
            callback_name = None
            for menu, items in MAIN_GUI_ACTION_SPECS:
                for it in items:
                    if isinstance(it[1], list):
                        for sub in it[1]:
                            if sub[0] == key:
                                callback_name = sub[2]
                    elif it[0] == key:
                        callback_name = it[2]
            if callback_name == 'close':
                action.triggered.connect(self.window.close)
            elif callback_name in acts:
                action.triggered.connect(acts[callback_name])

        # load and apply any custom shortcuts
        settings = QSettings("POEditor", "Settings")
        for key, action in self.qactions.items():
            seq = settings.value(f"shortcut/{key}")
            if seq:
                action.setShortcut(QKeySequence(seq))
                action.setShortcutContext(Qt.WidgetWithChildrenShortcut)
