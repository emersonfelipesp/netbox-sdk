#!/usr/bin/env python3
"""Shim: use ``nbx docs generate-capture`` or import from ``netbox_cli.docgen_capture``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate nbx CLI capture documentation.")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--raw-dir", type=Path, default=None)
    md = parser.add_mutually_exclusive_group()
    md.add_argument(
        "--markdown",
        dest="markdown_output",
        action="store_true",
        help="Append --markdown to list/get/call captures (default).",
    )
    md.add_argument(
        "--no-markdown",
        dest="markdown_output",
        action="store_false",
        help="Do not append --markdown (keep Rich table output in captures).",
    )
    parser.set_defaults(markdown_output=True)
    args = parser.parse_args()

    from netbox_cli.docgen_capture import generate_command_capture_docs, resolve_capture_paths

    try:
        out, raw = resolve_capture_paths(args.output, args.raw_dir)
    except FileNotFoundError as exc:
        print(exc, file=sys.stderr)
        return 1
    return generate_command_capture_docs(
        output=out,
        raw_dir=raw,
        markdown_output=args.markdown_output,
    )


if __name__ == "__main__":
    raise SystemExit(main())
