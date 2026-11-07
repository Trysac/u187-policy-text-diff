# Project record

## Objective
Provide a section-aware difference engine for privacy policies and terms of service that matches sections across renumbering and provides word-level change reports.

## Scope
- Typed Python library for policy diffing.
- Terminal-based CLI tool.
- Input normalization (whitespace, CRLF, NFC).

## Out of Scope
- Extraction from PDF/HTML/Binary formats.
- Legal interpretation.
- Automatic translation.
- Character-level diffs.

## Effort metrics
| Metric | Value |
|---|---|
| Tokens (input / output) | 617940 / 12641 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.1656 |

## Factory run u187 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | gemini-3.8-flash | yes | 4447 | 9092 | 0 | 0 | 0.0187 |
| fix-1 | gemini-3.8-flash | no | 11848 | 114 | 0 | 7633 | 0.0099 |
| fix-2 | gemini-3.8-flash | no | 60081 | 1216 | 0 | 290473 | 0.0714 |
| fix-3 | gemini-3.8-flash | no | 13071 | 430 | 0 | 8543 | 0.0121 |
| audit | gemini-3.1-flash-lite | no | 29271 | 289 | 0 | 20315 | 0.0083 |
| docs | gemini-3.1-flash-lite | no | 172258 | 1500 | 0 | 0 | 0.0453 |

Total: $0.1656. Prices: Anthropic list prices.
