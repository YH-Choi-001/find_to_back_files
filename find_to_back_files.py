#!/opt/homebrew/bin/python3

import argparse, os, time, subprocess
from datetime import datetime

# CONFIGURATION
IGNORE_DIRS = ["venv", ".venv", ".mypy_cache", "node_modules"]
IGNORE_FILES = [".DS_Store"]

parser = argparse.ArgumentParser(
    description="Find files/folders modified after a given timestamp for incremental backup."
)
parser.add_argument(
    "--since",
    required=True,
    metavar="DATETIME",
    help="Cutoff timestamp in 'YYYY-MM-DD HH:MM:SS' format. Only items newer than this are reported.",
)
parser.add_argument(
    "--root",
    default=os.path.join(os.path.expanduser("~"), "Documents"),
    metavar="DIR",
    help="Root directory to scan (default: ~/Documents).",
)
args = parser.parse_args()

target_str = args.since
root_dir = os.path.expanduser(args.root)
try:
    cutoff = time.mktime(datetime.strptime(target_str, "%Y-%m-%d %H:%M:%S").timetuple())
except ValueError:
    parser.error(f"--since value '{target_str}' must be in 'YYYY-MM-DD HH:MM:SS' format.")

dir_all_match = {}
git_repos = set()  # Set of directories that are git repo roots


def is_git_repo(path):
    """Return True if path contains a .git directory (i.e. is a git repo root)."""
    return os.path.isdir(os.path.join(path, ".git"))


def git_has_local_only_changes(repo_path):
    """
    Return True if the git repo at repo_path has local-only commits not pushed
    to any remote, or has no remote configured at all.
    """
    try:
        # Check if any remote is configured
        result = subprocess.run(
            ["git", "-C", repo_path, "remote"],
            capture_output=True, text=True, timeout=5
        )
        remotes = result.stdout.strip()
        if not remotes:
            # No remote configured — local only
            return True

        # Check for any local branch that is ahead of its upstream,
        # or has no upstream tracking branch at all.
        result = subprocess.run(
            ["git", "-C", repo_path, "branch", "-vv"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            # Strip the leading '* ' or '  ' marker
            line = line.strip().lstrip("* ")
            # If a branch has no upstream (no '[origin/...]' part), it's local-only
            if "[" not in line:
                return True
            # If a branch is ahead of its upstream, there are unpushed commits
            if "ahead" in line:
                return True

        return False
    except Exception:
        # On any error (git not installed, timeout, etc.) treat as local-only to be safe
        return True


# Walk bottom-up to evaluate children first, recording git repo roots
for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
    # Prune ignored directories (note: .git removed from IGNORE_DIRS so we detect repos,
    # but we skip descending into .git internals below)
    dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and d != ".git"]

    if os.path.basename(dirpath) in IGNORE_DIRS:
        continue

    if is_git_repo(dirpath):
        git_repos.add(dirpath)

    all_match = True
    has_items = False

    # Filter out ignored files before evaluation
    valid_files = [f for f in filenames if f not in IGNORE_FILES]

    # Check remaining files in current directory
    for f in valid_files:
        has_items = True
        fpath = os.path.join(dirpath, f)
        try:
            st = os.stat(fpath)
            mtime = max(st.st_mtime, getattr(st, "st_birthtime", st.st_mtime))
            if mtime <= cutoff:
                all_match = False
        except Exception:
            all_match = False

    # Check subdirectories
    for d in dirnames:
        has_items = True
        dpath = os.path.join(dirpath, d)
        if not dir_all_match.get(dpath, False):
            all_match = False

    dir_all_match[dirpath] = all_match and has_items


def find_git_repo_ancestor(path, stop_at):
    """
    Walk up from 'path' toward 'stop_at'. Return the first ancestor (or path
    itself) that is a known git repo root, or None if none found.
    """
    current = path
    while True:
        if current in git_repos:
            return current
        if current == stop_at or current == os.path.dirname(current):
            return None
        current = os.path.dirname(current)


# Print results collapsing paths
printed_dirs = set()       # directories printed as [d] whole-directory matches
printed_git_repos = set()  # git repos already emitted as [g] / [gL]

for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
    dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and d != ".git"]
    if os.path.basename(dirpath) in IGNORE_DIRS:
        continue

    # If this directory is inside an already-printed git repo, skip entirely
    repo_ancestor = find_git_repo_ancestor(dirpath, root_dir)
    if repo_ancestor and repo_ancestor in printed_git_repos:
        dirnames.clear()  # don't descend further
        continue

    # If this directory is a git repo root, emit one line for it and stop descending
    if dirpath in git_repos:
        if dir_all_match.get(dirpath, False):
            local_only = git_has_local_only_changes(dirpath)
            tag = "gL" if local_only else "g"
            print(f"[{tag}] {dirpath}")
            printed_git_repos.add(dirpath)
        dirnames.clear()  # never descend into git repo internals
        continue

    # Standard directory / file handling
    if dir_all_match.get(dirpath, False):
        parent = os.path.dirname(dirpath)
        if not dir_all_match.get(parent, False):
            print(f"[d] {dirpath}")
        printed_dirs.add(dirpath)
    else:
        valid_files = [f for f in filenames if f not in IGNORE_FILES]
        for f in valid_files:
            fpath = os.path.join(dirpath, f)
            skip = False
            p = dirpath
            while p != root_dir and p != "/":
                if p in printed_dirs and dir_all_match.get(p, False):
                    skip = True
                    break
                p = os.path.dirname(p)
            if not skip:
                try:
                    st = os.stat(fpath)
                    mtime = max(st.st_mtime, getattr(st, "st_birthtime", st.st_mtime))
                    if mtime > cutoff:
                        print(f"[-] {fpath}")
                except Exception:
                    pass
