import os

GIT_DIR = ".gfs"


def repo_path(*paths) -> str:
    return os.path.join(GIT_DIR, *paths)


def init():
    os.makedirs(repo_path("objects"), exist_ok=True)
    os.makedirs(repo_path("refs", "heads"), exist_ok=True)

    head_path = repo_path("HEAD")
    if not os.path.exists(head_path):
        with open(head_path, "w") as f:
            f.write("ref: refs/heads/main\n")

    print(f"Initialized empty gitfromscratch repository in {os.path.abspath(repo_path())}")


def is_inside_repo() -> bool:
    return os.path.isdir(GIT_DIR)
