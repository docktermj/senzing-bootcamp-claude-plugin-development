"""One listing of the repository's own files, for every guard that walks it from the root or `.claude/`.

The suite went red in the main checkout whenever untracked scratch sat under
`.claude/worktrees/` (#515): a 742 MB loop scratch directory made seven tests in six files fail
on a commit that was green in a clean worktree. Each guard walked the filesystem itself, and the
worktree exclusion had been applied to some walkers and not others, in three different idioms.
This module is the one listing those guards share, so the exclusion is made once.

``corpus_files(*subtrees, root=REPO_ROOT, suffixes=None)`` returns the sorted absolute paths of
the repository's files, optionally limited to ``subtrees`` (repo-relative, ``/``-separated, such
as ``".claude"`` or ``".claude/skills"``) and to ``suffixes`` (compared with ``Path.suffix``).
Each caller keeps its own further filters; this module decides only which files are the
repository's.

How the list is made:

- **git first.** ``git -C <root> ls-files -z --cached --others --exclude-standard``, run as an
  argument list (no shell): tracked files plus untracked, non-ignored ones, so a file a
  contributor has just written, and not yet staged, is still checked. ``-z`` keeps names with
  spaces, quotes or non-ASCII characters out of git's C-quoting, and each name is built into a
  path with ``pathlib`` from git's ``/``-separated output.
- **Only what exists.** ``--cached`` still lists a tracked file deleted in the working tree, so
  every path is kept only if it exists on disk as a file. An untracked nested repository, which
  git reports as one ``dir/`` entry without descending, is not a file and is dropped too.
- **Runtime directories, always.** ``RUNTIME_DIRS`` are the directories Claude Code keeps under
  ``.claude/`` and hides through ``.git/info/exclude`` (the runtime's own list, not
  ``.gitignore``). They are pruned whatever git reports, so a clone whose ``info/exclude`` lacks
  them is still safe. Like the ``**/.claude/worktrees/`` entries in that file, they are matched
  at any depth.
- **Fallback.** When git is not found, or exits non-zero (the root is not a work tree), the list
  comes from a filesystem walk of the root that prunes ``.git/``, ``RUNTIME_DIRS`` and the
  ``.gitignore``d directories in ``FALLBACK_PRUNED``. It never fails.

⚠️ A guard that walks a subtree through an intermediate variable, or with a recursive
``iterdir``, is invisible to ``test_corpus.py``'s hand-rolled walk guard. Route it through here.

Stdlib only (INV-108).

Run:  python3 -m unittest discover -s tests
"""
import os
import subprocess
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parent.parent

#: Claude Code's runtime directories, as `.git/info/exclude` lists them today. Never corpus.
RUNTIME_DIRS = (
    (".claude", "worktrees"),
    (".claude", "checkpoints"),
    (".claude", "mailbox"),
    (".claude", "agent-memory-local"),
    (".claude", "routines", ".state"),
)

#: Directory names the fallback walk prunes at any depth: git's own, and the `.gitignore`d ones.
FALLBACK_PRUNED = frozenset((".git", "__pycache__", ".pytest_cache", ".history"))


def is_runtime(parts):
    """True when the repo-relative path ``parts`` lies inside one of ``RUNTIME_DIRS``."""
    parts = tuple(parts)
    for runtime in RUNTIME_DIRS:
        n = len(runtime)
        if any(parts[i:i + n] == runtime for i in range(len(parts) - n + 1)):
            return True
    return False


def _git_listing(root):
    """Repo-relative ``/``-separated names from git, or None when git cannot answer."""
    try:
        done = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others",
             "--exclude-standard"],
            capture_output=True)
    except OSError:
        return None
    if done.returncode != 0:
        return None
    names = done.stdout.decode("utf-8", errors="surrogateescape").split("\0")
    return {name for name in names if name}


def _walk_listing(root):
    """Repo-relative ``/``-separated names from a pruned filesystem walk."""
    names = set()
    for directory, dirs, files in os.walk(root):
        rel = Path(directory).relative_to(root).parts
        dirs[:] = [d for d in dirs
                   if d not in FALLBACK_PRUNED and not is_runtime(rel + (d,))]
        names.update(PurePosixPath(*rel, f).as_posix() for f in files)
    return names


def corpus_files(*subtrees, root=REPO_ROOT, suffixes=None):
    """Sorted absolute paths of the repository's own files under ``subtrees`` (all when none)."""
    root = Path(root)
    names = _git_listing(root)
    if names is None:
        names = _walk_listing(root)
    prefixes = [PurePosixPath(s).parts for s in subtrees]
    out = []
    for name in names:
        parts = PurePosixPath(name).parts
        if not parts or is_runtime(parts):
            continue
        if prefixes and not any(parts[:len(p)] == p for p in prefixes):
            continue
        path = root.joinpath(*parts)
        if suffixes is not None and path.suffix not in suffixes:
            continue
        if path.is_file():
            out.append(path)
    return sorted(out)
