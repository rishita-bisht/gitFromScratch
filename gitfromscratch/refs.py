"""
refs.py — HEAD and branches.

A branch is nothing fancy: it's just a small file containing a commit hash.
HEAD is usually an *indirect* pointer — it says "look at this branch file"
rather than storing a commit hash directly. That's what makes committing
on a branch automatically "move the branch forward".
"""

import os

from gitfromscratch.repo import repo_path


def get_head() -> str | None:
    """Resolve HEAD all the way down to an actual commit hash (or None if no commits yet)."""
    head_path = repo_path("HEAD")
    with open(head_path) as f:
        ref = f.read().strip()

    if ref.startswith("ref: "):
        branch_path = repo_path(ref[5:])
        if os.path.exists(branch_path):
            with open(branch_path) as f:
                return f.read().strip()
        return None  # branch exists but has no commits yet

    return ref  # detached HEAD: HEAD file directly holds a commit hash


def set_head(sha1: str):
    """Point the current branch (or HEAD, if detached) at a new commit hash."""
    head_path = repo_path("HEAD")
    with open(head_path) as f:
        ref = f.read().strip()

    if ref.startswith("ref: "):
        branch_path = repo_path(ref[5:])
        os.makedirs(os.path.dirname(branch_path), exist_ok=True)
        with open(branch_path, "w") as f:
            f.write(sha1 + "\n")
    else:
        with open(head_path, "w") as f:
            f.write(sha1 + "\n")


def current_branch() -> str | None:
    """Return the current branch name, or None if HEAD is detached."""
    head_path = repo_path("HEAD")
    with open(head_path) as f:
        ref = f.read().strip()

    if ref.startswith("ref: refs/heads/"):
        return ref[len("ref: refs/heads/"):]
    return None


def list_branches() -> list[str]:
    """List every branch that exists (has a file under refs/heads/)."""
    heads_dir = repo_path("refs", "heads")
    if not os.path.isdir(heads_dir):
        return []
    return sorted(os.listdir(heads_dir))


def create_branch(name: str):
    """Create a new branch pointing at the current commit."""
    sha1 = get_head()
    if sha1 is None:
        raise ValueError("Cannot create a branch: no commits yet.")

    branch_path = repo_path("refs", "heads", name)
    if os.path.exists(branch_path):
        raise ValueError(f"Branch '{name}' already exists.")

    with open(branch_path, "w") as f:
        f.write(sha1 + "\n")


def switch_branch(name: str):
    """Point HEAD at a different branch (does NOT touch working directory files)."""
    branch_path = repo_path("refs", "heads", name)
    if not os.path.exists(branch_path):
        raise ValueError(f"Branch '{name}' does not exist.")

    with open(repo_path("HEAD"), "w") as f:
        f.write(f"ref: refs/heads/{name}\n")


def detach_head(sha1: str):
    """Point HEAD directly at a commit hash (used by checkout — 'detached HEAD' state)."""
    head_path = repo_path("HEAD")
    with open(head_path, "w") as f:
        f.write(sha1 + "\n")
