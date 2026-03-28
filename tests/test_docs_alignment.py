from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.suite_sdk

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_mkdocs_and_package_metadata_point_to_netbox_sdk() -> None:
    mkdocs = _read("mkdocs.yml")
    pyproject = _read("pyproject.toml")

    assert "site_name: NetBox SDK" in mkdocs
    assert "https://github.com/emersonfelipesp/netbox-sdk" in mkdocs
    assert 'Documentation = "https://emersonfelipesp.github.io/netbox-sdk/"' in pyproject


def test_sdk_docs_cover_typed_api_and_supported_versions() -> None:
    sdk_index = _read("docs/sdk/index.md")
    typed_page = _read("docs/sdk/typed.md")
    making_requests = _read("docs/sdk/making-requests.md")
    mkdocs = _read("mkdocs.yml")

    assert "typed_api()" in sdk_index
    assert "4.5" in typed_page and "4.4" in typed_page and "4.3" in typed_page
    assert "TypedRequestValidationError" in making_requests
    assert "Typed API: sdk/typed.md" in mkdocs


def test_claude_guidance_mentions_versioned_typed_sdk() -> None:
    root_claude = _read("CLAUDE.md")
    sdk_claude = _read("netbox_sdk/CLAUDE.md")
    reference_claude = _read("netbox_sdk/reference/CLAUDE.md")

    assert "typed_api()" in root_claude
    assert "4.5" in root_claude and "4.4" in root_claude and "4.3" in root_claude
    assert "typed_api()" in sdk_claude
    assert "netbox-openapi-4.5.json" in reference_claude


def test_repo_docs_branding_uses_netbox_sdk_urls() -> None:
    files = [
        "README.md",
        "mkdocs.yml",
        "install.sh",
        "docs/generated/nbx-command-capture.md",
    ]
    combined = "\n".join(_read(path) for path in files)

    assert "github.com/emersonfelipesp/netbox-cli" not in combined
    assert "github.io/netbox-cli" not in combined
    assert "emersonfelipesp.com/netbox-cli" not in combined
    assert "github.com/emersonfelipesp/netbox-sdk" in combined


def test_generated_docs_nav_separates_cli_and_tui_outputs() -> None:
    mkdocs = _read("mkdocs.yml")
    cli_index = _read("docs/cli/index.md")
    tui_index = _read("docs/tui/index.md")
    tui_logs = _read("docs/tui/logs.md")
    tui_graphql = _read("docs/tui/graphql.md")
    tui_screenshots = _read("docs/tui/screenshots.md")
    cli_graphql = _read("docs/cli/graphql.md")

    assert "Captured Command Output:" in mkdocs
    assert "reference/cli/command-examples/index.md" in mkdocs
    assert "Launch Command Output:" in mkdocs
    assert "reference/tui/launch-examples/index.md" in mkdocs
    assert "GraphQL TUI: tui/graphql.md" in mkdocs
    assert "GraphQL TUI: reference/tui/launch-examples/graphql-tui.md" in mkdocs
    assert "GraphQL TUI: tui/screenshots-graphql.md" in mkdocs
    assert "../reference/cli/command-examples/index.md" in cli_index
    assert "../reference/tui/launch-examples/index.md" in tui_index
    assert "nbx graphql tui" in tui_index
    assert "nbx tui logs" in tui_logs
    assert "`--live`" not in tui_logs
    assert "nbx demo graphql tui" in tui_graphql
    assert "six Textual applications" in tui_screenshots
    assert "Interactive GraphQL explorer" in cli_graphql


def test_docs_workflow_still_deploys_pages_for_netbox_sdk_repo() -> None:
    workflow = _read(".github/workflows/docs.yml")
    mkdocs = _read("mkdocs.yml")

    assert "branches:\n      - main" in workflow
    assert "uv run mkdocs gh-deploy --force --clean --verbose" in workflow
    assert "site_url: https://emersonfelipesp.github.io/netbox-sdk/" in mkdocs
    assert "repo_url: https://github.com/emersonfelipesp/netbox-sdk" in mkdocs
