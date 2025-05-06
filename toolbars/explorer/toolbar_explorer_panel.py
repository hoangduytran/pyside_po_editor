# toolbars/explorer/toolbar_explorer_panel.py

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QToolButton,
    QFileDialog, QTreeView, QSizePolicy, QFileSystemModel, QHeaderView
)
from PySide6.QtCore    import Qt, QDir, QSettings

from gv import main_gv  # your global vars holder

class ExplorerPanel(QWidget):
    """
    Explorer panel with:
     - A path entry field + browse button on top
     - A QTreeView below to show the directory contents
    """

    def __init__(self, on_open_path_callback, parent=None):
        super().__init__(parent)
        self.on_open_path = on_open_path_callback

        # ── Top row: path editor + browse button ───────────────
        self.path_edit = QLineEdit(self)
        self.path_edit.setPlaceholderText("Enter directory (e.g. $HOME/projects)...")
        self.path_edit.returnPressed.connect(self._apply_path)
        self.path_edit.editingFinished.connect(self._apply_path)

        self.browse_btn = QToolButton(self)
        self.browse_btn.setText("📁")
        self.browse_btn.setToolTip("Browse for folder")
        self.browse_btn.clicked.connect(self._on_browse)

        top = QWidget(self)
        top_l = QHBoxLayout(top)
        top_l.setContentsMargins(0, 0, 0, 0)
        top_l.setSpacing(4)
        top_l.addWidget(self.path_edit)
        top_l.addWidget(self.browse_btn)

        # ── Bottom: file-system view ────────────────────────────
        self.fs_model = QFileSystemModel(self)
        self.fs_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.AllDirs)

        self.view = QTreeView(self)
        self.view.setModel(self.fs_model)
        self.view.setHeaderHidden(False)
        self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.view.doubleClicked.connect(self._on_double_click)

        from PySide6.QtWidgets import QHeaderView
        header = self.view.header()
        # allow manual dragging:
        header.setSectionResizeMode(QHeaderView.Interactive)
        # but size each section to fit its contents right now:
        # **new**: re-fit *all* columns as soon as the directory is loaded
        self.fs_model.directoryLoaded.connect(self._on_dir_loaded)

        self.view.setSortingEnabled(True)
        self.view.sortByColumn(0, Qt.AscendingOrder)

        # ── Assemble layout ─────────────────────────────────────
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        lay.addWidget(top, 0)
        lay.addWidget(self.view, 1)

        # ── Initialize to last‐used dir or HOME ─────────────────
        settings = QSettings("com.poeditor", "POEditor")
        last = settings.value("lastDirectory", QDir.homePath())
        self._set_directory(last)
        # allow this panel to grow & shrink in the splitter
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _on_dir_loaded(self, loaded_path: str):
        # only re-size if it's the directory we care about
        # (optional check: if loaded_path != main_gv.current_dir: return)
        header = self.view.header()
        header.resizeSections(QHeaderView.ResizeToContents)

    # def resizeEvent(self, event):
    #     super().resizeEvent(event)
    #     self._equalize_columns()
    #
    # def _equalize_columns(self):
    #     header = self.view.header()
    #     total_width = self.view.viewport().width()
    #     count = header.count()
    #     if count:
    #         per_col = total_width // count
    #         for i in range(count):
    #             header.resizeSection(i, per_col)

    def _apply_path(self):
        text = self.path_edit.text().strip()
        if not text:
            return
        path = os.path.expanduser(os.path.expandvars(text))
        if os.path.isdir(path):
            self._set_directory(path)

    def _on_browse(self):
        start = main_gv.current_dir or QDir.homePath()
        chosen = QFileDialog.getExistingDirectory(
            self, "Select Directory", start, QFileDialog.ShowDirsOnly
        )
        if chosen:
            self._set_directory(chosen)

    def _set_directory(self, path: str):
        # 1) Update path field
        self.path_edit.setText(path)
        # 2) Update tree view root
        idx = self.fs_model.setRootPath(path)
        self.view.setRootIndex(idx)
        # 3) Update global and settings
        main_gv.current_dir = path
        QSettings("com.poeditor", "POEditor").setValue("lastDirectory", path)
        # **DO NOT** call on_open_path here any more.

    def _on_double_click(self, idx):
        path = self.fs_model.filePath(idx)
        if os.path.isdir(path):
            self._set_directory(path)
        else:
            # 1) remember the file
            main_gv.current_file = path
            QSettings("com.poeditor", "POEditor").setValue("lastFile", path)
            # 2) open it via your callback
            self.on_open_path(path)
