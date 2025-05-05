"""
Fast Search Tool

High-performance CLI search utility with optional regex, progress bar, and external opening.

Processing Steps:
1. **Collect Files**: Walk `root_path`, skip excluded dirs, apply optional glob filters.
2. **Parallel Search**: Spawn worker processes to search each file (literal or regex).
3. **Map Matches**: Calculate line/column and preview snippet for each match.
4. **Output/Open**: Print matches or open in VS Code/Chrome with highlighting.

Usage:
    fast_search.py <root_path> <keyword> [--glob GLOBS] [--regex] [--ignore-case]
                   [--context N] [--open] [--progress]

example:
    python3 fast_search_open_ext_editor.py
        $BLENDER_GIT "AOV conflicting"
        --regex
        --context 10
        --open
        --glob "*.c,*.h,*.cc,*.cpp,*.hh,*.hpp,*.py,*.html,*.rst"
        --progress

    python3 fast_search_open_ext_editor.py $BLENDER_GIT "AOV conflicting" --regex --context 10 --open --glob "*.c,*.h,*.cc,*.cpp,*.hh,*.hpp,*.py,*.html,*.rst" --progress
Environment:
    BLENDER_WEB_ROOT must be set for RST → HTML mapping.
    REPLACE_PART points to 'manual-old/manual' within that tree.
"""
import os
import pickle
import mmap
import multiprocessing
import fnmatch
import argparse
import re
import subprocess
import urllib.parse
from pathlib import Path

import pyperclip
from tqdm import tqdm

# --- Configuration Constants ---
CACHE_FILE = Path.home() / '.fast_search_file_list.pkl'

EXCLUDED_DIRS = {'.git', 'node_modules', '__pycache__', '.venv'}
BLENDER_WEB_ROOT = os.getenv('BLENDER_WEB_ROOT', '')
REPLACE_PART = 'manual-old/manual'

class SearchRequest:
    """
    Search parameters container.

    Attributes:
        root_path (str): Directory to search.
        keyword (str): Search term or regex.
        glob_patterns (list[str]|None): File patterns to include.
        use_regex (bool): Regex mode flag.
        ignore_case (bool): Case-insensitive for regex.
        context (int): Preview characters around match.
        open_results (bool): Open matches externally.
        show_progress (bool): Display progress bar.
    """
    def __init__(
        self,
        root_path: str,
        keyword: str,
        glob: str = None,
        use_regex: bool = False,
        ignore_case: bool = False,
        context: int = 40,
        open_results: bool = False,
        show_progress: bool = False,
    ):
        self.root_path = root_path
        self.keyword = keyword
        self.glob_patterns = [g.strip() for g in glob.split(',')] if glob else None
        self.use_regex = use_regex
        self.ignore_case = ignore_case
        self.context = context
        self.open_results = open_results
        self.show_progress = show_progress

class SearchResult:
    """
    Represents a single match.

    Attributes:
        filepath (str): File path.
        line (int): 1-based line number.
        column (int): 0-based column offset.
        preview (str): Context snippet.
    """
    def __init__(self, filepath: str, line: int, column: int, preview: str):
        self.filepath = filepath
        self.line = line
        self.column = column
        self.preview = preview

# --- Utility Functions ---

def should_skip_dir(dirpath: str) -> bool:
    """Skip VCS and virtual env directories."""
    return any(part in EXCLUDED_DIRS for part in Path(dirpath).parts)

# --- Boyer–Moore (Literal) ---

def build_skip_table(pattern: bytes) -> dict:
    """Bad-character skip table for Boyer–Moore."""
    skip = {}
    plen = len(pattern)
    for i in range(plen - 1):
        skip[pattern[i]] = plen - i - 1
    return skip


def boyer_moore_search_mmap(mm: mmap.mmap, pattern: bytes) -> list[int]:
    """Return byte offsets of literal pattern occurrences."""
    skip = build_skip_table(pattern)
    matches, i, plen, tlen = [], 0, len(pattern), len(mm)
    while i <= tlen - plen:
        j = plen - 1
        while j >= 0 and mm[i + j] == pattern[j]:
            j -= 1
        if j < 0:
            matches.append(i)
            i += plen
        else:
            i += skip.get(mm[i + plen - 1], plen)
    return matches

# --- Shared Helpers ---

def calculate_line_and_column(mm: mmap.mmap, positions: list[int]) -> list[tuple[int,int]]:
    """Convert byte offsets to (line, column)."""
    data = mm[:]
    offsets, curr = [], 0
    for line in data.split(b'\n'):
        offsets.append(curr)
        curr += len(line) + 1
    result = []
    for pos in positions:
        ln = next((i for i, off in enumerate(offsets) if off > pos), len(offsets))
        start = offsets[ln-1] if ln > 0 else 0
        result.append((ln + 1, pos - start))  # 1-based line
    return result


def extract_preview(mm: mmap.mmap, pos: int, length: int, context: int) -> str:
    """UTF-8 snippet around match."""
    start = max(pos - context, 0)
    end = min(pos + length + context, len(mm))
    return mm[start:end].decode('utf-8', errors='replace').strip()

# --- Caching of File List ---

def load_or_build_file_list(root: str, glob_patterns: list[str]|None) -> list[str]:
    """
    Load a cached file list if available; otherwise rebuild and cache it.
    """
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'rb') as f:
                data = pickle.load(f)
            if data.get('root') == root and data.get('globs') == glob_patterns:
                return data.get('files', [])
    except Exception:
        pass
    # Rebuild file list
    files = find_all_files(root, glob_patterns)
    try:
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump({'root': root, 'globs': glob_patterns, 'files': files}, f)
    except Exception:
        pass
    return files

# --- File Discovery ---

def find_all_files(root_path: str, glob_patterns: list[str]|None) -> list[str]:
    """Collect files, applying skip and glob filters."""
    files = []
    for dp, dns, fns in os.walk(root_path):
        if should_skip_dir(dp):
            dns[:] = []
            continue
        for fn in fns:
            if glob_patterns and not any(fnmatch.fnmatch(fn, pat) for pat in glob_patterns):
                continue
            files.append(os.path.join(dp, fn))
    return files

# --- RST → HTML Mapping ---

def convert_rst_to_html(rst_path: str) -> Path|None:
    """Map RST file to built HTML path under Blender docs."""
    try:
        tail = rst_path.split('/manual/')[1]
    except IndexError:
        return None
    front = os.path.join(BLENDER_WEB_ROOT, REPLACE_PART)
    html = Path(os.path.join(front, tail)).with_suffix('.html')
    return html if html.is_file() else None

# --- Search Implementations ---

def is_within_html_tag(data: bytes, pos: int) -> bool:
    """
    Determine if a byte-offset pos falls within an HTML tag (i.e. between '<' and '>').
    """
    # Find last '<' and '>' before pos
    last_open = data.rfind(b'<', 0, pos)
    last_close = data.rfind(b'>', 0, pos)
    return last_open > last_close


def regex_search_in_file(filepath: str, pattern: str, ignore_case: bool, context: int) -> list[SearchResult]:
    """Regex search: flexible whitespace, optional case insensitivity."""
    flags = re.IGNORECASE if ignore_case else 0
    regex = re.compile(re.escape(pattern).replace(r"\\ ", r"\\s+"), flags)
    try:
        text = open(filepath, encoding='utf-8', errors='ignore').read()
    except:
        return []
    matches = [(m.start(), m.end()-m.start()) for m in regex.finditer(text)]
    if not matches:
        return []
    with open(filepath, 'rb') as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    results = []
    for pos, length in matches:
        for ln, col in calculate_line_and_column(mm, [pos]):
            preview = extract_preview(mm, pos, length, context)
            results.append(SearchResult(filepath, ln, col, preview))
    mm.close()
    return results


def literal_search_in_file(filepath: str, keyword: str, context: int) -> list[SearchResult]:
    """Literal search using Boyer–Moore algorithm."""
    kb = keyword.encode('utf-8')
    try:
        with open(filepath, 'rb') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            positions = boyer_moore_search_mmap(mm, kb)
    except:
        return []
    if not positions:
        mm.close()
        return []
    results = []
    for pos, (ln, col) in zip(positions, calculate_line_and_column(mm, positions)):
        preview = extract_preview(mm, pos, len(kb), context)
        results.append(SearchResult(filepath, ln, col, preview))
    mm.close()
    return results

# --- External Viewer ---

OPENED = set()

def open_in_editor(result: SearchResult, keyword: str):
    """Open result once: VS Code for source, Chrome for HTML/RST."""
    ext = Path(result.filepath).suffix.lower()
    if ext == '.rst':
        html = convert_rst_to_html(result.filepath)
        target = str(html) if html else None
    elif ext == '.html':
        target = result.filepath
    else:
        target = f"{result.filepath}:{result.line}:{result.column}"

    if not target or target in OPENED:
        return
    OPENED.add(target)

    if ext in {'.rst', '.html'}:
        frag = urllib.parse.quote(keyword)
        url = f"file://{target}#:~:text={frag}"
        subprocess.run(['open', '-a', 'Google Chrome', url])
    else:
        subprocess.run(['code', '--goto', target])

# --- Worker & Parallel Search ---

def _worker(arg):
    """Select appropriate search function."""
    filepath, req = arg
    if req.use_regex:
        return regex_search_in_file(filepath, req.keyword, req.ignore_case, req.context)
    return literal_search_in_file(filepath, req.keyword, req.context)


def parallel_search(req: SearchRequest) -> list[SearchResult]:
    """Run search over files in parallel, optionally with progress and opening."""
    files = find_all_files(req.root_path, req.glob_patterns)
    args = [(f, req) for f in files]
    results = []
    with multiprocessing.Pool() as pool:
        iterator = pool.imap_unordered(_worker, args)
        if req.show_progress:
            iterator = tqdm(iterator, total=len(args), desc="Searching", unit="file")
        for res in iterator:
            results.extend(res)
    if req.open_results:
        for r in results:
            open_in_editor(r, req.keyword)
    return results

# --- Clipboard Utility ---

def copy_to_clipboard(text: str):
    """Copy text to clipboard using pyperclip."""
    try:
        pyperclip.copy(text)
    except Exception as e:
        print(f"Clipboard error: {e}")

# --- CLI Entrypoint ---

def main():
    """Parse CLI args and execute search."""
    parser = argparse.ArgumentParser(prog='fast_search')
    parser.add_argument('root_path', help='Directory to search')
    parser.add_argument('keyword', help='Search term or pattern')
    parser.add_argument('--glob', default=None, help='Comma-separated globs')
    parser.add_argument('--regex', action='store_true', help='Use regex')
    parser.add_argument('--ignore-case', action='store_true', help='Regex ignore case')
    parser.add_argument('--context', type=int, default=40, help='Preview chars')
    parser.add_argument('--open', action='store_true', help='Open matches')
    parser.add_argument('--progress', action='store_true', help='Show progress')
    args = parser.parse_args()

    copy_to_clipboard(args.keyword)
    req = SearchRequest(
        args.root_path,
        args.keyword,
        glob=args.glob,
        use_regex=args.regex,
        ignore_case=args.ignore_case,
        context=args.context,
        open_results=args.open,
        show_progress=args.progress
    )
    matches = parallel_search(req)
    # Summary: total matches and number of files
    total_matches = len(matches)
    files_with_matches = len({m.filepath for m in matches})
    print(f"Found {total_matches} matches across {files_with_matches} files.")
    if not req.open_results:
        if not matches:
            print(f"No occurrences of {args.keyword!r} found.")
        for m in matches:
            print(f"{m.filepath}:{m.line}:{m.column}: {m.preview}")

if __name__ == '__main__':
    main()
