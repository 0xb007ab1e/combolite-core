"""Chaos-validation: prove each gate actually goes red on known-bad input.

A guard never seen to fail is unproven (topic-testing: "verify the gate actually
fails"). Each test here feeds a public-named, deliberately-violating fixture to
the pure gate logic and asserts the gate reports the violation -- so a real
regression in the docs cannot slip past a silently-passing check.
"""

from __future__ import annotations

import docgates

# --- Keep-a-Changelog validator --------------------------------------------

BAD_CHANGELOG_NO_HEADER = """# Changelog

## [Unreleased]
### Added
- a thing
"""

BAD_CHANGELOG_NO_SECTIONS = """# Changelog
Based on Keep a Changelog.

Just some prose with no sections and no groups.
"""

GOOD_CHANGELOG = """# Changelog
The format is based on Keep a Changelog.

## [Unreleased]
### Security
- a fix (#1)
"""


def test_changelog_validator_flags_missing_header() -> None:
    """Missing the Keep-a-Changelog reference must fail the parse."""
    assert docgates.parse_keepachangelog(BAD_CHANGELOG_NO_HEADER).ok is False


def test_changelog_validator_flags_missing_sections() -> None:
    """A header with no grouped sections must fail the parse."""
    assert docgates.parse_keepachangelog(BAD_CHANGELOG_NO_SECTIONS).ok is False


def test_changelog_validator_accepts_conformant() -> None:
    """A minimally-conformant changelog must pass (no false negative)."""
    assert docgates.parse_keepachangelog(GOOD_CHANGELOG).ok is True


# --- Issue-ref extractor ----------------------------------------------------


def test_issue_ref_extractor_picks_up_numbers() -> None:
    """Issue extraction returns the cited numbers and ignores URL path fragments."""
    assert docgates.find_issue_refs("fixes #15 and #16; see v1/2") == {"15", "16"}


# --- Preset fidelity --------------------------------------------------------

PRESETS_JSON = """{
  "version": 6,
  "configurePresets": [{"name": "core-cpu-debug"}],
  "buildPresets": [{"name": "core-cpu-debug"}],
  "testPresets": [{"name": "core-cpu-debug"}]
}"""

README_WITH_INVENTED_PRESET = "Run `cmake --preset core-imaginary-debug` to configure."


def test_preset_fidelity_catches_invented_configure_preset() -> None:
    """A `cmake --preset` naming an unknown preset must be detected as missing."""
    presets = docgates.preset_names(PRESETS_JSON)
    used = docgates.typed_preset_commands(README_WITH_INVENTED_PRESET)["configure"]
    assert used == {"core-imaginary-debug"}
    assert used - presets["configure"] == {"core-imaginary-debug"}


def test_mentioned_presets_catches_invented_token() -> None:
    """A bare invented preset token is flagged against the real preset set."""
    presets = docgates.preset_names(PRESETS_JSON)["all"]
    mentioned = docgates.mentioned_presets("try core-imaginary-debug or noxz")
    assert "core-imaginary-debug" in mentioned
    assert mentioned - presets == {"core-imaginary-debug", "noxz"}


# --- Secret / local-path scanner --------------------------------------------

LEAKY_DOC = (
    "clone to /home/b007ab1e/secret-stuff then email johnannis@fablabfortsmith.org\n"
    "-----BEGIN PRIVATE KEY-----\nMIIB...\n-----END PRIVATE KEY-----\n"
    "AKIAIOSFODNN7EXAMPLE\n"
)

CLEAN_DOC = (
    "Clone from https://github.com/gorovehq/combolite-core.git and read the "
    "tokenizer notes; token-based traversal is covered in spec 6."
)


def test_secret_scanner_catches_planted_values() -> None:
    """The scanner must flag an absolute home path, email, PEM key, and AWS key."""
    kinds = {kind for kind, _ in docgates.scan_secrets(LEAKY_DOC)}
    assert {"abs-home-path", "email", "pem-private-key", "aws-access-key"} <= kinds


def test_secret_scanner_ignores_tokenizer_false_positives() -> None:
    """Legit 'tokenizer'/'token-based' prose and repo URLs are not flagged (AC14)."""
    assert docgates.scan_secrets(CLEAN_DOC) == []


# --- Fabricated coverage percentage -----------------------------------------


def test_fabricated_percentage_detector_flags_coverage_percent() -> None:
    """A planted 'NN%' coverage figure must be detected."""
    assert docgates.coverage_percentages("line coverage is 92% currently") == ["92%"]


def test_fabricated_percentage_detector_quiet_on_prose() -> None:
    """Prose with no percentage yields no hits (no false positive)."""
    assert docgates.coverage_percentages("coverage is tracked in issue #18") == []


# --- Scope gate -------------------------------------------------------------


def test_scope_gate_flags_forbidden_source_path() -> None:
    """A changed src/ or tests/ file must be reported by the scope filter."""
    changed = {"README.md", "docs/FAQ.md", "src/cdb_crypto.c", "tests/test_crypto.c"}
    assert docgates.forbidden_changed(changed) == {
        "src/cdb_crypto.c",
        "tests/test_crypto.c",
    }


def test_scope_gate_allows_docs_and_qa_artifacts() -> None:
    """Docs and the QA doc-gate suite itself are not forbidden paths."""
    changed = {"README.md", "docs/CHANGELOG.md", "tests/docs/test_faq.py"}
    assert docgates.forbidden_changed(changed) == set()


# --- Link helpers -----------------------------------------------------------


def test_link_parser_extracts_targets_and_skips_schemes() -> None:
    """Inline-link extraction and the URL/anchor skip predicate behave correctly."""
    md = "see [FAQ](docs/FAQ.md) and [site](https://x.y) and [top](#t)"
    targets = docgates.inline_link_targets(md)
    assert "docs/FAQ.md" in targets
    assert docgates.is_local_link("docs/FAQ.md") is True
    assert docgates.is_local_link("https://x.y") is False
    assert docgates.is_local_link("#top") is False
    assert docgates.strip_anchor("docs/FAQ.md#sec") == "docs/FAQ.md"
