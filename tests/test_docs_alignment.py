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

    assert "site_name: netbox-sdk" in mkdocs
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
