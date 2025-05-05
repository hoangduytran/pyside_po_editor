import os
import mmap
import multiprocessing
import fnmatch
import argparse
import re
from pathlib import Path

EXCLUDED_DIRS = {'.git', 'node_modules', '__pycache__', '.venv'}

class SearchRequest:
    """
    Encapsulates parameters for a search.
    Attributes:
        root_path: str - directory to search
        keyword: str - search string or pattern
        glob_patterns: list[str] or None - file patterns to include
        use_regex: bool - whether to use regex engine
        ignore_case: bool - case-insensitive flag for regex
        context: int - number of chars to include around match
    """
    def __init__(self, root_path: str, keyword: str,
                 glob: str = None, use_regex: bool = False,
                 ignore_case: bool = False, context: int = 40):
        self.root_path = root_path
        self.keyword = keyword
        self.glob_patterns = [g.strip() for g in glob.split(',')] if glob else None
        self.use_regex = use_regex
        self.ignore_case = ignore_case
        self.context = context

class SearchResult:
    """
    Holds a single match result.
    Attributes:
        filepath: str
        line: int
        column: int
        preview: str
    """
    def __init__(self, filepath: str, line: int, column: int, preview: str):
        self.filepath = filepath
        self.line = line
        self.column = column
        self.preview = preview

# ====== Utility Functions ======

def should_skip_dir(dirpath: str) -> bool:
    return any(part in EXCLUDED_DIRS for part in Path(dirpath).parts)

# ====== Boyer–Moore Algorithm ======

def build_skip_table(pattern: bytes) -> dict:
    skip = {}
    plen = len(pattern)
    for i in range(plen - 1):
        skip[pattern[i]] = plen - i - 1
    return skip


def boyer_moore_search_mmap(mm: mmap.mmap, pattern: bytes) -> list[int]:
    skip = build_skip_table(pattern)
    matches = []
    i, plen, tlen = 0, len(pattern), len(mm)
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

# ====== Shared Helpers ======

def calculate_line_and_column(mm: mmap.mmap, positions: list[int]) -> list[tuple[int,int]]:
    data = mm[:]
    lines = data.split(b'\n')
    offsets = []
    curr = 0
    for line in lines:
        offsets.append(curr)
        curr += len(line) + 1
    out = []
    for pos in positions:
        ln = next((i for i, off in enumerate(offsets) if off > pos), len(offsets))
        start = offsets[ln-1] if ln > 0 else 0
        out.append((ln, pos - start))
    return out


def extract_preview(mm: mmap.mmap, match_pos: int, match_len: int, context: int = 40) -> str:
    start = max(match_pos - context, 0)
    end   = min(match_pos + match_len + context, len(mm))
    snippet = mm[start:end]
    return snippet.decode('utf-8', errors='replace').strip()

# ====== Find Files ======

def match_glob(filename: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(filename, pat) for pat in patterns)


def find_all_files(root_path: str, glob_patterns: list[str] | None) -> list[str]:
    out = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        if should_skip_dir(dirpath):
            dirnames[:] = []
            continue
        for fn in filenames:
            if glob_patterns and not match_glob(fn, glob_patterns):
                continue
            out.append(os.path.join(dirpath, fn))
    return out

# ====== Regex Search Path ======

def regex_search_in_file(filepath: str, pattern: str, ignore_case: bool, context: int) -> list[SearchResult] | None:
    flags = re.IGNORECASE if ignore_case else 0
    # allow any whitespace run in place of spaces
    regex = re.compile(re.escape(pattern).replace(r"\\ ", r"\\s+"), flags)
    try:
        text = open(filepath, 'r', encoding='utf-8', errors='ignore').read()
    except Exception:
        return None
    matches = [(m.start(), m.end() - m.start()) for m in regex.finditer(text)]
    if not matches:
        return None
    with open(filepath, 'rb') as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    results = []
    linecols = calculate_line_and_column(mm, [pos for pos,_ in matches])
    for (pos, length), (ln, col) in zip(matches, linecols):
        preview = extract_preview(mm, pos, length, context)
        results.append(SearchResult(filepath, ln, col, preview))
    mm.close()
    return results

# ====== Literal Search Path ======

def literal_search_in_file(filepath: str, keyword: str, context: int) -> list[SearchResult] | None:
    keyword_bytes = keyword.encode('utf-8')
    try:
        with open(filepath, 'rb') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            positions = boyer_moore_search_mmap(mm, keyword_bytes)
            if not positions:
                mm.close()
                return None
            linecols = calculate_line_and_column(mm, positions)
            results = []
            for pos, (ln, col) in zip(positions, linecols):
                preview = extract_preview(mm, pos, len(keyword_bytes), context)
                results.append(SearchResult(filepath, ln, col, preview))
            mm.close()
            return results
    except Exception:
        return None

# ====== Worker Function ======

def search_worker(args) -> list[SearchResult] | None:
    filepath, req = args
    if req.use_regex:
        return regex_search_in_file(filepath, req.keyword, req.ignore_case, req.context)
    else:
        return literal_search_in_file(filepath, req.keyword, req.context)

# ====== Parallel Search ======

def parallel_search(request: SearchRequest) -> list[SearchResult]:
    files = find_all_files(request.root_path, request.glob_patterns)
    args_list = [(f, request) for f in files]
    results: list[SearchResult] = []
    with multiprocessing.Pool(processes=os.cpu_count()) as pool:
        for res in pool.imap_unordered(search_worker, args_list):
            if res:
                results.extend(res)
    return results

# ====== CLI Entrypoint ======

def main():
    parser = argparse.ArgumentParser(description="Fast Search Tool")
    parser.add_argument('root_path', help='Root directory to search')
    parser.add_argument('keyword', help='Keyword or phrase to search')
    parser.add_argument('--glob', default=None,
                        help='Comma-separated glob patterns, e.g. "*.py,*.rst"')
    parser.add_argument('--regex', action='store_true',
                        help='Use regex mode (\s+ for spaces)')
    parser.add_argument('--ignore-case', action='store_true',
                        help='Case-insensitive search (regex only)')
    parser.add_argument('--context', type=int, default=40,
                        help='Nuber of chars of context around match, 10 will give 10 chars around the found pattern')
    args = parser.parse_args()

    req = SearchRequest(
        args.root_path,
        args.keyword,
        glob=args.glob,
        use_regex=args.regex,
        ignore_case=args.ignore_case,
        context=args.context
    )

    matches = parallel_search(req)
    if not matches:
        print(f"No occurrences of {req.keyword!r} found.")
    else:
        for m in matches:
            print(f"{m.filepath}:{m.line}:{m.column}: {m.preview}")

if __name__ == '__main__':
    main()
