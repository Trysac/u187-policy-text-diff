# policy-text-diff

[![PyPI version](https://img.shields.io/pypi/v/trysac-policy-text-diff)](https://pypi.org/project/trysac-policy-text-diff/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-policy-text-diff)](LICENSE)
[![CI](https://github.com/Trysac/u187-policy-text-diff/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u187-policy-text-diff/actions/workflows/ci.yml)

Section-aware diff of privacy policy and terms versions: headings matched across renumbering, word-level changes, review keyword flags, Markdown or JSON

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-policy-text-diff
# or
uv add trysac-policy-text-diff
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import policy_text_diff

# normalize() trims surrounding whitespace and lower-cases the text.
print(policy_text_diff.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    policy_text_diff.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
