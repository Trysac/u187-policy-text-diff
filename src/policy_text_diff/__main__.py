"""CLI entry point for policy_text_diff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from policy_text_diff import PolicyDiffError, diff_policies, render


def main(argv: list[str] | None = None) -> int:
    """Run CLI for policy_text_diff."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="policy-text-diff",
        description="Section-aware diff of privacy policy and terms versions.",
    )
    parser.add_argument("old_file", help="Path to original policy file")
    parser.add_argument("new_file", help="Path to updated policy file")
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Body similarity threshold for heading renames (default: 0.8)",
    )

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code != 0 else 0

    try:
        old_path = Path(args.old_file)
        new_path = Path(args.new_file)
        if not old_path.is_file():
            sys.stderr.write(f"Error: old file not found: {args.old_file}\n")
            return 2
        if not new_path.is_file():
            sys.stderr.write(f"Error: new file not found: {args.new_file}\n")
            return 2

        old_text = old_path.read_text(encoding="utf-8-sig")
        new_text = new_path.read_text(encoding="utf-8-sig")

        diff = diff_policies(old_text, new_text, rename_threshold=args.threshold)
        output = render(diff, args.format)
        sys.stdout.write(output)
        if not output.endswith("\n"):
            sys.stdout.write("\n")
        return 1 if diff.changes else 0
    except PolicyDiffError as e:
        sys.stderr.write(f"Error: {e}\n")
        return 2
    except Exception as e:
        sys.stderr.write(f"Unexpected error: {e}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
