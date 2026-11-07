# Architecture

`policy_text_diff` provides a structural, section-aware comparison engine for privacy policies and terms of service.

## Parsing
Documents are processed into `Section` instances via `parse_sections`. The parser recognizes Markdown ATX headings (`#` to `######`) and numbered clauses (e.g., `1.2.`). 

Keys are normalized by removing clause identifiers, stripping `#` marks, converting to NFC Unicode, and lowercasing. Duplicate keys are disambiguated by appending ` #N`.

## Matching and Diffing
1. Matching: Sections are matched first by normalized key. Unmatched sections are then paired by `difflib.SequenceMatcher` ratio if they exceed `rename_threshold` (default 0.8).
2. Operations: Word-level changes are calculated using `difflib` opcodes (ignoring equal segments). Added/removed sections are treated as bulk inserts/deletes.
3. Flags: The library scans inserted or replaced text for case-insensitive substrings from `DEFAULT_KEYWORDS`, providing non-legal review hints.