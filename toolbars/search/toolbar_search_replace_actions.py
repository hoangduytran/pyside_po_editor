# toolbars/search/toolbar_search_replace_actions.py

import os
from PySide6.QtWidgets import QMessageBox, QTextEdit
from PySide6.QtCore    import Qt
from po_editor.po_editor_main_gui import POEditorWindow

from .fast_search import (
    SearchRequest,
    parallel_search,
)
from gv import main_gv

def get_search_actions(window, find_widget, editor_manager, get_root_path):
    """
    window           - your QMainWindow
    find_widget      - instance of ToggleFindReplace
    editor_manager   - instance of EditorTabManager
    get_root_path()  - a callable returning current directory (e.g. main_gv.current_dir)
    """
    # to store last results and current index:
    state = {
        "results": [],
        "current": 0
    }

    def on_toggle(show_replace: bool):
        # simply forward to the widget’s toggle logic
        find_widget._on_toggle(show_replace)

    def on_find():
        root = get_root_path() or os.path.expanduser("~")
        keyword = find_widget.find_edit.text().strip()
        if not keyword:
            QMessageBox.information(window, "Find", "Please enter a search term.")
            return

        # record in history if new
        hist = main_gv.find_pattern_list or []
        if keyword not in hist:
            hist.append(keyword)
            main_gv.find_pattern_list = hist

        # collect flags
        use_regex   = find_widget.flag_regex.isChecked()
        match_case  = find_widget.flag_match_case.isChecked()
        whole_word  = find_widget.flag_whole_word.isChecked()
        ignore_case = not match_case

        # assemble and run the search request, but only on .po files
        req = SearchRequest(
            root_path=root,
            keyword=keyword,
            glob="*.po",  # ← limit to PO files
            use_regex=use_regex,
            ignore_case=ignore_case,
            context=40,
            open_results=False,
            show_progress=False,
        )
        # you could incorporate whole_word by post-filtering matches if needed

        results = parallel_search(req)
        state["results"] = results
        state["current"] = 0

        # update UI
        find_widget.lbl_find_result.setText(f"{len(results)} results")
        if results:
            _show_result(0)

    def _show_result(idx: int):
        """Helper to open/navigate to result #idx."""
        res = state["results"][idx]
        # for .po, use your POEditorWindow, else a plain text viewer
        ext = os.path.splitext(res.filepath)[1].lower()
        if ext == ".po":
            editor = POEditorWindow(res.filepath)
        else:
            editor = QTextEdit()
            try:
                with open(res.filepath, "r", encoding="utf-8", errors="ignore") as f:
                    editor.setPlainText(f.read())
            except Exception as e:
                editor.setPlainText(f"Could not load:\n{e}")
        editor_manager.add_tab(editor, res.filepath)
        # move cursor to line/column:
        try:
            cursor = editor.textCursor()
            # move to line
            for _ in range(res.line - 1):
                cursor.movePosition(cursor.Down)
            # move to column
            for _ in range(res.column):
                cursor.movePosition(cursor.Right)
            editor.setTextCursor(cursor)
        except Exception:
            pass

    def on_next_found():
        if not state["results"]:
            return
        state["current"] = (state["current"] + 1) % len(state["results"])
        _show_result(state["current"])

    def on_prev_found():
        if not state["results"]:
            return
        state["current"] = (state["current"] - 1) % len(state["results"])
        _show_result(state["current"])

    def on_close():
        # clear state and reset UI
        state["results"].clear()
        state["current"] = 0
        find_widget.lbl_find_result.setText("No results")
        # optionally close the panel
        find_widget._on_toggle(False)

    def on_replace_current():
        # record in history if new
        pat = find_widget.replace_edit.text().strip()
        if pat:
            rh = main_gv.replace_pattern_list or []
            if pat not in rh:
                rh.append(pat)
                main_gv.replace_pattern_list = rh

        # now perform your replace‐current logic…
        QMessageBox.information(window, "Replace", "Replace Current not yet implemented.")

    def on_replace_all():
        # stub: you’ll need to integrate your replace-all logic here
        QMessageBox.information(window, "Replace", "Replace All not yet implemented.")

    return {
        "on_toggle":          on_toggle,
        "on_find":            on_find,
        "on_next_found":      on_next_found,
        "on_prev_found":      on_prev_found,
        "on_close":           on_close,
        "on_replace_current": on_replace_current,
        "on_replace_all":     on_replace_all,
    }
