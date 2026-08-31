"""
index.py — the staging area.

Before a commit happens, files must be "staged" (added to the index).
The index is simply a map of: file path -> blob hash.

Real Git stores this as a binary file with extra metadata (timestamps,
file size, etc.) so it can quickly detect changes without re-reading
every file. We keep it simple: plain text, one "hash path" per line.
"""

import os

from gitfromscratch.repo import repo_path
from gitfromscratch.objects import hash_object


def read_index() -> dict:
    """Read the current staging area into a dict of {path: blob_hash}."""
    index_path = repo_path("index")
    entries = {}

    if os.path.exists(index_path):
        with open(index_path) as f:
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                sha1, path = line.split(" ", 1)
                entries[path] = sha1

    return entries


def write_index(entries: dict):
    """Overwrite the staging area with the given {path: blob_hash} entries."""
    with open(repo_path("index"), "w") as f:
        for path, sha1 in sorted(entries.items()):
            f.write(f"{sha1} {path}\n")


def _collect_files(path: str) -> list[str]:
    """Given a path, return every FILE under it (walks folders recursively)."""
    if os.path.isfile(path):
        return [path]

    files = []
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d != ".gfs" and not d.startswith(".git")]
        for fname in filenames:
            files.append(os.path.join(dirpath, fname))
    return files


def add(paths: list[str]):
    """
    Stage one or more files (or folders, staging everything inside):
      1. read each file's content
      2. store it as a blob object (hash_object)
      3. record path -> hash in the index
    """
    entries = read_index()

    for path in paths:
        for file_path in _collect_files(path):
            with open(file_path, "rb") as f:
                data = f.read()
            sha1 = hash_object(data, "blob")
            clean_path = os.path.normpath(file_path).replace(os.sep, "/")
            entries[clean_path] = sha1

    write_index(entries)
