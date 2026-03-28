"""Tests for docgen_capture path resolution."""

import unittest
from pathlib import Path

import pytest

from netbox_cli import docgen_capture

pytestmark = pytest.mark.suite_cli


class ArgvMarkdownOutputTests(unittest.TestCase):
    def test_disabled_returns_copy(self) -> None:
        argv = ["demo", "dcim", "devices", "list"]
        self.assertEqual(
            docgen_capture.argv_with_markdown_output(argv, enabled=False),
            argv,
        )

    def test_appends_for_demo_list(self) -> None:
        self.assertEqual(
            docgen_capture.argv_with_markdown_output(
                ["demo", "dcim", "devices", "list"], enabled=True
            ),
            ["demo", "dcim", "devices", "list", "--markdown"],
        )

    def test_appends_for_default_profile_list(self) -> None:
        self.assertEqual(
            docgen_capture.argv_with_markdown_output(["dcim", "devices", "list"], enabled=True),
            ["dcim", "devices", "list", "--markdown"],
        )

    def test_appends_before_trailing_options(self) -> None:
        self.assertEqual(
            docgen_capture.argv_with_markdown_output(
                ["demo", "dcim", "interfaces", "get", "--id", "1", "--trace"],
                enabled=True,
            ),
            ["demo", "dcim", "interfaces", "get", "--id", "1", "--trace", "--markdown"],
        )

    def test_skips_when_json_set(self) -> None:
        argv = ["call", "GET", "/api/dcim/sites/", "--json"]
        self.assertEqual(
            docgen_capture.argv_with_markdown_output(argv, enabled=True),
            argv,
        )

    def test_appends_for_call_get(self) -> None:
        self.assertEqual(
            docgen_capture.argv_with_markdown_output(["call", "GET", "/api/status/"], enabled=True),
            ["call", "GET", "/api/status/", "--markdown"],
        )

    def test_skips_help(self) -> None:
        argv = ["dcim", "devices", "list", "--help"]
        self.assertEqual(
            docgen_capture.argv_with_markdown_output(argv, enabled=True),
            argv,
        )

    def test_skips_groups_command(self) -> None:
        argv = ["groups"]
        self.assertEqual(
            docgen_capture.argv_with_markdown_output(argv, enabled=True),
            argv,
        )


class ResolveCapturePathsTests(unittest.TestCase):
    def test_defaults_under_repo_docs(self) -> None:
        out, raw = docgen_capture.resolve_capture_paths(None, None)
        self.assertTrue(out.name.endswith(".md"))
        self.assertEqual(raw.name, "raw")
        self.assertEqual(raw.parent, out.parent)

    def test_custom_output_infers_raw_sibling(self) -> None:
        out = Path("/tmp/nbx-cap/capture.md")
        o, r = docgen_capture.resolve_capture_paths(out, None)
        self.assertEqual(o, out)
        self.assertEqual(r, Path("/tmp/nbx-cap/raw"))

    def test_both_explicit(self) -> None:
        out = Path("/tmp/nbx-cap/capture.md")
        raw = Path("/tmp/nbx-cap/raw-custom")
        o, r = docgen_capture.resolve_capture_paths(out, raw)
        self.assertEqual(o, out)
        self.assertEqual(r, raw)


if __name__ == "__main__":
    unittest.main()
