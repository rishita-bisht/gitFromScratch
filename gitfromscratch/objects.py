import hashlib
import os
import zlib

from gitfromscratch.repo import repo_path


def hash_object(data: bytes, obj_type: str = "blob", write: bool = True) -> str:
    header = f"{obj_type} {len(data)}\0".encode()
    full = header + data
    sha1 = hashlib.sha1(full).hexdigest()

    if write:
        path = repo_path("objects", sha1[:2], sha1[2:])
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(zlib.compress(full))

    return sha1


def read_object(sha1: str):
    path = repo_path("objects", sha1[:2], sha1[2:])
    with open(path, "rb") as f:
        full = zlib.decompress(f.read())

    null_idx = full.index(b"\0")
    header = full[:null_idx].decode()
    obj_type, _size = header.split()
    data = full[null_idx + 1:]
    return obj_type, data
