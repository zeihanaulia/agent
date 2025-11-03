#!/usr/bin/env python3
"""fetch_datasets.py

Clone one or more GitHub repositories into local dataset paths without committing them.

Features:
- Read a JSON config (list of {repo, path}) or use the example config.
- Ensure target paths are added to .gitignore so `git add .` won't include them.
- Clone with configurable depth (--depth) and optional --keep-git to keep the .git directory.
- By default removes the cloned repo's .git to avoid embedded git repo warnings.

Usage:
  python scripts/fetch_datasets.py --config scripts/datasets.json

Author: generated
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Dict


DEFAULT_CONFIG_PATH = Path(__file__).parent / "datasets.json"
EXAMPLE_CONFIG_PATH = Path(__file__).parent / "datasets.example.json"


def fail(msg: str, code: int = 1) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def add_to_gitignore(repo_root: Path, target_path: Path) -> None:
    gitignore = repo_root / ".gitignore"
    rel = os.path.relpath(target_path, repo_root)
    entry = rel.rstrip("/") + "/\n"

    if gitignore.exists():
        text = gitignore.read_text()
        if entry.strip() in (line.strip() for line in text.splitlines()):
            print(f".gitignore already contains: {rel}")
            return
    else:
        text = ""

    with gitignore.open("a", encoding="utf-8") as f:
        f.write(entry)
    print(f"Added to .gitignore: {rel}")


def git_clone(repo: str, target: Path, depth: int = 1, dry_run: bool = False) -> int:
    cmd = ["git", "clone"]
    if depth and depth > 0:
        cmd += ["--depth", str(depth)]
    cmd += [repo, str(target)]
    print("Running:", " ".join(cmd))
    if dry_run:
        return 0
    res = subprocess.run(cmd)
    return res.returncode


def remove_git_dir(target: Path) -> None:
    g = target / ".git"
    if g.exists():
        if g.is_dir():
            shutil.rmtree(g)
            print(f"Removed {g}")
        else:
            g.unlink()
            print(f"Removed {g}")


def load_config(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        fail(f"Config not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"Failed to read config {path}: {e}")
    if not isinstance(data, list):
        fail("Config must be a JSON array of {\"repo\":..., \"path\":...} entries")
    return data


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Clone external repos into dataset paths without committing them.")
    p.add_argument("--config", "-c", type=Path, default=DEFAULT_CONFIG_PATH, help="Path to JSON config (list of {repo,path})")
    p.add_argument("--repo", type=str, help="Single repository URL to clone (overrides config)")
    p.add_argument("--path", type=str, help="Target path for single-repo mode (relative to repo root)")
    p.add_argument("--keep-git", action="store_true", help="Do not remove the .git directory after clone")
    p.add_argument("--depth", type=int, default=1, help="Shallow clone depth (0 means full clone)")
    p.add_argument("--force", action="store_true", help="Re-clone even if target exists (will remove first)")
    p.add_argument("--dry-run", action="store_true", help="Show actions without running git clone or file writes")
    args = p.parse_args(argv)

    repo_root = Path.cwd()

    if args.repo:
        # Single-repo mode
        if not args.path:
            fail("When using --repo you must also provide --path to indicate target directory")
        config = [{"repo": args.repo, "path": args.path}]
    else:
        if args.config == DEFAULT_CONFIG_PATH and not args.config.exists():
            # If default missing but example exists, copy example to default so user can edit it
            if EXAMPLE_CONFIG_PATH.exists():
                if not args.dry_run:
                    shutil.copy(EXAMPLE_CONFIG_PATH, DEFAULT_CONFIG_PATH)
                print(f"No config found. Copied example to {DEFAULT_CONFIG_PATH}. Edit it and re-run.")
                return 0
            else:
                fail(f"Default config not found: {DEFAULT_CONFIG_PATH}")

        config = load_config(args.config)

    for entry in config:
        if not isinstance(entry, dict):
            print("Skipping invalid entry (not an object):", entry)
            continue
        repo = entry.get("repo")
        target = entry.get("path") or entry.get("target")
        if not repo or not target:
            print("Skipping entry missing 'repo' or 'path':", entry)
            continue

        target_path = repo_root / target

        if target_path.exists():
            if args.force:
                print(f"Removing existing {target_path} (force)")
                if not args.dry_run:
                    if target_path.is_dir():
                        shutil.rmtree(target_path)
                    else:
                        target_path.unlink()
            else:
                print(f"Target exists, skipping (use --force to re-clone): {target_path}")
                continue

        ensure_parent(target_path)

        # Add to .gitignore to avoid being added accidentally
        add_to_gitignore(repo_root, target_path)

        # Clone
        code = git_clone(repo, target_path, depth=(args.depth if args.depth > 0 else 0), dry_run=args.dry_run)
        if code != 0:
            print(f"git clone failed for {repo} -> {target_path} (exit {code})")
            continue

        if not args.keep_git:
            if not args.dry_run:
                remove_git_dir(target_path)
            else:
                print(f"(dry-run) would remove {target_path / '.git'})")

        print(f"Fetched {repo} -> {target_path}")

    print("All done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
