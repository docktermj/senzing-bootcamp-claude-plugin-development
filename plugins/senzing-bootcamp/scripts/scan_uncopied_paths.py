#!/usr/bin/env python3
"""Find paths the copied production code names that graduation left behind.

Graduation Step 2 copies the bootcamp project's code into `production/` verbatim and leaves
the rest behind: its Exclude list, and anything it neither copies nor excludes. A copied
program that reads one of those paths at runtime finds nothing in `production/`, and usually
falls back quietly instead of failing, so the handover is wrong with no error to point at.

This scan searches the text of every file under `<production>/src/` for a project-relative
path (`config/bootcamp_preferences.yaml`, `data/truth/scenario_truth.json`, `data/raw/` …) that
exists in the project and not in `production/`. The uncopied set is never listed here: it is
read off the two trees as they stand after the copy, so it is whatever Step 2 left behind.
Because it is a text search, it works whatever language the code is in. It cannot tell a read
from a write or a comment, and it does not see a path the code assembles from pieces
(`Path("config") / name`); each hit is a place to look, not a proven defect.

Usage::

    python3 scan_uncopied_paths.py [--project-dir .] [--production-dir production]

Output: one `<file>: <path>` line on stdout per hit, the file relative to the production
directory, both with forward slashes, sorted. No hit prints nothing on stdout. A one-line
summary goes to stderr.

Exit codes: 0 = finished, with or without hits; 1 = the production directory does not exist.

Stdlib only and `pathlib` throughout, so it runs the same on Linux, macOS and Windows.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

#: Build output Step 2 never copies; skipped here too, in case a Merge left one behind.
BUILD_OUTPUT = {"classes", "target", "dist", "node_modules", "bin", "obj", "__pycache__"}

#: A relative path of two or more segments, separated by `/` or `\`. It may not start right
#: after a path character or `:`, so `production/data/…`, `/abs/path` and a URL's path stay out.
PATH_TOKEN = re.compile(r"(?<![\w./\\:-])[\w.-]+(?:[/\\]+[\w.-]+)+[/\\]?")


def candidates(text):
    """Each project-relative path token in ``text``, normalized to forward slashes."""
    for match in PATH_TOKEN.finditer(text):
        token = re.sub(r"[/\\]+", "/", match.group(0))
        parts = [p for p in token.split("/") if p and p != "."]
        if ".." in parts or len(parts) < 2:
            continue
        yield "/".join(parts) + ("/" if token.endswith("/") else "")


def code_files(src):
    """Every file under ``src``, outside build output."""
    for path in sorted(src.rglob("*")):
        rel = path.relative_to(src)
        if path.is_file() and not BUILD_OUTPUT.intersection(rel.parts[:-1]):
            yield path


def read_text(path):
    """The file's text, or None for a binary file."""
    data = path.read_bytes()
    if b"\0" in data:
        return None
    return data.decode("utf-8", errors="replace")


def scan(project, production):
    """Sorted ``(file, path)`` pairs: each path a copied file names that only the project has."""
    hits = set()
    src = production / "src"
    if not src.is_dir():
        return []
    for path in code_files(src):
        text = read_text(path)
        if text is None:
            continue
        for token in candidates(text):
            if token.split("/")[0] == production.name:
                continue
            if (project / token).exists() and not (production / token).exists():
                hits.add((path.relative_to(production).as_posix(), token))
    return sorted(hits)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--project-dir", default=".", help="the bootcamp project root")
    parser.add_argument("--production-dir", default=None,
                        help="the production project (default: <project-dir>/production)")
    args = parser.parse_args(argv)
    project = Path(args.project_dir).resolve()
    production = (Path(args.production_dir) if args.production_dir
                  else project / "production").resolve()
    if not production.is_dir():
        print("scan_uncopied_paths: %s does not exist" % production, file=sys.stderr)
        return 1
    hits = scan(project, production)
    for file, path in hits:
        print("%s: %s" % (file, path))
    print("scan_uncopied_paths: %d hit(s) under %s" % (len(hits), production / "src"),
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
