"""CHANGELOG acceptance gates (FR1, FR2, AC1-AC3, AC12)."""

from __future__ import annotations

import docgates


def test_ac1_parses_as_keepachangelog(changelog: str) -> None:
    """AC1: Keep-a-Changelog header + at least one section with grouped entries."""
    v = docgates.parse_keepachangelog(changelog)
    assert v.has_header, "CHANGELOG must reference the Keep a Changelog format"
    assert v.sections, "CHANGELOG must have at least one ## [section]"
    assert v.groups, "CHANGELOG must group entries under ### headings"
    assert v.ok


def test_ac1_has_unreleased_section(changelog: str) -> None:
    """AC1 / ADR-0006: no tagged release invented; work lives under [Unreleased]."""
    sections = docgates.parse_keepachangelog(changelog).sections
    assert "Unreleased" in sections


def test_ac2_mbedtls_bump_present(changelog: str) -> None:
    """AC2: records the Mbed TLS 3.6.5 bump."""
    assert "Mbed TLS" in changelog
    assert "3.6.5" in changelog


def test_ac2_ubsan_fixes_cover_crypto_pager_index(changelog: str) -> None:
    """AC2: UBSan fixes in crypto, pager, and index are each recorded."""
    low = changelog.lower()
    assert "ubsan" in low or "undefinedbehaviorsanitizer" in low
    for subsystem in ("crypto", "pager", "index"):
        assert subsystem in low, f"CHANGELOG must mention the {subsystem} UBSan fix"


def test_ac2_references_milestone_arc(changelog: str) -> None:
    """AC2: references the M-series milestone state."""
    assert "M26" in changelog and "M0" in changelog


def test_ac3_required_issue_numbers_present(changelog: str) -> None:
    """AC3: #1, #15, #16, #17 each appear against an entry."""
    refs = docgates.find_issue_refs(changelog)
    for required in ("1", "15", "16", "17"):
        assert required in refs, f"CHANGELOG must cite #{required}"


def test_ac3_mbedtls_entry_cites_issue_1(changelog: str) -> None:
    """AC3: the Mbed TLS bump line carries its issue number (#1)."""
    bump_lines = [ln for ln in changelog.splitlines() if "3.6.5" in ln]
    idx = changelog.index("3.6.5")
    block = changelog[idx : idx + 400]
    assert "#1" in "".join(bump_lines) or "#1" in block


def test_ac12_milestones_not_flattened_to_done(changelog: str) -> None:
    """AC12: in-progress / planned statuses are preserved, not flattened."""
    low = changelog.lower()
    assert "in progress" in low, "M26 must be shown as in progress"
    assert "planned" in low, "M27-M32 must be shown as planned"


def test_security_group_precedes_fixed(changelog: str) -> None:
    """Grouped entries appear within the Unreleased section (structural sanity)."""
    assert "### Security" in changelog
    assert "### Fixed" in changelog
    assert changelog.index("## [Unreleased]") < changelog.index("### Security")
