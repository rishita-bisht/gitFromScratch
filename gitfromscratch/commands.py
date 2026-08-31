"""
commands.py — the high-level operations users actually run.

This is where objects.py + index.py + refs.py come together to form
real Git-like behavior: commit, log, checkout, status, branch.
"""

import os
import time

from gitfromscratch.objects import hash_object, read_object
from gitfromscratch.index import read_index
from gitfromscratch.refs import get_head, set_head, current_branch, detach_head


# ---------------------------------------------------------------------------
# Trees — building a nested tree object from the flat staging index
# ---------------------------------------------------------------------------

def write_tree() -> str:
    """
    Turn the flat staging index ({'sub/b.txt': hash, ...}) into a nested
    tree of tree objects, and return the hash of the root tree.
    """
    entries = read_index()

    root: dict = {}
    for path, sha1 in entries.items():
        parts = path.split("/")
        node = root
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = sha1

    def build(node: dict) -> str:
        rows = []
        for name, val in sorted(node.items()):
            if isinstance(val, dict):
                rows.append(("40000", name, build(val)))
            else:
                rows.append(("100644", name, val))

        tree_data = b""
        for mode, name, sha1 in rows:
            tree_data += f"{mode} {name}\0".encode() + bytes.fromhex(sha1)
        return hash_object(tree_data, "tree")

    return build(root)


def read_tree(sha1: str, prefix: str = "") -> dict:
    """Flatten a tree object back into {path: blob_hash}, walking subtrees recursively."""
    obj_type, data = read_object(sha1)
    assert obj_type == "tree"

    entries = {}
    i = 0
    while i < len(data):
        null_idx = data.index(b"\0", i)
        mode, name = data[i:null_idx].decode().split(" ")
        entry_sha1 = data[null_idx + 1: null_idx + 21].hex()
        path = f"{prefix}{name}"

        if mode == "40000":
            entries.update(read_tree(entry_sha1, prefix=path + "/"))
        else:
            entries[path] = entry_sha1

        i = null_idx + 21

    return entries


# ---------------------------------------------------------------------------
# Commit
# ---------------------------------------------------------------------------

def commit(message: str, author: str = "gitfromscratch <gfs@example.com>") -> str:
    tree = write_tree()
    parent = get_head()

    lines = [f"tree {tree}"]
    if parent:
        lines.append(f"parent {parent}")
    ts = int(time.time())
    lines.append(f"author {author} {ts} +0000")
    lines.append(f"committer {author} {ts} +0000")
    lines.append("")
    lines.append(message)

    data = "\n".join(lines).encode()
    sha1 = hash_object(data, "commit")
    set_head(sha1)
    return sha1


def parse_commit(sha1: str) -> dict:
    obj_type, data = read_object(sha1)
    assert obj_type == "commit"

    header, message = data.decode().split("\n\n", 1)
    info = {"message": message}
    for line in header.split("\n"):
        key, _, val = line.partition(" ")
        info[key] = val
    return info


# ---------------------------------------------------------------------------
# Log
# ---------------------------------------------------------------------------

def log():
    sha1 = get_head()
    if not sha1:
        print("No commits yet.")
        return

    while sha1:
        info = parse_commit(sha1)
        print(f"commit {sha1}")
        print(f"Author: {info.get('author', '')}")
        print()
        print(f"    {info['message'].strip()}")
        print()
        sha1 = info.get("parent")


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------

def checkout(sha1: str):
    info = parse_commit(sha1)
    files = read_tree(info["tree"])

    for path, blob_sha1 in files.items():
        obj_type, data = read_object(blob_sha1)
        assert obj_type == "blob"

        dirname = os.path.dirname(path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

    detach_head(sha1)
    print(f"Checked out {len(files)} file(s) from {sha1[:7]}")
    print(f"Note: you are in 'detached HEAD' state at {sha1[:7]}.")


# ---------------------------------------------------------------------------
# Status — compares HEAD tree vs. index vs. working directory
# ---------------------------------------------------------------------------

def status():
    head_sha1 = get_head()
    head_files = read_tree(parse_commit(head_sha1)["tree"]) if head_sha1 else {}
    staged_files = read_index()

    branch = current_branch()
    print(f"On branch {branch}" if branch else "HEAD detached")
    print()

    staged_new_or_modified = {
        p: h for p, h in staged_files.items()
        if p not in head_files or head_files[p] != h
    }
    staged_deleted = [p for p in head_files if p not in staged_files]

    if staged_new_or_modified or staged_deleted:
        print("Changes to be committed:")
        for p in staged_new_or_modified:
            status_word = "new file" if p not in head_files else "modified"
            print(f"  {status_word}:   {p}")
        for p in staged_deleted:
            print(f"  deleted:    {p}")
        print()

    modified_not_staged = []
    for path, staged_hash in staged_files.items():
        if os.path.exists(path):
            with open(path, "rb") as f:
                current_hash = hash_object(f.read(), "blob", write=False)
            if current_hash != staged_hash:
                modified_not_staged.append(path)
        else:
            modified_not_staged.append(path)

    if modified_not_staged:
        print("Changes not staged for commit:")
        for p in modified_not_staged:
            print(f"  modified:   {p}")
        print()

    tracked = set(staged_files.keys())
    untracked = []
    for dirpath, dirnames, filenames in os.walk("."):
        dirnames[:] = [d for d in dirnames if d != ".gfs" and not d.startswith(".git")]
        for fname in filenames:
            rel = os.path.relpath(os.path.join(dirpath, fname), ".").replace(os.sep, "/")
            if rel not in tracked:
                untracked.append(rel)

    if untracked:
        print("Untracked files:")
        for p in sorted(untracked):
            print(f"  {p}")
        print()

    if not (staged_new_or_modified or staged_deleted or modified_not_staged or untracked):
        print("Nothing to commit, working tree clean.")
