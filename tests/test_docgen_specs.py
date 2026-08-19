from __future__ import annotations

import json
from pathlib import Path

import pytest

from netbox_cli.docgen.specs import load_specs

pytestmark = pytest.mark.suite_cli

ROOT = Path(__file__).resolve().parents[1]


def test_docgen_specs_cover_cli_and_tui_surfaces() -> None:
    specs = load_specs()

    surfaces = {spec.surface for spec in specs}
    titles = {spec.title for spec in specs}

    assert surfaces == {"cli", "tui"}
    assert "nbx cli tui --help" in titles
    assert "nbx demo cli tui --help" in titles
    assert "nbx tui logs --theme" in titles
    assert "nbx graphql --help" in titles
    assert "nbx demo graphql --help" in titles
    assert "nbx graphql tui --help" in titles
    assert "nbx graphql tui --theme" in titles
    assert "nbx demo graphql tui --help" in titles
    assert "nbx demo graphql tui --theme" in titles
    assert "nbx proxbox resources --json" in titles
    assert "nbx proxbox ops firewall/rules --json" in titles
    assert "nbx proxbox tui --theme" in titles


def test_docgen_demo_backed_specs_use_demo_prefix() -> None:
    specs = load_specs()

    demo_specs = [spec for spec in specs if spec.argv and spec.argv[0] == "demo"]
    non_demo_safe_false = [
        spec for spec in specs if not spec.safe and (not spec.argv or spec.argv[0] != "demo")
    ]

    assert demo_specs
    assert not non_demo_safe_false


def test_docgen_drops_timeout_prone_live_api_sections() -> None:
    specs = load_specs()

    sections = {spec.section for spec in specs}

    assert "Live API" not in sections
    assert "Cable Trace" not in sections


def test_generated_raw_call_help_captures_current_safety_options() -> None:
    raw_path = ROOT / "docs/generated/raw/014-cli-graphql-and-http-nbx-call-help.json"
    raw_capture = json.loads(raw_path.read_text(encoding="utf-8"))
    index = json.loads((ROOT / "docs/generated/raw/index.json").read_text(encoding="utf-8"))
    index_capture = next(run for run in index["runs"] if run["title"] == "nbx call --help")
    markdown = (ROOT / "docs/generated/nbx-command-capture.md").read_text(encoding="utf-8")
    markdown_pt = (ROOT / "docs/generated/nbx-command-capture.pt.md").read_text(encoding="utf-8")

    for capture in (raw_capture, index_capture):
        assert "--header" in capture["stdout_full"]
        assert "--confirm" in capture["stdout_full"]
        assert "--dry-run" in capture["stdout_full"]
    for rendered in (markdown, markdown_pt):
        call_section = rendered.split("#### nbx call --help", maxsplit=1)[1].split(
            "\n---\n", maxsplit=1
        )[0]
        assert "--header" in call_section
        assert "--confirm" in call_section
        assert "--dry-run" in call_section
