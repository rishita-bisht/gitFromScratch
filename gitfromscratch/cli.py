import argparse
import sys

from gitfromscratch.repo import init, is_inside_repo
from gitfromscratch.index import add as index_add
from gitfromscratch.objects import read_object
from gitfromscratch.refs import list_branches, create_branch, current_branch
from gitfromscratch.commands import commit, log, status, checkout


def require_repo():
    if not is_inside_repo():
        print("fatal: not a gitfromscratch repository (or any of the parent directories)")
        sys.exit(1)


def cmd_cat_file(sha1: str):
    obj_type, data = read_object(sha1)
    if obj_type == "blob":
        sys.stdout.buffer.write(data)
    elif obj_type == "tree":
        i = 0
        while i < len(data):
            null_idx = data.index(b"\0", i)
            mode, name = data[i:null_idx].decode().split(" ")
            entry_sha1 = data[null_idx + 1: null_idx + 21].hex()
            print(f"{mode} {entry_sha1}\t{name}")
            i = null_idx + 21
    else:
        print(data.decode())


def cmd_branch(name: str | None):
    if name is None:
        # list branches, marking the current one with *
        current = current_branch()
        for b in list_branches():
            marker = "*" if b == current else " "
            print(f"{marker} {b}")
    else:
        create_branch(name)
        print(f"Created branch '{name}'")


def main():
    parser = argparse.ArgumentParser(prog="gfs", description="gitfromscratch: a minimal Git clone")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="create a new repository")

    p_add = sub.add_parser("add", help="stage files")
    p_add.add_argument("paths", nargs="+")

    p_commit = sub.add_parser("commit", help="record staged changes")
    p_commit.add_argument("-m", "--message", required=True)

    sub.add_parser("log", help="show commit history")
    sub.add_parser("status", help="show staged/unstaged/untracked changes")

    p_cat = sub.add_parser("cat-file", help="inspect an object by hash")
    p_cat.add_argument("sha1")

    p_co = sub.add_parser("checkout", help="restore files from a commit")
    p_co.add_argument("sha1")

    p_branch = sub.add_parser("branch", help="list or create branches")
    p_branch.add_argument("name", nargs="?", default=None)

    args = parser.parse_args()

    if args.command == "init":
        init()
    elif args.command == "add":
        require_repo()
        index_add(args.paths)
    elif args.command == "commit":
        require_repo()
        sha1 = commit(args.message)
        print(f"[{current_branch()} {sha1[:7]}] {args.message}")
    elif args.command == "log":
        require_repo()
        log()
    elif args.command == "status":
        require_repo()
        status()
    elif args.command == "cat-file":
        require_repo()
        cmd_cat_file(args.sha1)
    elif args.command == "checkout":
        require_repo()
        checkout(args.sha1)
    elif args.command == "branch":
        require_repo()
        cmd_branch(args.name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
