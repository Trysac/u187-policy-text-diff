# policy-text-diff

![Build](https://github.com/factory/policy-text-diff/actions/workflows/ci.yml/badge.svg)

Section-aware diff of privacy policy and terms versions: matches headings across renumbering, performs word-level comparisons, flags review keywords, and renders to Markdown or JSON.

## Usage

```python
from policy_text_diff import diff_policies, render

old_policy = "# Data\nWe keep data for 30 days.\n"
new_policy = "# Data\nWe keep data for 90 days.\n"
diff = diff_policies(old_policy, new_policy)
print(render(diff, "markdown"))
```

## Public API

- `parse_sections(text: str, *, max_chars: int = 2_000_000) -> list[Section]`
- `diff_policies(old: str, new: str, *, keywords: Sequence[str] = DEFAULT_KEYWORDS, rename_threshold: float = 0.8, max_chars: int = 2_000_000) -> PolicyDiff`
- `render(diff: PolicyDiff, fmt: Literal["markdown", "json"]) -> str`
- `PolicyDiffError` (Exception)

## Why not <best-known alternative>?
Unlike standard `git diff` or character-level tools, this library understands document structure. It handles clause renumbering and reflowed text, ensuring significant policy changes are not buried in noise.

## Security
See [docs/SECURITY.md](docs/SECURITY.md).