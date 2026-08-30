import os

from gitfromscratch.repo import repo_path


def get_head() -> str | None:
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
    head_path = repo_path("HEAD")
    with open(head_path) as f:
        ref = f.read().strip()

    if ref.startswith("ref: refs/heads/"):
        return ref[len("ref: refs/heads/"):]
    return None


def list_branches() -> list[str]:
    heads_dir = repo_path("refs", "heads")
    if not os.path.isdir(heads_dir):
        return []
    return sorted(os.listdir(heads_dir))


def create_branch(name: str):
    sha1 = get_head()
    if sha1 is None:
        raise ValueError("Cannot create a branch: no commits yet.")

    branch_path = repo_path("refs", "heads", name)
    if os.path.exists(branch_path):
        raise ValueError(f"Branch '{name}' already exists.")

    with open(branch_path, "w") as f:
        f.write(sha1 + "\n")


def switch_branch(name: str):
    branch_path = repo_path("refs", "heads", name)
    if not os.path.exists(branch_path):
        raise ValueError(f"Branch '{name}' does not exist.")

    with open(repo_path("HEAD"), "w") as f:
        f.write(f"ref: refs/heads/{name}\n")
