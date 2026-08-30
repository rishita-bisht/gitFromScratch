"""
test_basic.py — sanity tests for gitfromscratch.

Each test gets a fresh temp directory (via the tmp_path fixture) and
switches into it, so tests never interfere with each other or with
a real repo.
"""

import os

import pytest

from gitfromscratch.repo import init, is_inside_repo
from gitfromscratch.objects import hash_object, read_object
from gitfromscratch.index import add, read_index
from gitfromscratch.refs import get_head, current_branch, create_branch, list_branches
from gitfromscratch.commands import commit, write_tree, read_tree, parse_commit


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """Create a fresh gitfromscratch repo in an isolated temp directory."""
    monkeypatch.chdir(tmp_path)
    init()
    return tmp_path


# ---------------------------------------------------------------------------
# repo.py
# ---------------------------------------------------------------------------

def test_init_creates_expected_structure(repo):
    assert os.path.isdir(".gfs/objects")
    assert os.path.isdir(".gfs/refs/heads")
    assert os.path.exists(".gfs/HEAD")


def test_is_inside_repo(repo):
    assert is_inside_repo() is True


# ---------------------------------------------------------------------------
# objects.py
# ---------------------------------------------------------------------------

def test_hash_object_is_deterministic(repo):
    """Same content should always produce the same hash."""
    sha1_a = hash_object(b"hello world", "blob")
    sha1_b = hash_object(b"hello world", "blob")
    assert sha1_a == sha1_b


def test_different_content_different_hash(repo):
    sha1_a = hash_object(b"hello", "blob")
    sha1_b = hash_object(b"world", "blob")
    assert sha1_a != sha1_b


def test_hash_object_roundtrip(repo):
    sha1 = hash_object(b"some content", "blob")
    obj_type, data = read_object(sha1)
    assert obj_type == "blob"
    assert data == b"some content"


# ---------------------------------------------------------------------------
# index.py
# ---------------------------------------------------------------------------

def test_add_stages_a_file(repo):
    with open("a.txt", "w") as f:
        f.write("hello")

    add(["a.txt"])
    entries = read_index()

    assert "a.txt" in entries
    assert len(entries["a.txt"]) == 40  # sha1 hex digest length


def test_add_multiple_files(repo):
    with open("a.txt", "w") as f:
        f.write("A")
    os.makedirs("sub", exist_ok=True)
    with open("sub/b.txt", "w") as f:
        f.write("B")

    add(["a.txt", "sub/b.txt"])
    entries = read_index()

    assert set(entries.keys()) == {"a.txt", "sub/b.txt"}


# ---------------------------------------------------------------------------
# refs.py
# ---------------------------------------------------------------------------

def test_head_is_none_before_first_commit(repo):
    assert get_head() is None


def test_default_branch_is_main(repo):
    assert current_branch() == "main"


def test_create_branch_requires_a_commit(repo):
    with pytest.raises(ValueError):
        create_branch("feature-x")


# ---------------------------------------------------------------------------
# commands.py — the full workflow
# ---------------------------------------------------------------------------

def test_commit_and_log(repo):
    with open("a.txt", "w") as f:
        f.write("hello")
    add(["a.txt"])

    sha1 = commit("first commit")
    info = parse_commit(sha1)

    assert info["message"].strip() == "first commit"
    assert "parent" not in info  # first commit has no parent


def test_second_commit_has_parent(repo):
    with open("a.txt", "w") as f:
        f.write("v1")
    add(["a.txt"])
    first_sha1 = commit("first")

    with open("a.txt", "w") as f:
        f.write("v2")
    add(["a.txt"])
    second_sha1 = commit("second")

    info = parse_commit(second_sha1)
    assert info["parent"] == first_sha1


def test_write_tree_and_read_tree_roundtrip(repo):
    with open("a.txt", "w") as f:
        f.write("A")
    os.makedirs("sub", exist_ok=True)
    with open("sub/b.txt", "w") as f:
        f.write("B")

    add(["a.txt", "sub/b.txt"])
    tree_sha1 = write_tree()
    files = read_tree(tree_sha1)

    assert set(files.keys()) == {"a.txt", "sub/b.txt"}


def test_branch_created_after_commit(repo):
    with open("a.txt", "w") as f:
        f.write("hello")
    add(["a.txt"])
    commit("first")

    create_branch("feature-x")
    assert "feature-x" in list_branches()
    assert "main" in list_branches()
