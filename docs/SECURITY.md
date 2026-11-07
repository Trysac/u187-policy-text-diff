# Security

## Threat Model
`policy-text-diff` processes arbitrary text inputs which may be user-supplied or from untrusted sources.

### Defended
- **Denial of Service**: Processing is capped by `max_chars = 2_000_000` to prevent memory exhaustion and quadratic complexity during `SequenceMatcher` execution.
- **Unbounded Output**: Rendered operations are truncated to 200 characters to prevent terminal flood/injection.
- **Input Sanitization**: Unicode normalization (NFC) is applied automatically.

### Not Defended
- **Non-text formats**: Processing binary data is out of scope and will yield undefined text output.
- **Semantic logic**: No analysis of legal or logical validity is performed.