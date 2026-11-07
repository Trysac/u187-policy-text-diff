"""Behavior tests for the public API of policy_text_diff."""

from __future__ import annotations

import pytest

import policy_text_diff


def test_normalize_trims_and_lowercases() -> None:
    assert policy_text_diff.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        policy_text_diff.normalize(value)


def test_version_is_semver() -> None:
    parts = policy_text_diff.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
