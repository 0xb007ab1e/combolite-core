"""Pure, deterministic gate logic for the combolite-core docs-currency change.

These helpers are the machine oracles behind the acceptance criteria for
`gorovehq/combolite-core` #20 (docs-only: CHANGELOG + FAQ + README quickstart).
They are intentionally free of I/O and of any repo-path knowledge so they can be
unit-tested in isolation with known-bad fixtures (chaos-validation: a guard never
seen to go red is unproven -- see ``tests/docs/test_gate_self_check.py``).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

# --- Keep a Changelog -------------------------------------------------------

_KAC_HEADER_RE = re.compile(r"keep a changelog", re.IGNORECASE)
_SECTION_RE = re.compile(r"^##\s+\[([^\]]+)\]", re.MULTILINE)
_GROUP_RE = re.compile(
    r"^###\s+(Added|Changed|Deprecated|Removed|Fixed|Security)\b",
    re.MULTILINE,
)


@dataclass
class ChangelogVerdict:
    """Structured result of parsing a Keep-a-Changelog document."""

    has_header: bool
    sections: list[str] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True when the text parses as a minimally-conformant changelog."""
        return self.has_header and bool(self.sections) and bool(self.groups)


def parse_keepachangelog(text: str) -> ChangelogVerdict:
    """Parse *text* as a Keep-a-Changelog file.

    A conformant file references the Keep-a-Changelog spec, carries at least one
    ``## [section]`` (e.g. ``[Unreleased]`` or a version), and groups entries
    under standard ``### Added/Changed/Fixed/Security/...`` headings.
    """
    return ChangelogVerdict(
        has_header=bool(_KAC_HEADER_RE.search(text)),
        sections=_SECTION_RE.findall(text),
        groups=_GROUP_RE.findall(text),
    )


# --- Issue / PR traceability ------------------------------------------------

_ISSUE_RE = re.compile(r"(?<![\w/])#(\d+)\b")


def find_issue_refs(text: str) -> set[str]:
    """Return the set of ``#NN`` issue/PR numbers (without the ``#``) in *text*."""
    return set(_ISSUE_RE.findall(text))


# --- CMake preset fidelity --------------------------------------------------

# Preset-like tokens mentioned in prose/commands.
_PRESET_TOKEN_RE = re.compile(
    r"\b(?:core|gutenfree|studio)-[a-z]+(?:-[a-z]+)?\b|\bnoxz\b"
)
# Typed command forms: (verb, preset).
_CMD_CONFIGURE_RE = re.compile(r"cmake\s+--preset(?:=|\s+)([A-Za-z0-9_-]+)")
_CMD_BUILD_RE = re.compile(r"cmake\s+--build\s+--preset(?:=|\s+)([A-Za-z0-9_-]+)")
_CMD_TEST_RE = re.compile(r"ctest\s+(?:[^\n]*?\s)?--preset(?:=|\s+)([A-Za-z0-9_-]+)")


def mentioned_presets(text: str) -> set[str]:
    """Return every preset-like token referenced anywhere in *text*."""
    return set(_PRESET_TOKEN_RE.findall(text))


def preset_names(cmake_presets_text: str) -> dict[str, set[str]]:
    """Return configure/build/test preset-name sets from a CMakePresets.json body."""
    doc = json.loads(cmake_presets_text)
    out: dict[str, set[str]] = {}
    for key, short in (
        ("configurePresets", "configure"),
        ("buildPresets", "build"),
        ("testPresets", "test"),
    ):
        out[short] = {p["name"] for p in doc.get(key, []) if "name" in p}
    out["all"] = out["configure"] | out["build"] | out["test"]
    return out


def typed_preset_commands(text: str) -> dict[str, set[str]]:
    """Extract presets grouped by the command kind that references them."""
    return {
        "configure": set(_CMD_CONFIGURE_RE.findall(text)),
        "build": set(_CMD_BUILD_RE.findall(text)),
        "test": set(_CMD_TEST_RE.findall(text)),
    }


# --- Markdown link integrity ------------------------------------------------

_LINK_RE = re.compile(r"\[(?:[^\]]*)\]\(\s*(<[^>]+>|[^)\s]+)(?:\s+\"[^\"]*\")?\s*\)")
_SKIP_SCHEME_RE = re.compile(r"^(?:https?:|mailto:|ftp:|#|data:)", re.IGNORECASE)


def inline_link_targets(text: str) -> list[str]:
    """Return raw inline-link targets (angle brackets stripped) from markdown."""
    out: list[str] = []
    for raw in _LINK_RE.findall(text):
        tgt = raw.strip()
        if tgt.startswith("<") and tgt.endswith(">"):
            tgt = tgt[1:-1]
        out.append(tgt)
    return out


def is_local_link(target: str) -> bool:
    """True when *target* is a repo-relative path to check (not URL/anchor)."""
    return not _SKIP_SCHEME_RE.match(target)


def strip_anchor(target: str) -> str:
    """Return the path portion of a link target, dropping any ``#anchor``."""
    return target.split("#", 1)[0]


# --- Secret / local-path leakage (AC14 / SR1) -------------------------------

# Allow-listed example/benign domains that may legitimately appear in docs.
_ALLOWED_EMAIL_DOMAINS = {"example.com", "example.org"}
_EMAIL_RE = re.compile(r"\b[\w.+-]+@([\w-]+(?:\.[\w-]+)+)\b")
_SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("abs-home-path", re.compile(r"/home/[A-Za-z0-9._-]+")),
    ("abs-users-path", re.compile(r"/Users/[A-Za-z0-9._-]+")),
    ("worktree-path", re.compile(r"/runs/worktrees/")),
    ("pem-private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-pat", re.compile(r"\bghp_[A-Za-z0-9]{20,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
)


def scan_secrets(text: str) -> list[tuple[str, str]]:
    """Return ``(kind, matched-substring)`` for any secret/local-path leak.

    Deliberately does **not** scan for the bare word ``token`` -- the docs use
    "tokenizer"/"token-based traversal" legitimately (AC14 noted this false
    positive). Emails on allow-listed example domains are ignored.
    """
    hits: list[tuple[str, str]] = []
    for kind, pat in _SECRET_PATTERNS:
        for m in pat.findall(text):
            hits.append((kind, m if isinstance(m, str) else m[0]))
    for m in _EMAIL_RE.finditer(text):
        domain = m.group(1).lower()
        if domain not in _ALLOWED_EMAIL_DOMAINS:
            hits.append(("email", m.group(0)))
    return hits


# --- Fabricated coverage percentage (AC7 / SR2) -----------------------------

_PERCENT_RE = re.compile(r"\b\d{1,3}(?:\.\d+)?\s*%")


def coverage_percentages(text: str) -> list[str]:
    """Return any ``NN%`` literals in *text* (a fabricated coverage figure)."""
    return _PERCENT_RE.findall(text)


# --- Scope gate (AC11) ------------------------------------------------------

_FORBIDDEN_PREFIXES = (
    "src/",
    "include/",
    "third-party/",
    "tests/",
    "tools/",
    "cmake/",
    ".github/",
)
_FORBIDDEN_EXACT = {"CMakeLists.txt", "CMakePresets.json", "CMakeUserPresets.json"}
# QA/process artifacts that are not part of the product diff and never forbidden.
_ARTIFACT_PREFIXES = ("tests/docs/",)


def forbidden_changed(paths: set[str]) -> set[str]:
    """Return changed *paths* that fall under a source/build/third-party root.

    Materialized QA test files under ``tests/docs/`` are process artifacts and
    are excluded -- the gate targets product/source drift, not the doc-gate
    suite itself.
    """
    bad: set[str] = set()
    for p in paths:
        if any(p.startswith(a) for a in _ARTIFACT_PREFIXES):
            continue
        if p in _FORBIDDEN_EXACT or any(p.startswith(pre) for pre in _FORBIDDEN_PREFIXES):
            bad.add(p)
    return bad
