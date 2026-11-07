# Use section-aware matching with fallback to word similarity for renumbered clauses

Status: accepted (generated, pending human review)

## Context

Privacy policies frequently renumber clauses (e.g., adding clause 2 shifts 2 to 3) or change section titles slightly while keeping the body intact. Traditional line-based diff tools produce massive false positives on paragraph reflow and renumbering.

## Decision

Implement parse_sections with heading normalization that strips clause numbers. Match sections by key first, and for unmatched sections fall back to SequenceMatcher word ratio with a 0.8 rename threshold. Word diffs are computed on normalized tokens.

## Consequences

Minor reflows and clause renumberings do not register as false positive changes. Word-level changes highlight exact contractual alterations with relevant risk keyword flags.
