"""Section-aware diff of privacy policy and terms versions."""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import Literal

__all__ = [
    "DEFAULT_KEYWORDS",
    "PolicyDiff",
    "PolicyDiffError",
    "Section",
    "SectionChange",
    "WordOp",
    "__version__",
    "diff_policies",
    "parse_sections",
    "render",
]

__version__ = "0.1.0"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

DEFAULT_KEYWORDS: tuple[str, ...] = (
    "sell",
    "share",
    "third part",
    "transfer",
    "retain",
    "retention",
    "arbitration",
    "waive",
    "liability",
    "biometric",
    "children",
    "location",
)


class PolicyDiffError(Exception):
    """Base error for policy text diff operations."""

    def __init__(self, code: Literal["input_too_large", "invalid_option"], message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


@dataclass(frozen=True)
class Section:
    """A parsed document section with a normalized key, heading, and body text."""

    key: str
    heading: str | None
    body: str


@dataclass(frozen=True)
class WordOp:
    """A word-level operation inside a section diff."""

    op: Literal["insert", "delete", "replace"]
    old: str
    new: str


@dataclass(frozen=True)
class SectionChange:
    """A change detected within or across sections."""

    kind: Literal["added", "removed", "modified"]
    key: str
    heading_old: str | None
    heading_new: str | None
    word_ops: tuple[WordOp, ...]
    flags: tuple[str, ...]


@dataclass(frozen=True)
class PolicyDiff:
    """The set of changes across two policy versions."""

    changes: tuple[SectionChange, ...]


_ATX_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_CLAUSE_RE = re.compile(r"^(\d+(?:\.\d+)*\.?)\s+(\S.*)$", re.DOTALL)


def _normalize_nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _normalize_heading_to_key(heading_text: str) -> str:
    # Strip Markdown ATX leading '#' marks if any remain
    cleaned = heading_text.lstrip("# ").strip()
    # Check for numbered clause prefix like '1.2.' or '1.' or '1. Intro'
    clause_match = _CLAUSE_RE.match(cleaned)
    if clause_match:
        cleaned = clause_match.group(2).strip()
    # Normalize NFC, lowercase, collapse whitespace
    cleaned = _normalize_nfc(cleaned).lower()
    words = cleaned.split()
    return " ".join(words)


def _split_into_words(text: str) -> list[str]:
    normalized = _normalize_nfc(text)
    return normalized.split()


def _truncate_op_text(text: str, max_chars: int = 200) -> str:
    if len(text) > max_chars:
        return text[:max_chars] + "..."
    return text


def parse_sections(text: str, *, max_chars: int = 2_000_000) -> list[Section]:
    """Parse text into sections separated by Markdown ATX headings or numbered clauses."""
    if len(text) > max_chars:
        raise PolicyDiffError(
            "input_too_large",
            f"Input text exceeds maximum allowed length of {max_chars} characters.",
        )

    normalized_text = _normalize_nfc(text)
    # Normalize CRLF to LF
    lines = normalized_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if len(lines) == 1 and lines[0] == "":
        return []

    sections_raw: list[tuple[str | None, list[str]]] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    for line in lines:
        is_heading = False
        heading_val: str | None = None

        atx_match = _ATX_RE.match(line)
        if atx_match:
            is_heading = True
            heading_val = atx_match.group(2).strip()
        else:
            clause_match = _CLAUSE_RE.match(line)
            if clause_match:
                is_heading = True
                heading_val = line.strip()

        if is_heading:
            if current_heading is not None or current_lines:
                sections_raw.append((current_heading, current_lines))
            current_heading = heading_val
            current_lines = []
        else:
            current_lines.append(line)

    if current_heading is not None or current_lines:
        sections_raw.append((current_heading, current_lines))

    # Convert raw sections into Section instances with unique keys
    key_counts: dict[str, int] = {}
    sections: list[Section] = []

    for heading, blines in sections_raw:
        body = "\n".join(blines)
        if heading is None:
            base_key = "(preamble)"
        else:
            base_key = _normalize_heading_to_key(heading)
            if not base_key:
                base_key = "(untitled)"

        count = key_counts.get(base_key, 0) + 1
        key_counts[base_key] = count
        key = base_key if count == 1 else f"{base_key} #{count}"

        sections.append(Section(key=key, heading=heading, body=body))

    return sections


def _compute_flags(text: str, keywords: Sequence[str]) -> tuple[str, ...]:
    norm_text = text.lower()
    flags: list[str] = []
    for kw in keywords:
        if kw.lower() in norm_text:
            flags.append(kw)
    return tuple(flags)


def _diff_words(old_words: list[str], new_words: list[str]) -> list[WordOp]:
    matcher = SequenceMatcher(None, old_words, new_words, autojunk=False)
    ops: list[WordOp] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old_span = " ".join(old_words[i1:i2])
        new_span = " ".join(new_words[j1:j2])
        if tag == "replace":
            ops.append(WordOp("replace", old_span, new_span))
        elif tag == "insert":
            ops.append(WordOp("insert", "", new_span))
        elif tag == "delete":
            ops.append(WordOp("delete", old_span, ""))
    return ops


def diff_policies(
    old: str,
    new: str,
    *,
    keywords: Sequence[str] = DEFAULT_KEYWORDS,
    rename_threshold: float = 0.8,
    max_chars: int = 2_000_000,
) -> PolicyDiff:
    """Diff two policy texts by section and word."""
    if len(old) > max_chars or len(new) > max_chars:
        raise PolicyDiffError(
            "input_too_large",
            f"Input text exceeds maximum allowed length of {max_chars} characters.",
        )

    for kw in keywords:
        if not kw:
            raise PolicyDiffError(
                "invalid_option",
                "Keywords cannot contain empty strings.",
            )

    if not (0.0 <= rename_threshold <= 1.0):
        raise PolicyDiffError(
            "invalid_option",
            f"rename_threshold must be between 0.0 and 1.0, got {rename_threshold}",
        )

    old_sections = parse_sections(old, max_chars=max_chars)
    new_sections = parse_sections(new, max_chars=max_chars)

    # Phase 1: match by exact key
    old_by_key: dict[str, list[tuple[int, Section]]] = {}
    for idx, s in enumerate(old_sections):
        old_by_key.setdefault(s.key, []).append((idx, s))

    new_by_key: dict[str, list[tuple[int, Section]]] = {}
    for idx, s in enumerate(new_sections):
        new_by_key.setdefault(s.key, []).append((idx, s))

    matched_pairs: dict[int, int] = {}  # new_idx -> old_idx
    matched_old: set[int] = set()
    matched_new: set[int] = set()

    for key, new_list in new_by_key.items():
        if key in old_by_key:
            old_list = old_by_key[key]
            pairs = min(len(new_list), len(old_list))
            for p in range(pairs):
                n_idx, _ = new_list[p]
                o_idx, _ = old_list[p]
                matched_pairs[n_idx] = o_idx
                matched_old.add(o_idx)
                matched_new.add(n_idx)

    # Phase 2: match unmatched new sections to unmatched old sections by highest difflib ratio
    unmatched_new_indices = [i for i in range(len(new_sections)) if i not in matched_new]
    unmatched_old_indices = [i for i in range(len(old_sections)) if i not in matched_old]

    for n_idx in unmatched_new_indices:
        new_sec = new_sections[n_idx]
        new_words = _split_into_words(new_sec.body)
        best_ratio = -1.0
        best_old_idx: int | None = None

        for o_idx in unmatched_old_indices:
            if o_idx in matched_old:
                continue
            old_sec = old_sections[o_idx]
            old_words = _split_into_words(old_sec.body)
            if not old_words and not new_words:
                ratio = 1.0
            else:
                matcher = SequenceMatcher(None, old_words, new_words, autojunk=False)
                ratio = matcher.ratio()

            # ties: earlier old section (strictly greater required to overwrite)
            if ratio >= rename_threshold and ratio > best_ratio:
                best_ratio = ratio
                best_old_idx = o_idx

        if best_old_idx is not None:
            matched_pairs[n_idx] = best_old_idx
            matched_old.add(best_old_idx)
            matched_new.add(n_idx)

    # Phase 3: Build changes list in order:
    # 1) sections in new-document order
    # 2) removed sections in old order
    changes: list[SectionChange] = []

    for n_idx, new_sec in enumerate(new_sections):
        new_words = _split_into_words(new_sec.body)
        if n_idx in matched_pairs:
            o_idx = matched_pairs[n_idx]
            old_sec = old_sections[o_idx]
            old_words = _split_into_words(old_sec.body)

            # Check if bodies or headings differ:
            # If matched by key, heading difference due to clause renumbering
            # does not constitute a rename.
            is_renamed = (old_sec.key != new_sec.key) and (old_sec.heading != new_sec.heading)
            words_differ = old_words != new_words

            if not words_differ and not is_renamed:
                continue  # unchanged

            word_ops = tuple(_diff_words(old_words, new_words))

            # Flags: keywords found in inserted or replacing text
            inserted_or_replaced_text = " ".join(
                op.new for op in word_ops if op.op in ("insert", "replace")
            )
            flags = _compute_flags(inserted_or_replaced_text, keywords)

            changes.append(
                SectionChange(
                    kind="modified",
                    key=new_sec.key,
                    heading_old=old_sec.heading,
                    heading_new=new_sec.heading,
                    word_ops=word_ops,
                    flags=flags,
                )
            )
        else:
            # Added section
            body_str = " ".join(new_words)
            word_ops = (WordOp("insert", "", body_str),) if body_str else ()
            flags = _compute_flags(body_str, keywords)
            changes.append(
                SectionChange(
                    kind="added",
                    key=new_sec.key,
                    heading_old=None,
                    heading_new=new_sec.heading,
                    word_ops=word_ops,
                    flags=flags,
                )
            )

    # Unmatched old sections are removed sections
    for o_idx, old_sec in enumerate(old_sections):
        if o_idx not in matched_old:
            old_words = _split_into_words(old_sec.body)
            body_str = " ".join(old_words)
            word_ops = (WordOp("delete", body_str, ""),) if body_str else ()
            changes.append(
                SectionChange(
                    kind="removed",
                    key=old_sec.key,
                    heading_old=old_sec.heading,
                    heading_new=None,
                    word_ops=word_ops,
                    flags=(),
                )
            )

    return PolicyDiff(changes=tuple(changes))


def render(diff: PolicyDiff, fmt: Literal["markdown", "json"]) -> str:
    """Render PolicyDiff to Markdown or JSON."""
    if fmt == "json":
        data = asdict(diff)
        return json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2)

    if fmt == "markdown":
        mod_count = sum(1 for c in diff.changes if c.kind == "modified")
        add_count = sum(1 for c in diff.changes if c.kind == "added")
        rem_count = sum(1 for c in diff.changes if c.kind == "removed")

        lines: list[str] = [
            f"# Policy changes: {mod_count} modified, {add_count} added, {rem_count} removed",
            "",
        ]

        for change in diff.changes:
            heading_label = change.heading_new or change.heading_old or "(preamble)"
            lines.append(f"### {change.kind}: {heading_label}")

            for op in change.word_ops:
                old_trunc = _truncate_op_text(op.old)
                new_trunc = _truncate_op_text(op.new)
                if op.op == "insert":
                    lines.append(f'- insert: "{new_trunc}"')
                elif op.op == "delete":
                    lines.append(f'- delete: "{old_trunc}"')
                elif op.op == "replace":
                    lines.append(f'- replace: "{old_trunc}" -> "{new_trunc}"')

            if change.flags:
                lines.append(f"Flags: {', '.join(change.flags)}")

            lines.append("")

        lines.append("Review aid only, not legal advice.")
        lines.append("")
        return "\n".join(lines)

    raise PolicyDiffError("invalid_option", f"Unsupported format: {fmt}")
