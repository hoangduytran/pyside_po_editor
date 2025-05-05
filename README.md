# PySide6 PO Editor IDE

A VS Code–inspired graphical editor for gettext `.po` files, built with PySide6.  
Features include:

- **Multi-tab editing**: each file in its own tab  
- **Built-in file-explorer** and **workspace** panels  
- **Fast search** (CLI & integrated) with literal/regex, context, progress bar  
- **Find & replace bar** with flags (case, whole-word, regex, preserve-case)  
- **Version history** for translations, powered by a local DB  
- **Preferences** (fonts, translation backends, etc.) saved via QSettings  
- **MRU (most-recently-used)** file list and auto-reopen on startup  
- **Extensible architecture**: `main_utils/`, `po_editor/`, `workspace/`, `search/` modules  

---

## `main.py`

This is the application entry‐point. On launch it:

1. Initializes a `QApplication` and loads the Qt stylesheet from `rs/styles.css`.  
2. Instantiates `MainWindow` (in `main.py`), which builds:
   - The **left toolbar** (buttons → panels)  
   - The **side panels** (`ExplorerPanel`, `FindReplaceMain`, etc.)  
   - The **central** tab widget for `POEditorWidget` instances  
   - The **menu bar** (`POEditorMainMenu`) and **status bar**  
3. Hooks up the “Open…” action to the multi-tab open logic in `main_utils/actions_factory.py`.  
4. Optionally re-opens your MRU files before showing the main window.  
5. Enters the Qt event loop.

You can launch via:

```bash
# from project root
./runme.sh           # convenience wrapper
# or
python3 main.py      # (requires PySide6, polib, etc.)
````

You may also pass an initial `.po` file on the command line; `main.py` will place it in the first tab.

# POEditor

A lightweight, PySide6-based GUI for browsing and editing GNU gettext `.po` files.  
Perfect for translators and localization engineers who need a quick, intuitive interface for searching, paging, and editing large translation catalogs.

---

## Editor Features

- **Import / Export**  
  - Drag & drop `.po` files or use the Import/Export buttons.  

- **Paging**  
  - Browse entries in fixed‐size pages (default 20 entries/page).  
  - First/Home, Previous/PageUp, Next/PageDown, Last/End shortcuts.  

- **Search & Navigate**  
  - Full‐text search on **msgid** or **msgstr**.  
  - “Find”, “↑”, “↓” buttons to jump between hits.  
  - **Overview sidebar** shows all matches across the entire file, with clickable markers to jump to any hit.  

- **Inline Editing**  
  - Click a row → Edit… dialog to update translations.  
  - Add… and Delete buttons for entry management.  

- **macOS-style Text Replacements**  
  - Supports system or custom replacement shortcuts (via `ReplacementLineEdit`).  
  - Automatically expands your configured text replacements as you type.  

- **Configurable Shortcuts & Settings**  
  - QSettings-backed keyboard shortcuts (Home, PageUp, PageDown, End).  
  - Persists your preferences between sessions.  

---

## Installation

1. **Clone** the repo:

   ```bash
   git clone https://github.com/hoangduytran/pyside_po_editor.git
   cd pyside_po_editor
   ```
2. **Install** dependencies (ideally in a virtualenv):

   ```bash
   bash getrequirement.sh
   # or, manually:
   pip install -r requirements.txt
   ```
3. **Compile** the Qt resources:

   ```bash
   ./mkresource       # runs pyside6-rcc on resources.qrc → resources_rc.py
   ```
4. **Run**:

   ```bash
   ./runme.sh
   ```

---

## Directory Structure

```
.
├─ app_kit.py
├─ db_const.py
├─ gv.py                 ← global app state (now holds only open_tabs & recent_files)
├─ lg.py                 ← logging helper
├─ main.py               ← entry‐point, builds MainWindow
├─ po_editor_main.py     ← legacy single‐file mode (superseded by tabbed UI)
│
├─ main_utils/           ← reusable UI & logic components
│   ├─ actions_factory.py    ← all menu/toolbar callbacks (now tab-aware via TabRecord)
│   ├─ collapsible_section.py
│   ├─ import_worker.py
│   ├─ left_tab_bar.py
│   ├─ main_button_enum.py
│   ├─ main_editor_tab.py
│   ├─ main_editor_tab_manager.py
│   ├─ main_toolbar_manager.py
│   ├─ po_ed_table_model.py
│   ├─ popup_mnu.py
│   ├─ safe_emit.py
│   └─ table_widgets.py
│
├─ po_editor/            ← multi‐tab editor core
│   ├─ po_editor_widget.py    ← per‐file QWidget (table, editors, suggestions)
│   ├─ po_editor_main_menu.py ← builds the shared menu bar
│   ├─ po_editor_main_gui.py  ← legacy GUI split out into menu + widget
│   ├─ po_editor_main_actions.py ← legacy callbacks
│   └─ tab_record.py           ← holds all per‐tab state (path, model, widgets, dirty flag)
│
├─ workspace/            ← dockable panels & file-search tab
│   ├─ button_symbols.py
│   ├─ file_search_tab.py
│   ├─ find_replace_bar.py
│   ├─ search_dock.py
│   └─ workspace_tab.py
│
├─ search/               ← CLI fast‐search tools
│   ├─ fast_search.py
│   └─ fast_search_open_ext_editor.py
│
├─ subcmp/               ← replacement/text-compare utilities
├─ sugg/                 ← translation suggestion backend & controller
├─ pref/                 ← Preferences dialog + persistence
├─ resources.qrc / resources_rc.py  ← Qt resource file  
├─ rs/                   ← external stylesheet, images  
├─ runme.sh              ← launcher wrapper  
├─ setup.py              ← packaging script  
└─ requirements.txt      ← Python dependencies
```

---

## Usage

1. **Open** one or more `.po` files via **File → Open…**
2. Each file appears in its own **tab** (`POEditorWidget`).
3. Use the **Find/Replace** panel (hamburger button) to search in-file.
4. Use the **Explorer** panel (folder button) to browse and open files.
5. **Save** via File → Save or **Ctrl+S**.
6. Access **Preferences** via File → Preferences (fonts, translation backends, file‐exclude patterns).
7. Recent files live under **File → (recent list)** and auto-reopen on startup.

---

## Contributing & Testing

* Tests aren’t included yet, but you can add `pytest` in `tests/` and run under GitHub Actions.
* Pay special attention to the Qt `QApplication` fixture when testing widgets.
* Use `TabRecord` and `main_gv.open_tabs` to inspect per-tab state in your tests.

---

## License

This project is released under the **MIT License**. See [LICENSE](LICENSE) for details.
