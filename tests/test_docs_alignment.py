from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml


class _NavLoader(yaml.SafeLoader):
    """SafeLoader extended to silently ignore !!python/name: and similar tags.

    mkdocs.yml uses !!python/name:material.extensions.emoji.twemoji which
    UnsafeLoader tries to import at parse time.  The test only needs the nav
    structure so a loader that maps those tags to plain strings is sufficient.
    """


_NavLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/",
    lambda loader, tag_suffix, node: (
        loader.construct_scalar(node)  # type: ignore[arg-type]
        if isinstance(node, yaml.ScalarNode)
        else None
    ),
)

pytestmark = pytest.mark.suite_sdk

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _pyproject_version() -> str:
    data = tomllib.loads(_read("pyproject.toml"))
    return str(data["project"]["version"])


_DOC_VERSION_SNIPPETS = (
    "docs/snippets/package-version.txt",
    "docs/snippets/documented-release-en.md",
    "docs/snippets/documented-release-pt.md",
    "docs/snippets/pip-pinned-sdk.txt",
    "docs/snippets/pip-pinned-cli.txt",
    "docs/snippets/pip-pinned-tui.txt",
    "docs/snippets/pip-pinned-all.txt",
    "docs/snippets/uv-pinned-cli.txt",
)


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


def _nav_markdown_paths(node: Any) -> list[str]:
    paths: list[str] = []
    if isinstance(node, list):
        for entry in node:
            paths.extend(_nav_markdown_paths(entry))
    elif isinstance(node, dict):
        for _key, value in node.items():
            if isinstance(value, str) and value.endswith(".md"):
                paths.append(value)
            else:
                paths.extend(_nav_markdown_paths(value))
    return paths


def test_mkdocs_i18n_en_default_and_pt_locale() -> None:
    mkdocs_text = _read("mkdocs.yml")
    assert "language: en" in mkdocs_text
    assert "i18n:" in mkdocs_text
    assert "locale: en" in mkdocs_text
    assert "default: true" in mkdocs_text
    assert "locale: pt" in mkdocs_text
    assert "Português (Brasil)" in mkdocs_text
    assert "fallback_to_default: false" in mkdocs_text


def test_nav_markdown_pages_have_portuguese_siblings() -> None:
    mkdocs = yaml.load(_read("mkdocs.yml"), Loader=_NavLoader)
    docs_dir = REPO_ROOT / "docs"
    for rel in _nav_markdown_paths(mkdocs["nav"]):
        pt = rel[:-3] + ".pt.md" if rel.endswith(".md") else rel
        assert (docs_dir / pt).is_file(), f"missing Portuguese mirror: docs/{pt}"


def test_docs_package_version_snippet_matches_pyproject() -> None:
    expected = _pyproject_version()
    assert (REPO_ROOT / "docs/snippets/package-version.txt").read_text(
        encoding="utf-8"
    ).strip() == expected


def test_mkdocs_extra_package_version_matches_pyproject() -> None:
    mkdocs = yaml.load(_read("mkdocs.yml"), Loader=_NavLoader)
    extra = mkdocs.get("extra") or {}
    assert extra.get("package_version") == _pyproject_version()


def test_docs_version_snippets_reference_pyproject_version() -> None:
    version = _pyproject_version()
    for rel in _DOC_VERSION_SNIPPETS:
        text = _read(rel)
        assert version in text, f"{rel} must include project version {version!r}"
