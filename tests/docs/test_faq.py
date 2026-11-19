"""FAQ acceptance gates (FR3, AC4-AC7, SR2, SR3)."""

from __future__ import annotations

import docgates


def test_ac4_five_topic_areas_present(faq: str) -> None:
    """AC4: a distinct answer for each of the five FR3 topic areas."""
    low = faq.lower()
    assert "what is combolite-core" in low or "embeddable" in low
    assert "build it" in low or "toolchain" in low
    assert "data models" in low and "cmbql" in low
    assert "cryptography" in low
    assert "coverage" in low


def test_ac5_build_answer_names_submodule_clone_and_real_preset(
    faq: str, cmake_presets: str
) -> None:
    """AC5: build answer names submodule clone AND a real preset (exact strings)."""
    assert ("--recurse-submodules" in faq) or (
        "git submodule update --init --recursive" in faq
    )
    presets = docgates.preset_names(cmake_presets)
    referenced = docgates.mentioned_presets(faq)
    assert referenced, "FAQ build answer must name at least one preset"
    assert referenced & presets["all"], "FAQ must name a real CMakePresets.json preset"


def test_ac6_crypto_answer_lists_required_primitives(faq: str) -> None:
    """AC6: AEAD, signing, hash, MAC, and KDF primitives are all listed."""
    required = [
        "AES-256-GCM",
        "ChaCha20-Poly1305",
        "ECDSA",
        "SHA-256",
        "HMAC",
        "HKDF",
    ]
    for term in required:
        assert term in faq, f"FAQ crypto answer must list {term}"


def test_ac6_crypto_attributed_to_vendored_mbedtls(faq: str) -> None:
    """AC6 / SR3: crypto is attributed to the vendored Mbed TLS library."""
    low = faq.lower()
    assert "vendored" in low and "mbed tls" in low


def test_ac6_identity_key_scheme_matches_source(faq: str, crypto_source: str) -> None:
    """ADR-0003: FAQ states ECDSA P-256/secp256r1 exactly as the code implements."""
    assert "MBEDTLS_ECP_DP_SECP256R1" in crypto_source
    low = faq.lower()
    assert "ecdsa" in low
    assert "p-256" in low or "secp256r1" in low


def test_ac6_crypto_claims_do_not_contradict_spec(faq: str, spec_security: str) -> None:
    """AC6: the AEAD/hash/KDF set named in the FAQ also appears in spec 12."""
    for term in ("AES-256-GCM", "ChaCha20-Poly1305", "HKDF", "HMAC", "SHA-256"):
        assert term in spec_security, f"spec 12 should establish {term}"
        assert term in faq


def test_sr2_honest_fixed_nonce_caveat_discoverable(faq: str) -> None:
    """SR2: the key-wrap fixed-nonce limitation is kept discoverable, not hidden."""
    low = faq.lower()
    assert "fixed" in low and "nonce" in low, "fixed-nonce caveat must be present"
    assert ("rfc 3394" in low) or ("m27" in low) or ("known issues" in low), (
        "the caveat must point to the remediation / Known Issues"
    )


def test_sr2_no_overstated_confidentiality(faq: str) -> None:
    """SR2: FAQ must not claim there are no crypto issues / perfect confidentiality."""
    low = faq.lower()
    for forbidden in (
        "no known crypto",
        "no known security issues",
        "unconditionally secure",
        "cannot be broken",
    ):
        assert forbidden not in low


def test_ac7_coverage_posture_cites_issue_18_without_fabricated_percent(faq: str) -> None:
    """AC7: coverage answer is interim, cites #18, and fabricates no percentage."""
    assert "#18" in faq
    low = faq.lower()
    assert (
        "defensive error branch" in low
        or "fault-injection" in low
        or "fault injection" in low
    )
    section = _coverage_section(faq)
    assert not docgates.coverage_percentages(section), (
        "no fabricated coverage percentage is allowed in the FAQ coverage answer"
    )


def test_ac12_provisioned_operators_not_claimed_shipped(faq: str) -> None:
    """AC12: executor operators still pending are not asserted as done."""
    low = faq.lower()
    assert "cmbql" in low
    assert "pending" in low or "not yet implemented" in low or "stubbed" in low


def _coverage_section(faq: str) -> str:
    marker = "test coverage posture"
    i = faq.lower().find(marker)
    return faq[i:] if i != -1 else faq
