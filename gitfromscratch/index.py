import os

from gitfromscratch.repo import repo_path
from gitfromscratch.objects import hash_object


def read_index() -> dict:
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
    with open(repo_path("index"), "w") as f:
        for path, sha1 in sorted(entries.items()):
            f.write(f"{sha1} {path}\n")


def add(paths: list[str]):

    entries = read_index()

    for path in paths:
        with open(path, "rb") as f:
            data = f.read()
        sha1 = hash_object(data, "blob")
        
        entries[path.replace(os.sep, "/")] = sha1

    write_index(entries)
