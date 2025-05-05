# POEditor

A lightweight, PySide6-based GUI for browsing and editing GNU gettext `.po` files.  
Perfect for translators and localization engineers who need a quick, intuitive interface for searching, paging, and editing large translation catalogs.

---

## 🚀 Features

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

## 📸 Screenshot

![POEditor main window with search and sidebar navigation](docs/screenshot.png)

---

## 🛠️ Installation

1. **Clone** this repository  
   ```bash
   git clone https://github.com/yourusername/POEditor.git
   cd POEditor
