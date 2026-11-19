"""Cross-cutting gates: scope, links, leakage, shared-fact consistency.

Covers AC11 (scope), AC13 (link integrity), AC14/SR1 (no leakage), and the
design's single-source-of-truth contract (shared facts must not diverge).
"""

from __future__ import annotations

import os

import pytest

import docgates

_TOUCHED = ("README.md", "docs/CHANGELOG.md", "docs/FAQ.md")


def test_ac11_no_forbidden_source_files_changed(changed_files: set[str] | None) -> None:
    """AC11: the change touches no src/**, tests/**, build system, or third-party/**."""
    if changed_files is None:
        pytest.skip("git diff vs merge-base unavailable")
    bad = docgates.forbidden_changed(changed_files)
    assert not bad, f"docs-only change must not touch source/build files: {sorted(bad)}"


def test_ac11_touched_docs_are_in_the_diff(changed_files: set[str] | None) -> None:
    """AC11: the three documentation files are the product of this change."""
    if changed_files is None:
        pytest.skip("git diff vs merge-base unavailable")
    if not (set(_TOUCHED) & changed_files):
        pytest.skip("docs already merged into base; nothing in diff to assert")
    for doc in _TOUCHED:
        assert doc in changed_files, f"{doc} must be part of the docs change"


@pytest.mark.parametrize("rel", _TOUCHED)
def test_ac14_no_secret_or_local_path_leakage(repo_root: str, rel: str) -> None:
    """AC14 / SR1: no secret, credential, private email, or absolute local path."""
    with open(os.path.join(repo_root, rel), encoding="utf-8") as fh:
        text = fh.read()
    hits = docgates.scan_secrets(text)
    assert not hits, f"{rel} leaks sensitive content: {hits}"


@pytest.mark.parametrize("rel", _TOUCHED)
def test_ac13_internal_links_resolve(repo_root: str, rel: str) -> None:
    """AC13: every authored repo-relative link resolves within the tree.

    Links that resolve *outside* the repo root (the pre-existing umbrella
    ``../ATTRIBUTIONS.md`` reference, ADR-0004) are acknowledged external
    references and are not checked here.
    """
    path = os.path.join(repo_root, rel)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    base_dir = os.path.dirname(path)
    root_real = os.path.realpath(repo_root)
    for target in docgates.inline_link_targets(text):
        if not docgates.is_local_link(target):
            continue
        rel_path = docgates.strip_anchor(target)
        if not rel_path:
            continue  # pure in-page anchor
        resolved = os.path.realpath(os.path.join(base_dir, rel_path))
        if os.path.commonpath([resolved, root_real]) != root_real:
            continue  # escapes repo root -> acknowledged external (ADR-0004)
        assert os.path.exists(resolved), f"{rel}: broken internal link -> {target}"


def test_ac13_key_crosslinks_present_and_resolve(
    repo_root: str, readme: str, faq: str
) -> None:
    """AC13: the intended README<->CHANGELOG<->FAQ<->spec cross-links exist."""
    assert "docs/CHANGELOG.md" in readme and "docs/FAQ.md" in readme
    assert "CHANGELOG.md" in faq and "../README.md" in faq
    for rel in ("docs/CHANGELOG.md", "docs/FAQ.md", "docs/dev/testing-and-coverage.md"):
        assert os.path.exists(os.path.join(repo_root, rel))


def test_shared_fact_mbedtls_version_consistent(changelog: str, faq: str) -> None:
    """Single-source contract: the current Mbed TLS version is 3.6.5 everywhere."""
    import re

    assert "3.6.5" in changelog and "3.6.5" in faq
    current = re.search(r"currently\s+3\.6\.(\d+)", faq)
    assert current is not None and current.group(0).endswith("3.6.5")


def test_shared_fact_preset_consistency(readme: str, faq: str, cmake_presets: str) -> None:
    """Presets named in README and FAQ are all real and the canonical one agrees."""
    presets = docgates.preset_names(cmake_presets)["all"]
    assert docgates.mentioned_presets(readme) <= presets
    assert docgates.mentioned_presets(faq) <= presets
    assert "core-cpu-debug" in docgates.mentioned_presets(readme)
    assert "core-cpu-debug" in docgates.mentioned_presets(faq)
