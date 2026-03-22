"""Tests for docgen_capture path resolution."""

import unittest
from pathlib import Path

from netbox_cli import docgen_capture


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
