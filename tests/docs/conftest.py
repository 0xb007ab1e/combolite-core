"""Shared fixtures for the docs-currency acceptance suite.

Locates the repository root from this file's position and exposes the touched
documents plus the verification source files (CMakePresets.json, spec, dev docs)
as text, so the gate tests assert against the real merged tree.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def _find_repo_root(start: str) -> str:
    cur = start
    while True:
        if os.path.isfile(os.path.join(cur, "CMakePresets.json")) and os.path.isdir(
            os.path.join(cur, "docs")
        ):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            raise RuntimeError("repo root (CMakePresets.json + docs/) not found")
        cur = parent


@pytest.fixture(scope="session")
def repo_root() -> str:
    """Absolute path to the combolite-core worktree root."""
    return _find_repo_root(os.path.dirname(os.path.abspath(__file__)))


def _read(root: str, rel: str) -> str:
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture(scope="session")
def readme(repo_root: str) -> str:
    """Text of README.md."""
    return _read(repo_root, "README.md")


@pytest.fixture(scope="session")
def changelog(repo_root: str) -> str:
    """Text of docs/CHANGELOG.md."""
    return _read(repo_root, "docs/CHANGELOG.md")


@pytest.fixture(scope="session")
def faq(repo_root: str) -> str:
    """Text of docs/FAQ.md."""
    return _read(repo_root, "docs/FAQ.md")


@pytest.fixture(scope="session")
def cmake_presets(repo_root: str) -> str:
    """Text of CMakePresets.json."""
    return _read(repo_root, "CMakePresets.json")


@pytest.fixture(scope="session")
def cmakelists(repo_root: str) -> str:
    """Text of the top-level CMakeLists.txt."""
    return _read(repo_root, "CMakeLists.txt")


@pytest.fixture(scope="session")
def spec_security(repo_root: str) -> str:
    """Text of docs/spec/12-security.md (crypto consistency reference)."""
    return _read(repo_root, "docs/spec/12-security.md")


@pytest.fixture(scope="session")
def crypto_source(repo_root: str) -> str:
    """Text of src/cdb_crypto.c (ground truth for the identity-key scheme)."""
    return _read(repo_root, "src/cdb_crypto.c")


@pytest.fixture(scope="session")
def changed_files(repo_root: str) -> set[str] | None:
    """Committed product diff against the merge-base, or None if undeterminable."""

    def _git(*args: str) -> str | None:
        try:
            out = subprocess.run(
                ["git", *args],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
        except (OSError, ValueError):
            return None
        if out.returncode != 0:
            return None
        return out.stdout.strip()

    base = None
    for ref in ("origin/main", "main", "origin/HEAD"):
        base = _git("merge-base", "HEAD", ref)
        if base:
            break
    if not base:
        return None
    diff = _git("diff", "--name-only", base, "HEAD")
    if diff is None:
        return None
    return {line for line in diff.splitlines() if line.strip()}
