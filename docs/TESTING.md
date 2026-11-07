# Testing

## Running
```sh
uv run pytest --cov=policy_text_diff
```

## Coverage
Tests in `tests/test_policy_text_diff.py` cover:
- Acceptance criteria: section matching, clause renumbering, reflow handling.
- Edge cases: preamble handling, duplicate section keys, empty input.
- Error handling: limits on `max_chars`, invalid options.
- Rendering: verify output format parity for Markdown and JSON.

Coverage must remain at or above 80%.