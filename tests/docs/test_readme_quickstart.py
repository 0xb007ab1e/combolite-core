"""README quickstart acceptance gates (FR4, FR5, AC8-AC10)."""

from __future__ import annotations

import docgates


def test_ac8_quickstart_steps_in_order(readme: str) -> None:
    """AC8: clone-with-submodules -> configure -> build -> ctest -> coverage, in order."""
    anchors = [
        "git clone --recurse-submodules",
        "cmake --preset core-cpu-debug",
        "cmake --build --preset core-cpu-debug",
        "ctest --preset core-cpu-debug",
        "CDB_COVERAGE",
    ]
    positions = []
    for a in anchors:
        idx = readme.find(a)
        assert idx != -1, f"README quickstart must contain: {a}"
        positions.append(idx)
    assert positions == sorted(positions), f"quickstart steps out of order: {positions}"


def test_ac9_configure_presets_exist(readme: str, cmake_presets: str) -> None:
    """AC9: every `cmake --preset X` names a real configurePreset."""
    presets = docgates.preset_names(cmake_presets)
    used = docgates.typed_preset_commands(readme)["configure"]
    assert used, "README must configure via a preset"
    missing = used - presets["configure"]
    assert not missing, f"invented configure preset(s): {missing}"


def test_ac9_build_presets_exist(readme: str, cmake_presets: str) -> None:
    """AC9: every `cmake --build --preset X` names a real buildPreset."""
    presets = docgates.preset_names(cmake_presets)
    used = docgates.typed_preset_commands(readme)["build"]
    assert used, "README must build via a preset"
    missing = used - presets["build"]
    assert not missing, f"invented build preset(s): {missing}"


def test_ac9_test_presets_exist(readme: str, cmake_presets: str) -> None:
    """AC9: every `ctest --preset X` names a real testPreset."""
    presets = docgates.preset_names(cmake_presets)
    used = docgates.typed_preset_commands(readme)["test"]
    assert used, "README must test via a preset"
    missing = used - presets["test"]
    assert not missing, f"invented test preset(s): {missing}"


def test_ac9_all_mentioned_presets_exist(readme: str, cmake_presets: str) -> None:
    """AC9: no preset-like token in the README is absent from CMakePresets.json."""
    presets = docgates.preset_names(cmake_presets)
    mentioned = docgates.mentioned_presets(readme)
    assert mentioned, "README references presets"
    missing = mentioned - presets["all"]
    assert not missing, f"README references non-existent preset(s): {missing}"


def test_ac9_canonical_quickstart_preset_is_core_cpu_debug(readme: str) -> None:
    """ADR-0001: the runnable path uses the toolchain-light core-cpu-debug preset."""
    assert "cmake --preset core-cpu-debug" in readme


def test_coverage_options_exist_in_build_system(readme: str, cmakelists: str) -> None:
    """AC9: the coverage build flags named in README exist in CMakeLists.txt."""
    assert "CDB_COVERAGE" in readme and "CDB_COVERAGE" in cmakelists
    assert "CDB_BUILD_TESTS" in cmakelists
    assert ("llvm-profdata" in readme and "llvm-cov" in readme) or (
        "cov.profdata" in readme
    )


def test_sr4_no_remote_exec_in_quickstart(readme: str) -> None:
    """SR4 / STRIDE-DoS: quickstart must not fetch-and-execute remote scripts."""
    low = readme.lower()
    for bad in ("curl | sh", "curl|sh", "wget | sh", "wget|sh", "| bash", "|bash"):
        assert bad not in low, f"quickstart must not pipe remote content to a shell: {bad}"


def test_ac10_prerequisites_documented(readme: str) -> None:
    """AC10: zero-undocumented-steps bar -- prerequisites (CMake>=3.20, C99) stated."""
    assert "CMake" in readme and "3.20" in readme
    low = readme.lower()
    assert "c99" in low
