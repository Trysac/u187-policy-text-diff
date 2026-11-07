"""Tests for policy_text_diff conforming to all acceptance items and edge cases."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from policy_text_diff import (
    PolicyDiffError,
    WordOp,
    diff_policies,
    parse_sections,
    render,
)
from policy_text_diff.__main__ import main


def test_acceptance_item_1() -> None:
    old = "# Data\nWe keep data for 30 days.\n# Contact\nEmail us.\n"
    new = "# Data\nWe keep data for 90 days.\n# Contact\nEmail us.\n# Sharing\nWe share data with third parties.\n"
    diff = diff_policies(old, new)
    kinds = [c.kind for c in diff.changes]
    keys = [c.key for c in diff.changes]
    assert kinds == ["modified", "added"]
    assert keys == ["data", "sharing"]
    assert diff.changes[0].word_ops == (WordOp("replace", "30", "90"),)
    assert diff.changes[0].flags == ()
    assert diff.changes[1].flags == ("share", "third part")


def test_acceptance_item_2_whitespace_reflow() -> None:
    old = "# Data\nWe keep\ndata."
    new = "# Data\nWe keep data."
    diff = diff_policies(old, new)
    assert diff.changes == ()


def test_acceptance_item_3_clause_renumbering() -> None:
    old = "1. Intro\nHello.\n2. Data\nKeep 30 days.\n"
    new = "1. Intro\nHello.\n2. Cookies\nWe use cookies.\n3. Data\nKeep 30 days.\n"
    diff = diff_policies(old, new)
    assert len(diff.changes) == 1
    change = diff.changes[0]
    assert change.kind == "added"
    assert change.key == "cookies"


def test_acceptance_item_4_rename_threshold() -> None:
    # Heading rename with identical body gives one 'modified' change with heading_old and heading_new and word_ops == ()
    old_same = "# Data\nWe store records securely in encrypted databases."
    new_same = "# Your data\nWe store records securely in encrypted databases."
    diff_same = diff_policies(old_same, new_same, rename_threshold=0.8)
    assert len(diff_same.changes) == 1
    ch = diff_same.changes[0]
    assert ch.kind == "modified"
    assert ch.heading_old == "Data"
    assert ch.heading_new == "Your data"
    assert ch.word_ops == ()

    # Heading rename with similarity < 0.8 gives removed + added
    old_diff = "# Data\nWe store records securely in encrypted databases for 10 years."
    new_diff = "# Information\nAll user logs are deleted immediately upon logout."
    diff_diff = diff_policies(old_diff, new_diff, rename_threshold=0.8)
    kinds = [c.kind for c in diff_diff.changes]
    assert kinds == ["added", "removed"]


def test_acceptance_item_5_preamble_and_duplicates() -> None:
    text = "Preamble text here.\n# FAQ\nFirst FAQ content.\n# FAQ\nSecond FAQ content.\n"
    secs = parse_sections(text)
    assert [s.key for s in secs] == ["(preamble)", "faq", "faq #2"]
    assert secs[0].heading is None
    assert secs[0].body == "Preamble text here."
    assert secs[1].heading == "FAQ"
    assert secs[2].heading == "FAQ"


def test_acceptance_item_6_render_markdown() -> None:
    old = "# Data\nWe keep data for 30 days.\n# Contact\nEmail us.\n"
    new = "# Data\nWe keep data for 90 days.\n# Contact\nEmail us.\n# Sharing\nWe share data with third parties.\n"
    diff = diff_policies(old, new)
    md = render(diff, "markdown")
    expected = (
        "# Policy changes: 1 modified, 1 added, 0 removed\n\n"
        "### modified: Data\n"
        '- replace: "30" -> "90"\n\n'
        "### added: Sharing\n"
        '- insert: "We share data with third parties."\n'
        "Flags: share, third part\n\n"
        "Review aid only, not legal advice.\n"
    )
    assert md == expected


def test_acceptance_item_7_limits_and_flags() -> None:
    # 2_000_001 raises input_too_large
    with pytest.raises(PolicyDiffError) as exc_info:
        diff_policies("a" * 2_000_001, "b")
    assert exc_info.value.code == "input_too_large"

    with pytest.raises(PolicyDiffError) as exc_info2:
        parse_sections("a" * 2_000_001)
    assert exc_info2.value.code == "input_too_large"

    # 2_000_000 accepted
    diff_empty = diff_policies("" * 2_000_000, "")
    assert diff_empty.changes == ()

    # keywords=('',) raises invalid_option
    with pytest.raises(PolicyDiffError) as exc_kw:
        diff_policies("old", "new", keywords=("",))
    assert exc_kw.value.code == "invalid_option"

    # keywords=() produces no flags
    old = "# Info\nHello"
    new = "# Info\nHello we share data with third parties and retain biometric children"
    diff_no_kw = diff_policies(old, new, keywords=())
    assert diff_no_kw.changes[0].flags == ()

    # Truncate over 200 characters followed by '...'
    long_text = "word " * 50
    assert len(long_text) > 200
    diff_long = diff_policies("", f"# Section\n{long_text}")
    rendered = render(diff_long, "markdown")
    expected_trunc = long_text.strip()[:200] + "..."
    assert f'- insert: "{expected_trunc}"' in rendered


def test_acceptance_item_8_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    old_file = tmp_path / "old.md"
    new_file = tmp_path / "new.md"

    old_file.write_text("# Data\nWe keep data for 30 days.\n", encoding="utf-8")
    new_file.write_text("# Data\nWe keep data for 90 days.\n", encoding="utf-8")

    code = main([str(old_file), str(new_file), "--format", "json"])
    captured = capsys.readouterr()
    assert code == 1
    data = json.loads(captured.out)
    assert "changes" in data
    assert len(data["changes"]) == 1
    assert data["changes"][0]["kind"] == "modified"

    # Identical files -> exit code 0
    code_same = main([str(old_file), str(old_file), "--format", "json"])
    assert code_same == 0

    # Non-existent file -> exit code 2
    code_err = main(["non_existent.md", str(new_file)])
    assert code_err == 2


def test_cli_errors_and_bom(tmp_path: Path) -> None:
    f1 = tmp_path / "f1.md"
    f2 = tmp_path / "f2.md"
    # UTF-8 with BOM
    f1.write_bytes("\ufeff# Data\nOld text".encode("utf-8"))
    f2.write_bytes("\ufeff# Data\nNew text".encode("utf-8"))
    code = main([str(f1), str(f2), "--format", "markdown"])
    assert code == 1

    # Invalid threshold option
    code_bad_thresh = main([str(f1), str(f2), "--threshold", "2.5"])
    assert code_bad_thresh == 2

    # Argparse help or error
    assert main(["--unknown-flag"]) == 2


def test_edge_cases() -> None:
    # Empty old -> everything added
    diff = diff_policies("", "# Intro\nWelcome")
    assert len(diff.changes) == 1
    assert diff.changes[0].kind == "added"

    # CRLF line endings
    crlf_old = "# Terms\r\nLine 1\r\nLine 2"
    crlf_new = "# Terms\r\nLine 1\r\nLine 2 updated"
    diff_crlf = diff_policies(crlf_old, crlf_new)
    assert len(diff_crlf.changes) == 1
    assert diff_crlf.changes[0].kind == "modified"

    # Heading without body
    diff_nobd = diff_policies("# Terms\n# Contact", "# Terms\n# Contact\nReach out")
    assert len(diff_nobd.changes) == 1
    assert diff_nobd.changes[0].key == "contact"

    # HTML input treated as plain text
    html_old = "<h1>Privacy</h1><p>We do not track.</p>"
    html_new = "<h1>Privacy</h1><p>We do track.</p>"
    diff_html = diff_policies(html_old, html_new)
    assert len(diff_html.changes) == 1
    assert diff_html.changes[0].key == "(preamble)"

    # Removed section
    diff_rem = diff_policies("# Removed\nBye", "")
    assert len(diff_rem.changes) == 1
    assert diff_rem.changes[0].kind == "removed"
    assert diff_rem.changes[0].word_ops[0].op == "delete"
    assert diff_rem.changes[0].word_ops[0].old == "Bye"

    # Render with unknown format
    with pytest.raises(PolicyDiffError) as exc_render:
        render(diff_rem, "xml")  # type: ignore
    assert exc_render.value.code == "invalid_option"

    # Check PolicyDiffError str
    err = PolicyDiffError("invalid_option", "bad")
    assert str(err) == "[invalid_option] bad"

    # Heading rename with identical body without word ops formatting in render
    diff_renamed = diff_policies("# Data\nHello", "# Info\nHello", rename_threshold=0.8)
    rendered_renamed = render(diff_renamed, "markdown")
    assert "### modified: Info" in rendered_renamed
