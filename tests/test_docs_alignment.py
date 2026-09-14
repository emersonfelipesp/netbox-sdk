from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml
from packaging.version import Version

from netbox_sdk.versioning import SUPPORTED_NETBOX_VERSIONS
from scripts import build_metadata
from scripts.release_policy import is_public_pypi_version


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


_DOCUMENTED_RELEASE_VERSION_FIELDS = {
    "docs/snippets/documented-release-en.md": {
        "candidate": r"\*\*netbox-sdk (?P<version>[^*\s]+) source candidate\*\*",
        "published": r"default PyPI index is \*\*(?P<version>[^*\s]+)\*\*",
        "install": r"use `==(?P<version>[^`\s]+)`",
    },
    "docs/snippets/documented-release-pt.md": {
        "candidate": (
            r"\*\*candidato de código-fonte netbox-sdk "
            r"(?P<version>[^*\s]+)\*\*"
        ),
        "published": r"índice PyPI padrão é a \*\*(?P<version>[^*\s]+)\*\*",
        "install": r"use `==(?P<version>[^`\s]+)`",
    },
}

_PINNED_INSTALL_SNIPPETS = {
    "docs/snippets/pip-pinned-sdk.txt": "pip install netbox-sdk=={version}",
    "docs/snippets/pip-pinned-cli.txt": "pip install 'netbox-sdk[cli]=={version}'",
    "docs/snippets/pip-pinned-tui.txt": "pip install 'netbox-sdk[tui]=={version}'",
    "docs/snippets/pip-pinned-all.txt": "pip install 'netbox-sdk[all]=={version}'",
    "docs/snippets/uv-pinned-cli.txt": ("uv tool install --force 'netbox-sdk[cli]=={version}'"),
}


def _documented_version_field(path: str, field: str) -> str:
    pattern = _DOCUMENTED_RELEASE_VERSION_FIELDS[path][field]
    match = re.search(pattern, _read(path))
    assert match is not None, f"{path} must expose an exact {field} version field"
    return match.group("version")


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
    # Derived from the registry, not a hardcoded list: a hardcoded list keeps
    # passing after a new line is registered, which is exactly how the 4.7 docs
    # ended up contradicting themselves (the page documented 4.7 lower down while
    # its own support inventory still stopped at 4.6).
    for line in SUPPORTED_NETBOX_VERSIONS:
        assert line in typed_page, f"docs/sdk/typed.md does not mention release line {line}"
    assert "TypedRequestValidationError" in making_requests
    assert "Typed API: sdk/typed.md" in mkdocs


def test_localized_support_inventories_cover_every_registered_line() -> None:
    """Both locales must advertise every registered line, preview included.

    Granularity is deliberately "the line is named somewhere on the page": it
    catches a page that never mentions a line at all — the failure that let the
    4.7 inventories go stale — but it cannot tell a support claim from a passing
    reference. Keep illustrative pages out of the list rather than trying to make
    this assertion smarter.
    """
    pages = (
        "docs/index.md",
        "docs/index.pt.md",
        "docs/sdk/typed.md",
        "docs/sdk/typed.pt.md",
        "docs/sdk/making-requests.md",
        "docs/sdk/making-requests.pt.md",
        "docs/getting-started/installation.md",
        "docs/getting-started/installation.pt.md",
        "docs/getting-started/quickstart.md",
        "docs/getting-started/quickstart.pt.md",
        # Support/compatibility inventories. These make an explicit claim about
        # which lines are supported, so every registered line must appear.
        # Pages that merely *illustrate* a version (docs/sdk/schema.md picks one
        # line as an example) are deliberately excluded — forcing them to name
        # every line would make the guard noise rather than signal.
        "CERTIFICATION.md",
        "docs/certification.md",
        "docs/certification.pt.md",
        "docs/cli/dynamic-commands.md",
        "docs/cli/dynamic-commands.pt.md",
        "docs/mock-api/index.md",
        "docs/mock-api/index.pt.md",
        "docs/sdk/index.md",
        "docs/sdk/index.pt.md",
        "docs/sdk/branching.md",
        "docs/sdk/branching.pt.md",
        "docs/mock-api/pytest-integration.md",
        "docs/mock-api/pytest-integration.pt.md",
    )
    for page in pages:
        text = _read(page)
        for line in SUPPORTED_NETBOX_VERSIONS:
            assert line in text, f"{page} omits release line {line}"


def test_generated_module_inventories_list_every_registered_line() -> None:
    """The typed pages must name each line's generated modules."""
    for page in ("docs/sdk/typed.md", "docs/sdk/typed.pt.md"):
        text = _read(page)
        for line in SUPPORTED_NETBOX_VERSIONS:
            suffix = line.replace(".", "_")
            assert f"netbox_sdk.models.v{suffix}" in text, f"{page} omits models.v{suffix}"
            assert f"netbox_sdk.typed_versions.v{suffix}" in text, (
                f"{page} omits typed_versions.v{suffix}"
            )


def test_claude_guidance_mentions_versioned_typed_sdk() -> None:
    root_claude = _read("CLAUDE.md")
    sdk_claude = _read("netbox_sdk/CLAUDE.md")
    reference_claude = _read("netbox_sdk/reference/CLAUDE.md")

    assert "typed_api()" in root_claude
    for line in SUPPORTED_NETBOX_VERSIONS:
        assert line in root_claude, f"CLAUDE.md does not mention release line {line}"
    assert "typed_api()" in sdk_claude
    for line in SUPPORTED_NETBOX_VERSIONS:
        assert f"netbox-openapi-{line}.json" in reference_claude, (
            f"netbox_sdk/reference/CLAUDE.md omits netbox-openapi-{line}.json"
        )


def test_agent_guidance_keeps_generic_bridge_contract_mirrored() -> None:
    sdk_guides = (_read("netbox_sdk/CLAUDE.md"), _read("netbox_sdk/AGENTS.md"))
    test_guides = (_read("tests/CLAUDE.md"), _read("tests/AGENTS.md"))

    for guide in sdk_guides:
        assert "Descriptor version 1 is generic" in guide
        assert "lossless integer semantics" in guide
        assert "normalized UTC month boundaries" in guide
        assert "plugin repositories own their operation payload snapshots" in guide
    for guide in test_guides:
        assert "test_plugin_bridge.py" in guide
        assert "test_mcp_plugin_bridge.py" in guide
        assert "neutral descriptor-v1 sample" in guide
        assert "canonical plugin payload snapshots remain producer-owned" in guide


def test_sdk_bridge_sample_remains_neutral_and_producer_independent() -> None:
    fixture_path = REPO_ROOT / "tests/fixtures/plugin_bridge_v1_sample.json"
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert payload["plugin"] == "example"
    assert [tool["name"] for tool in payload["tools"]] == [
        "list_tasks",
        "create_task",
    ]
    assert {tool["path"] for tool in payload["tools"]} == {"tasks/"}
    encoded = json.dumps(payload, sort_keys=True).casefold()
    for producer_contract in (
        "proxbox",
        "proxmox",
        "sync/schedule",
        "sync_stages",
        "sync_types",
        "netbox_endpoint_ids",
        "proxmox_endpoint_ids",
    ):
        assert producer_contract not in encoded
    assert not (REPO_ROOT / "tests/fixtures/proxbox_bridge_v1.json").exists()


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
    for path in _DOCUMENTED_RELEASE_VERSION_FIELDS:
        assert _documented_version_field(path, "candidate") == version, (
            f"{path} candidate field must equal project version {version!r}"
        )


def test_default_index_install_snippets_reference_published_final() -> None:
    published = _read("docs/snippets/published-package-version.txt").strip()
    assert is_public_pypi_version(published), (
        "the default-index install version must be a public final or post-release"
    )
    for path in _DOCUMENTED_RELEASE_VERSION_FIELDS:
        for field in ("published", "install"):
            assert _documented_version_field(path, field) == published, (
                f"{path} {field} field must equal published final {published!r}"
            )
    for path, template in _PINNED_INSTALL_SNIPPETS.items():
        expected = template.format(version=published)
        assert _read(path).strip() == expected, (
            f"{path} must contain only the exact published install command {expected!r}"
        )


def _live_ci_netbox_targets() -> tuple[str, ...]:
    workflow = yaml.load(_read(".github/workflows/test.yml"), Loader=yaml.BaseLoader)
    assert isinstance(workflow, dict), "the test workflow must be a YAML mapping"
    jobs = workflow.get("jobs")
    assert isinstance(jobs, dict), "the test workflow must define jobs"
    live_job = jobs.get("test-live-netbox")
    assert isinstance(live_job, dict), "the test workflow must define test-live-netbox"
    strategy = live_job.get("strategy")
    assert isinstance(strategy, dict), "test-live-netbox must define a strategy"
    matrix = strategy.get("matrix")
    assert isinstance(matrix, dict), "test-live-netbox must define a matrix"
    targets = list(matrix.get("netbox-version") or [])
    assert targets, "test-live-netbox must define a non-empty netbox-version matrix"
    # ``include`` entries create additional live jobs, so an include-only target
    # is as real as a base-matrix one and must be part of the effective set.
    included = matrix.get("include") or []
    assert isinstance(included, list), "a test-live-netbox matrix include must be a list"
    for entry in included:
        assert isinstance(entry, dict), "every matrix include entry must be a mapping"
        extra = entry.get("netbox-version")
        if extra is not None and extra not in targets:
            targets.append(extra)
    assert all(isinstance(target, str) for target in targets), (
        "every test-live-netbox target must be a string"
    )
    assert len(targets) == len(set(targets)), (
        "the test-live-netbox matrix must not contain duplicate targets"
    )
    return tuple(
        sorted(targets, key=lambda target: Version(target.removeprefix("v")), reverse=True)
    )


def _table_after_heading(markdown: str, heading: str) -> list[str]:
    lines = markdown.splitlines()
    heading_indexes = [index for index, line in enumerate(lines) if line == heading]
    assert len(heading_indexes) == 1, f"expected exactly one {heading!r} heading"
    index = heading_indexes[0] + 1
    while index < len(lines) and not lines[index]:
        index += 1
    rows: list[str] = []
    while index < len(lines) and lines[index].startswith("|"):
        rows.append(lines[index])
        index += 1
    assert rows, f"{heading!r} must be followed by a Markdown table"
    return rows


def test_certification_matrices_track_the_source_candidate_and_ci_contract() -> None:
    version = _pyproject_version()
    typed_lines = ", ".join(f"`{line}`" for line in SUPPORTED_NETBOX_VERSIONS)
    live_targets = ", ".join(f"`{target}`" for target in _live_ci_netbox_targets())
    expected_tables = {
        "docs/certification.md": (
            "## Compatibility matrix",
            [
                "| `netbox-sdk` release | Python | Typed NetBox API lines | "
                "Live CI NetBox targets |",
                "| --- | --- | --- | --- |",
                f"| `{version}` source candidate | `>=3.11,<3.14` | {typed_lines} | "
                f"{live_targets}; one bundled-schema job per release line |",
            ],
        ),
        "docs/certification.pt.md": (
            "## Matriz de compatibilidade",
            [
                "| Release `netbox-sdk` | Python | Linhas de API NetBox tipadas | "
                "Alvos live NetBox na CI |",
                "| --- | --- | --- | --- |",
                f"| candidato de código-fonte `{version}` | `>=3.11,<3.14` | "
                f"{typed_lines} | {live_targets}; um job com schema integrado por "
                "linha de release |",
            ],
        ),
    }
    for path, (heading, expected) in expected_tables.items():
        rows = _table_after_heading(_read(path), heading)
        assert rows == expected, (
            f"{path} must contain exactly one current compatibility row derived from CI"
        )


def test_all_release_version_surfaces_match_pyproject() -> None:
    version = _pyproject_version()
    published = _read("docs/snippets/published-package-version.txt").strip()
    init_match = re.search(r'^__version__ = "([^"]+)"$', _read("netbox_sdk/__init__.py"), re.M)
    assert init_match is not None
    assert init_match.group(1) == version

    metadata = json.loads(_read("metadata.json"))
    assert metadata["release"] == version

    lock = tomllib.loads(_read("uv.lock"))
    project_rows = [row for row in lock["package"] if row["name"] == "netbox-sdk"]
    assert len(project_rows) == 1
    assert project_rows[0]["version"] == version

    assert f"**Current project version**: `{version}`" in _read("llms.txt")

    readme = _read("README.md")
    readme_lines = readme.splitlines()
    assert f"pip install 'netbox-sdk[all]=={published}'" in readme_lines
    if is_public_pypi_version(version):
        assert re.search(r"git push gitea v\S+rc\S*", readme)
        assert f"git push gitea v{version}" not in readme_lines
        assert not any(line.startswith(f"git tag -a v{version} ") for line in readme_lines)
        assert f"gh release create v{version} \\" in readme_lines
        assert "--target <canonical-main-sha>" in readme
        final_refs_path = f"/tmp/netbox-sdk-v{version}-tag-refs"
        assert (
            f"git ls-remote origin refs/tags/v{version} > {final_refs_path} && \\" in readme_lines
        )
        assert f"test ! -s {final_refs_path} && \\" in readme_lines
    else:
        assert f'git tag -a v{version} -m "Release v{version}"' in readme_lines
        assert f"git push gitea v{version}" in readme_lines
    template_refs_path = "/tmp/netbox-sdk-vX.Y.Z-tag-refs"
    assert f"git ls-remote origin refs/tags/vX.Y.Z > {template_refs_path} && \\" in readme_lines
    assert f"test ! -s {template_refs_path} && \\" in readme_lines
    assert "gh release create vX.Y.Z \\" in readme_lines
    assert '  --title "netbox-sdk vX.Y.Z" \\' in readme_lines


def _load_workflow(path: str) -> dict[str, Any]:
    workflow = yaml.load(_read(path), Loader=yaml.BaseLoader)
    assert isinstance(workflow, dict)
    return workflow


def _assert_job_checks_out_full_history(path: str, job_name: str) -> None:
    workflow = _load_workflow(path)
    job = workflow["jobs"][job_name]
    checkout_steps = [
        step
        for step in job["steps"]
        if isinstance(step, dict) and str(step.get("uses", "")).startswith("actions/checkout@")
    ]
    assert len(checkout_steps) == 1, f"{path}:{job_name} must have one checkout step"
    assert checkout_steps[0].get("with", {}).get("fetch-depth") == "0", (
        f"{path}:{job_name} must fetch immutable release history"
    )


@pytest.mark.parametrize(
    ("path", "job_name"),
    [
        (".gitea/workflows/ci.yml", "full-tests"),
        (".github/workflows/test.yml", "test-sdk"),
        (".github/workflows/test.yml", "test-all-mock"),
        (".github/workflows/test.yml", "test-all-mock-main"),
        (".github/workflows/test.yml", "test-live-netbox"),
        (".github/workflows/main-post-merge.yml", "validate-main"),
        (".github/workflows/publish-testpypi.yml", "release-preflight"),
        (".github/workflows/publish-testpypi.yml", "prepare-release"),
        (".github/workflows/publish-testpypi.yml", "publish-testpypi"),
        (".github/workflows/publish-testpypi.yml", "validate-testpypi"),
        (".github/workflows/publish-testpypi.yml", "publish-pypi"),
    ],
)
def test_release_sensitive_jobs_checkout_full_history(path: str, job_name: str) -> None:
    _assert_job_checks_out_full_history(path, job_name)


def test_registry_upload_is_gated_by_source_preflight() -> None:
    workflow = _load_workflow(".github/workflows/publish-testpypi.yml")
    jobs = workflow["jobs"]
    assert jobs["prepare-release"]["needs"] == "release-preflight"
    assert jobs["smoke-built-wheel"]["needs"] == "prepare-release"
    assert jobs["publish-testpypi"]["needs"] == ["prepare-release", "smoke-built-wheel"]
    preflight_commands = "\n".join(
        str(step.get("run", ""))
        for step in jobs["release-preflight"]["steps"]
        if isinstance(step, dict)
    )
    assert "uv run pytest -v --tb=short -p no:randomly" in preflight_commands
    assert "twine upload" not in preflight_commands

    workflow_text = _read(".github/workflows/publish-testpypi.yml")
    assert "--skip-existing" not in workflow_text
    assert "scripts/prepare_testpypi_upload.py" in workflow_text
    assert "scripts/release_policy.py" in workflow_text
    assert "--require-published" in workflow_text
    assert "https://git.nmulti.cloud/emersonfelipesp/netbox-sdk.git" in workflow_text
    assert "refs/remotes/gitea/release-policy-main" in workflow_text
    assert "refs/remotes/origin/release-policy-main" not in workflow_text
    assert "refs/release-policy/gitea-v0.0.10" in workflow_text
    assert _IMMUTABLE_V0_0_10_TAG_OBJECT in workflow_text
    assert _IMMUTABLE_V0_0_10_COMMIT in workflow_text
    assert "needs.prepare-release.outputs.publish_pypi == 'true'" in workflow_text
    assert "!contains(github.ref, 'rc')" not in workflow_text
    assert '"netbox-sdk[all] @ ${WHEEL_URL}"' in workflow_text


def test_release_workflow_authorizes_rc_pushes_and_official_release_events() -> None:
    workflow = _load_workflow(".github/workflows/publish-testpypi.yml")
    triggers = workflow["on"]
    assert triggers["push"]["tags"] == ["v*rc*"]
    assert triggers["release"]["types"] == ["published"]
    assert "workflow_dispatch" not in triggers
    assert "github.event_name == 'release'" in str(workflow["jobs"]["publish-pypi"]["if"])


def _assert_mirror_credentials_are_step_scoped(writer: dict[str, Any]) -> None:
    prepare_step, push_step, _cleanup_step = writer["steps"]
    assert prepare_step["env"]["GITEA_SOURCE_TOKEN"] == ("${{ secrets.SOURCE_MIRROR_TOKEN }}")
    assert prepare_step["env"]["GIT_CONFIG_GLOBAL"] == "/dev/null"
    assert prepare_step["env"]["GIT_CONFIG_NOSYSTEM"] == "1"
    assert "GH_TOKEN" not in prepare_step["env"]
    assert push_step["env"]["GH_TOKEN"] == "${{ secrets.GH_MIRROR_TOKEN }}"
    assert push_step["env"]["GIT_CONFIG_GLOBAL"] == "/dev/null"
    assert push_step["env"]["GIT_CONFIG_NOSYSTEM"] == "1"
    assert "GITEA_SOURCE_TOKEN" not in push_step["env"]


def _assert_mirror_pushes_the_exact_commit(writer: dict[str, Any]) -> None:
    prepare_step, push_step, _cleanup_step = writer["steps"]
    assert "latest_sha" in prepare_step["run"]
    assert "scripts/build_metadata.py" not in prepare_step["run"]
    assert "git commit" not in prepare_step["run"]
    assert "for attempt in 1 2 3" not in push_step["run"]
    assert "ls-remote github" not in push_step["run"]
    assert 'python3 "$MIRROR_ROOT/scripts/mirror_github.py"' in push_step["run"]
    assert '--repository "$MIRROR_ROOT"' in push_step["run"]
    assert "--remote github" in push_step["run"]
    assert "--branch main" in push_step["run"]
    assert "--historical-tip" not in push_step["run"]
    assert 'git -C "$MIRROR_ROOT" push' not in push_step["run"]


def test_metadata_mirror_preserves_provenance_with_scoped_credentials() -> None:
    workflow = _load_workflow(".gitea/workflows/mirror-github.yml")
    triggers = workflow["on"]
    assert triggers["push"] == {"branches": ["main"]}
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"]["cancel-in-progress"] == "false"
    assert set(workflow["jobs"]) == {"mirror"}

    writer = workflow["jobs"]["mirror"]
    assert "needs" not in writer
    assert writer["runs-on"] == "mirror-host"
    assert writer["permissions"] == {"contents": "read"}
    _assert_mirror_credentials_are_step_scoped(writer)
    _assert_mirror_pushes_the_exact_commit(writer)

    workflow_text = _read(".gitea/workflows/mirror-github.yml")
    assert workflow_text.count("${{ secrets.SOURCE_MIRROR_TOKEN }}") == 1
    assert workflow_text.count("${{ secrets.GH_MIRROR_TOKEN }}") == 1
    assert "METADATA_WRITE_TOKEN" not in workflow_text
    assert "generate-metadata" not in workflow_text
    assert "chore: refresh metadata provenance" not in workflow_text


def test_metadata_source_records_version_and_content_identity() -> None:
    metadata = json.loads(_read("metadata.json"))
    assert metadata["source"]["version"] == _pyproject_version()
    assert re.fullmatch(r"[0-9a-f]{64}", metadata["source"]["content_id"])


def test_metadata_only_push_has_a_dedicated_validation_gate() -> None:
    workflow = _load_workflow(".github/workflows/publish-metadata.yml")
    triggers = workflow["on"]
    assert triggers["push"] == {"branches": ["main"], "paths": ["metadata.json"]}
    assert "workflow_dispatch" not in triggers
    assert workflow["permissions"] == {"contents": "read"}

    validator = workflow["jobs"]["validate-metadata"]
    assert "github.ref == 'refs/heads/main'" in str(validator["if"])
    assert validator["permissions"] == {"contents": "read"}
    checkout = validator["steps"][0]
    assert checkout["with"]["fetch-depth"] == "0"
    assert checkout["with"]["persist-credentials"] == "false"
    validation_command = validator["steps"][-1]["run"]
    assert validation_command == "python scripts/build_metadata.py --verify"
    assert "METADATA_WRITE_TOKEN" not in str(workflow)
    assert "github.token" not in str(workflow)


@pytest.mark.parametrize(
    "path",
    [
        ".github/workflows/test.yml",
        ".github/workflows/lint.yml",
        ".github/workflows/security.yml",
        ".github/workflows/certification.yml",
        ".github/workflows/docs.yml",
        ".github/workflows/main-post-merge.yml",
    ],
)
def test_metadata_changes_run_regular_github_workflows(path: str) -> None:
    workflow = _load_workflow(path)
    assert "paths-ignore" not in workflow["on"]["push"]


def test_github_workflows_do_not_push_to_main() -> None:
    for path in sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml")):
        workflow_text = path.read_text(encoding="utf-8")
        assert "git push" not in workflow_text, f"{path.name} must not push GitHub main"
        assert "HEAD:refs/heads/main" not in workflow_text, (
            f"{path.name} must not update GitHub main"
        )


def test_django_model_builds_uploads_only_three_overall_releases() -> None:
    workflow = _load_workflow(".github/workflows/django-model-builds.yml")
    assert workflow["permissions"] == {"contents": "read"}
    steps = workflow["jobs"]["build"]["steps"]
    checkout_step = steps[0]
    assert str(checkout_step["uses"]).startswith("actions/checkout@")
    assert checkout_step["with"]["persist-credentials"] == "false"
    install_step = next(
        step for step in steps if step.get("name") == "Install the checked-out netbox-sdk tool"
    )
    assert install_step["run"] == "uv tool install --force '.[cli]'"
    release_step = next(step for step in steps if step.get("id") == "releases")
    assert "releases?per_page=3" in release_step["run"]
    assert "--paginate" not in release_step["run"]
    upload_step = next(step for step in steps if step.get("name") == "Upload model graphs")
    assert str(upload_step["uses"]).startswith("actions/upload-artifact@")
    assert upload_step["with"]["if-no-files-found"] == "error"


def test_docs_deployments_are_serialized() -> None:
    workflow = _load_workflow(".github/workflows/docs.yml")
    assert workflow["concurrency"]["cancel-in-progress"] == "false"


@pytest.mark.parametrize(
    "path",
    [
        ".github/workflows/publish-testpypi.yml",
        ".github/workflows/publish-metadata.yml",
        ".github/workflows/django-model-builds.yml",
        ".gitea/workflows/mirror-github.yml",
    ],
)
def test_sensitive_workflows_use_immutable_actions(path: str) -> None:
    workflow = _load_workflow(path)
    for job_name, job in workflow["jobs"].items():
        for step in job["steps"]:
            if not isinstance(step, dict) or "uses" not in step:
                continue
            action = str(step["uses"])
            assert re.fullmatch(r"[^@]+@[0-9a-f]{40}", action), (
                f"{path}:{job_name} action must use an immutable full SHA: {action}"
            )
            if action.startswith("astral-sh/setup-uv@"):
                assert step.get("with", {}).get("version") == "0.11.28", (
                    f"{path}:{job_name} must pin the uv binary version"
                )


def test_release_workflow_uses_locked_publish_tools() -> None:

    dependency_groups = tomllib.loads(_read("pyproject.toml"))["dependency-groups"]
    assert dependency_groups["publish"] == [
        "build==1.5.0",
        "packaging==26.0",
        "setuptools==83.0.0",
        "twine==6.2.0",
        "wheel==0.46.2",
    ]
    workflow_text = _read(".github/workflows/publish-testpypi.yml")
    assert "uv sync --only-group publish --locked" in workflow_text
    assert "--group publish" not in workflow_text.replace("--only-group publish", "")
    assert "python -m build --no-isolation" in workflow_text
    assert "--with twine" not in workflow_text
    assert "--with build" not in workflow_text


def test_validated_artifacts_are_captured_before_downstream_smoke_install() -> None:
    workflow = _load_workflow(".github/workflows/publish-testpypi.yml")
    jobs = workflow["jobs"]
    prepare_steps = jobs["prepare-release"]["steps"]
    names = [step.get("name") for step in prepare_steps]
    capture_index = names.index("Capture the validated dist artifacts")
    assert names[capture_index - 1] == "Validate the closed local artifact set"
    assert all("pip install" not in str(step.get("run", "")) for step in prepare_steps)
    capture = prepare_steps[capture_index]
    assert capture["with"]["path"].splitlines() == ["dist/*.whl", "dist/*.tar.gz"]

    smoke_commands = "\n".join(
        str(step.get("run", ""))
        for step in jobs["smoke-built-wheel"]["steps"]
        if isinstance(step, dict)
    )
    assert "pip install" in smoke_commands
    assert "${wheels[0]}[branching]" in smoke_commands


def test_public_pypi_upload_immediately_revalidates_release_authorization() -> None:
    workflow = _load_workflow(".github/workflows/publish-testpypi.yml")
    steps = workflow["jobs"]["publish-pypi"]["steps"]
    upload_index = next(
        index for index, step in enumerate(steps) if step.get("name") == "Upload to PyPI"
    )
    selection = steps[upload_index - 1]
    assert selection["name"] == "Select exact missing PyPI artifacts"
    assert selection["id"] == "pypi-registry"
    assert "--registry pypi" in str(selection["run"])
    assert "pypi-registry.outputs.upload_required == 'true'" in str(steps[upload_index]["if"])

    recheck = steps[upload_index - 2]
    assert recheck["name"] == "Revalidate canonical Gitea and the exact TestPyPI artifact set"
    commands = str(recheck["run"])
    assert "git fetch --no-tags" in commands
    assert "scripts/release_policy.py" in commands
    assert "scripts/prepare_testpypi_upload.py" in commands
    assert "--require-published" in commands
    assert "--upload-all" not in commands
    upload_commands = str(steps[upload_index]["run"])
    assert "--verify-upload-dir" in upload_commands
    assert "pypi-upload/*" in str(steps[upload_index]["run"])
    assert "dist/*" not in str(steps[upload_index]["run"])

    final_check = steps[upload_index + 1]
    assert final_check["name"] == "Verify exact published PyPI artifact set"
    final_commands = str(final_check["run"])
    assert "for attempt in 1 2 3 4 5 6" in final_commands
    assert "--registry pypi" in final_commands
    assert "--require-published" in final_commands


def test_testpypi_upload_revalidates_manifest_in_the_twine_step() -> None:
    workflow = _load_workflow(".github/workflows/publish-testpypi.yml")
    steps = workflow["jobs"]["publish-testpypi"]["steps"]
    upload = next(step for step in steps if step.get("name") == "Upload to TestPyPI")
    commands = str(upload["run"])
    assert "--verify-upload-dir" in commands
    assert commands.index("--verify-upload-dir") < commands.index("twine upload")


def test_release_policy_inputs_route_to_the_full_github_suite() -> None:
    workflow = _load_workflow(".github/workflows/test.yml")
    filters = workflow["jobs"]["changes"]["steps"][1]["with"]["filters"]
    assert "scripts/build_metadata.py" in filters
    assert "scripts/release_policy.py" in filters
    assert ".github/workflows/publish-metadata.yml" in filters
    assert ".gitea/workflows/mirror-github.yml" in filters
    assert "tests/test_release_policy.py" in filters


def test_package_integration_docs_separate_pypi_final_from_source_candidate() -> None:
    for path in (
        "docs/developer/package-integration.md",
        "docs/developer/package-integration.pt.md",
    ):
        text = _read(path)
        assert "docs/snippets/published-package-version.txt" in text
        assert "docs/snippets/package-version.txt" in text
        assert "TestPyPI" in text


_IMMUTABLE_V0_0_10_COMMIT = "3bcc86481f60f0f2d6fb1913c42d1561f5d5b77e"
_IMMUTABLE_V0_0_10_TAG_OBJECT = "e104bdd554ac2becf7abd38b238d8fb5509651f4"


def _run_git(*args: str) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
            text=True,
        )
    except FileNotFoundError:
        return None


def _git_blob_text(commit: str, path: str) -> str | None:
    entry = _run_git("ls-tree", commit, "--", path)
    if entry is None or entry.returncode != 0:
        return None
    lines = entry.stdout.splitlines()
    if len(lines) != 1:
        return None
    try:
        metadata, recorded_path = lines[0].split("\t", 1)
        _mode, object_type, object_id = metadata.split()
    except ValueError:
        return None
    if object_type != "blob" or recorded_path != path:
        return None
    blob = _run_git("cat-file", "blob", object_id)
    return blob.stdout if blob is not None and blob.returncode == 0 else None


def test_published_v0_0_10_is_in_candidate_ancestry() -> None:
    git_probe = _run_git("rev-parse", "--show-toplevel")
    if (
        git_probe is None
        or git_probe.returncode != 0
        or Path(git_probe.stdout.strip()).resolve() != REPO_ROOT.resolve()
    ):
        pytest.skip("Git metadata is unavailable in this source archive")

    tag_type = _run_git("cat-file", "-t", "v0.0.10")
    tag_object = _run_git("rev-parse", "--verify", "v0.0.10")
    tag = _run_git("rev-parse", "--verify", "v0.0.10^{}")
    assert tag_type is not None and tag_type.returncode == 0
    assert tag_type.stdout.strip() == "tag", "v0.0.10 must remain an annotated tag"
    assert tag_object is not None and tag_object.returncode == 0
    assert tag_object.stdout.strip() == _IMMUTABLE_V0_0_10_TAG_OBJECT, (
        "v0.0.10 must remain the originally published annotated tag object"
    )
    assert tag is not None and tag.returncode == 0, (
        "the immutable v0.0.10 release tag must be available"
    )
    assert tag.stdout.strip() == _IMMUTABLE_V0_0_10_COMMIT, (
        "v0.0.10 must continue to peel to its originally published commit"
    )

    ancestor = _run_git("merge-base", "--is-ancestor", _IMMUTABLE_V0_0_10_COMMIT, "HEAD")
    assert ancestor is not None
    if ancestor.returncode == 0:
        parents = _run_git("rev-list", "--parents", "HEAD")
        assert parents is not None and parents.returncode == 0
        integration_merges = [
            line.split()
            for line in parents.stdout.splitlines()
            if len(line.split()) == 3 and line.split()[2] == _IMMUTABLE_V0_0_10_COMMIT
        ]
        assert integration_merges, (
            "v0.0.10 must enter the candidate through a two-parent merge; "
            "squash and rebase integration are forbidden"
        )
        return

    merge_path_result = _run_git("rev-parse", "--git-path", "MERGE_HEAD")
    assert merge_path_result is not None and merge_path_result.returncode == 0
    merge_path = Path(merge_path_result.stdout.strip())
    if not merge_path.is_absolute():
        merge_path = REPO_ROOT / merge_path
    merge_heads = merge_path.read_text(encoding="utf-8").splitlines()
    assert len(merge_heads) == 1, "the pending integration must have exactly two parents"
    pending_parent = _run_git("rev-parse", "--verify", f"{merge_heads[0]}^{{}}")
    assert pending_parent is not None and pending_parent.returncode == 0, (
        "v0.0.10 must be an ancestor of the candidate"
    )
    assert pending_parent.stdout.strip() == _IMMUTABLE_V0_0_10_COMMIT, (
        "an uncommitted reconciliation must have v0.0.10 as its second parent"
    )


def _metadata_source_mismatch(commit: str, release: str) -> str | None:
    """Return why ``commit`` fails to describe the candidate tree, or ``None``.

    Content identity is authoritative. When the informational commit remains
    available, this additional predicate requires it to carry the same project
    version and tree as the candidate outside the metadata file itself.
    """
    source_pyproject = _git_blob_text(commit, "pyproject.toml")
    if source_pyproject is None:
        return f"metadata source.commit {commit} does not expose pyproject.toml"
    source_version = tomllib.loads(source_pyproject)["project"]["version"]
    if source_version != release:
        return (
            "metadata must name a commit containing the same project version; "
            f"{commit} declares {source_version!r} but the metadata declares {release!r}"
        )
    source_diff = _run_git(
        "diff",
        "--name-only",
        commit,
        "HEAD",
        "--",
        ".",
        ":(exclude)metadata.json",
    )
    if source_diff is None or source_diff.returncode != 0:
        return f"the candidate tree could not be compared against {commit}"
    drifted = source_diff.stdout.strip()
    if drifted:
        return (
            "metadata source.commit must represent the candidate tree outside "
            f"metadata.json; {commit} differs in: {drifted.splitlines()[0]}"
        )
    return None


def test_metadata_has_traceable_source_commit() -> None:
    metadata = json.loads(_read("metadata.json"))
    commit = metadata["source"]["commit"]
    project_version = _pyproject_version()
    assert metadata["release"] == project_version
    assert metadata["source"]["version"] == project_version
    assert re.fullmatch(r"[0-9a-f]{40}", commit), "metadata source.commit must be a full SHA"

    git_probe = _run_git("rev-parse", "--show-toplevel")
    if (
        git_probe is None
        or git_probe.returncode != 0
        or Path(git_probe.stdout.strip()).resolve() != REPO_ROOT.resolve()
    ):
        return

    expected_content_id = build_metadata.content_id_for_tree("HEAD")
    candidate_changes = _run_git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        "--",
        ".",
        ":(exclude)metadata.json",
    )
    assert candidate_changes is not None and candidate_changes.returncode == 0
    if candidate_changes.stdout.strip():
        # Local patch verification runs before a commit exists. The generated
        # candidate identity must match that future tree. A committed CI checkout
        # takes the HEAD path above, which is the published contract.
        expected_content_id = build_metadata.content_id_for_worktree()
    assert metadata["source"]["content_id"] == expected_content_id

    source_type = _run_git("cat-file", "-t", commit)
    assert source_type is not None
    if source_type.returncode != 0:
        return
    assert source_type.stdout.strip() == "commit", (
        "metadata source.commit must identify a commit object in repository history"
    )
    reason = _metadata_source_mismatch(commit, metadata["release"])
    assert reason is None, reason


def test_metadata_verification_allows_an_unavailable_informational_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metadata = json.loads(_read("metadata.json"))
    metadata["source"]["content_id"] = build_metadata.content_id_for_worktree()
    metadata["source"]["commit"] = "f" * 40
    output = tmp_path / "metadata.json"
    output.write_text(json.dumps(metadata), encoding="utf-8")
    monkeypatch.setattr(build_metadata, "OUTPUT", output)
    monkeypatch.setattr(build_metadata, "_resolved_object_type", lambda _commit: None)

    build_metadata.verify_metadata(use_worktree=True)


def test_metadata_verification_rejects_a_changed_content_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metadata = json.loads(_read("metadata.json"))
    metadata["source"]["content_id"] = "0" * 64
    output = tmp_path / "metadata.json"
    output.write_text(json.dumps(metadata), encoding="utf-8")
    monkeypatch.setattr(build_metadata, "OUTPUT", output)

    with pytest.raises(RuntimeError, match="does not match the repository content"):
        build_metadata.verify_metadata(use_worktree=True)


def _worktree_metadata() -> dict[str, Any]:
    metadata = json.loads(_read("metadata.json"))
    metadata["source"]["content_id"] = build_metadata.content_id_for_worktree()
    metadata["source"]["commit"] = "f" * 40
    return metadata


def _write_metadata_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    metadata: dict[str, Any],
) -> None:
    output = tmp_path / "metadata.json"
    output.write_text(json.dumps(metadata), encoding="utf-8")
    monkeypatch.setattr(build_metadata, "OUTPUT", output)
    monkeypatch.setattr(build_metadata, "_resolved_object_type", lambda _commit: None)


@pytest.mark.parametrize("container", ["top", "source"])
def test_metadata_verification_rejects_unknown_fields(
    container: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metadata = _worktree_metadata()
    target = metadata if container == "top" else metadata["source"]
    target["unexpected"] = True
    _write_metadata_fixture(tmp_path, monkeypatch, metadata)

    with pytest.raises(RuntimeError, match="unknown: unexpected"):
        build_metadata.verify_metadata(use_worktree=True)


@pytest.mark.parametrize(
    ("container", "field"),
    [("top", "python"), ("source", "repo")],
)
def test_metadata_verification_rejects_missing_fields(
    container: str,
    field: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metadata = _worktree_metadata()
    target = metadata if container == "top" else metadata["source"]
    del target[field]
    _write_metadata_fixture(tmp_path, monkeypatch, metadata)

    with pytest.raises(RuntimeError, match=rf"missing: {field}"):
        build_metadata.verify_metadata(use_worktree=True)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("python", "3.12+", "project.requires-python"),
        ("netbox", ["4.7"], "typed version modules"),
        ("generated_at", "2026-02-30T00:00:00Z", "valid RFC 3339 UTC"),
        ("generated_at", "2026-09-14T00:00:00+00:00", "YYYY-MM-DDTHH:MM:SSZ"),
    ],
)
def test_metadata_verification_rejects_noncanonical_derived_values(
    field: str,
    value: object,
    message: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metadata = _worktree_metadata()
    metadata[field] = value
    _write_metadata_fixture(tmp_path, monkeypatch, metadata)

    with pytest.raises(RuntimeError, match=message):
        build_metadata.verify_metadata(use_worktree=True)


def test_metadata_verification_rejects_a_noncanonical_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metadata = _worktree_metadata()
    metadata["source"]["repo"] = "attacker/netbox-sdk"
    _write_metadata_fixture(tmp_path, monkeypatch, metadata)

    with pytest.raises(RuntimeError, match="source.repo"):
        build_metadata.verify_metadata(use_worktree=True)


def _stub_generation_source(
    monkeypatch: pytest.MonkeyPatch,
    *,
    object_type: str | None,
    source_version: str,
    source_content_id: str,
) -> None:
    monkeypatch.setattr(build_metadata, "source_commit", lambda: "a" * 40)
    monkeypatch.setattr(build_metadata, "content_id_for_worktree", lambda: "b" * 64)
    monkeypatch.setattr(build_metadata, "_resolved_object_type", lambda _commit: object_type)
    monkeypatch.setattr(
        build_metadata,
        "_git_output",
        lambda *_args, **_kwargs: object_type or "",
    )
    monkeypatch.setattr(
        build_metadata,
        "_git_blob_text",
        lambda _commit, _path: f'[project]\nversion = "{source_version}"\n',
    )
    monkeypatch.setattr(
        build_metadata,
        "content_id_for_tree",
        lambda _treeish="HEAD", **_kwargs: source_content_id,
    )


def test_generate_metadata_rejects_a_resolved_wrong_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_generation_source(
        monkeypatch,
        object_type="commit",
        source_version="0.0.12",
        source_content_id="b" * 64,
    )

    with pytest.raises(RuntimeError, match="project version"):
        build_metadata.generate_metadata()


def test_generate_metadata_rejects_a_resolved_wrong_tree(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_generation_source(
        monkeypatch,
        object_type="commit",
        source_version=_pyproject_version(),
        source_content_id="c" * 64,
    )

    with pytest.raises(RuntimeError, match="does not match the candidate tree"):
        build_metadata.generate_metadata()


def test_generate_metadata_rejects_a_resolved_tag_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_generation_source(
        monkeypatch,
        object_type="tag",
        source_version=_pyproject_version(),
        source_content_id="b" * 64,
    )

    with pytest.raises(RuntimeError, match="must identify a commit object"):
        build_metadata.generate_metadata()


def test_main_allows_an_unavailable_informational_sha(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "metadata.json"
    monkeypatch.setattr(build_metadata, "OUTPUT", output)
    monkeypatch.setattr(build_metadata, "source_commit", lambda: "f" * 40)
    monkeypatch.setattr(build_metadata, "content_id_for_worktree", lambda: "b" * 64)
    monkeypatch.setattr(build_metadata, "_resolved_object_type", lambda _commit: None)
    monkeypatch.setenv("GITHUB_REPOSITORY", "attacker/netbox-sdk")

    assert build_metadata.main([]) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["source"] == {
        "repo": "emersonfelipesp/netbox-sdk",
        "version": _pyproject_version(),
        "commit": "f" * 40,
        "content_id": "b" * 64,
    }


def _run_vector_git(
    repository: Path,
    *args: str,
    input_text: str | None = None,
    env: dict[str, str] | None = None,
) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repository,
        capture_output=True,
        check=False,
        env=env,
        input=input_text,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.rstrip("\n")


def _fixed_commit_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
            "GIT_AUTHOR_EMAIL": "vector@example.invalid",
            "GIT_AUTHOR_NAME": "Content Identity Vector",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
            "GIT_COMMITTER_EMAIL": "vector@example.invalid",
            "GIT_COMMITTER_NAME": "Content Identity Vector",
        }
    )
    return environment


def _build_content_identity_vector(repository: Path) -> str:
    repository.mkdir()
    _run_vector_git(repository, "init", "--quiet", "--initial-branch=main", "--object-format=sha1")
    _run_vector_git(repository, "config", "core.autocrlf", "false")
    _run_vector_git(repository, "config", "core.filemode", "true")
    _run_vector_git(repository, "config", "core.symlinks", "true")
    (repository / "dir with space").mkdir()
    (repository / "sub").mkdir()
    (repository / "unicodé").mkdir()
    (repository / "lf.txt").write_bytes(b"line one\nline two\n")
    (repository / "crlf.txt").write_bytes(b"line one\r\nline two\r\n")
    (repository / "plain.txt").write_bytes(b"regular file\n")
    executable = repository / "run.sh"
    executable.write_bytes(b"#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    (repository / "link").symlink_to("lf.txt")
    (repository / "dir with space" / "file name.txt").write_bytes(b"space path\n")
    (repository / "unicodé" / "雪.txt").write_bytes(b"snow\n")
    (repository / "metadata.json").write_bytes(b"{}\n")
    (repository / "sub" / "metadata.json").write_bytes(b"nested decoy\n")

    submodule = repository / "vendor" / "submodule"
    submodule.mkdir(parents=True)
    _run_vector_git(submodule, "init", "--quiet", "--initial-branch=main", "--object-format=sha1")
    empty_tree = _run_vector_git(submodule, "mktree", input_text="")
    submodule_commit = _run_vector_git(
        submodule,
        "commit-tree",
        empty_tree,
        input_text="fixed gitlink\n",
        env=_fixed_commit_environment(),
    )
    _run_vector_git(submodule, "update-ref", "refs/heads/main", submodule_commit)

    _run_vector_git(repository, "add", "--all", "--", ".")
    indexed_tree = _run_vector_git(repository, "write-tree")
    top_level = _run_vector_git(repository, "ls-tree", indexed_tree)
    outer_empty_tree = _run_vector_git(repository, "mktree", input_text="")
    tree_with_empty_subtree = _run_vector_git(
        repository,
        "mktree",
        input_text=f"{top_level}\n040000 tree {outer_empty_tree}\tempty\n",
    )
    commit = _run_vector_git(
        repository,
        "commit-tree",
        tree_with_empty_subtree,
        input_text="content identity vector\n",
        env=_fixed_commit_environment(),
    )
    _run_vector_git(repository, "update-ref", "refs/heads/main", commit)
    _run_vector_git(repository, "reset", "--quiet", "--hard", commit)
    return commit


_CONTENT_ID_VECTOR_TREE_LISTING = r"""100644 blob cf9b2a85b62bc2fd67c5ed43a1d0009df848ac8a	crlf.txt
100644 blob 3190dbbebe345ad88c4267721535251ac3d50cb9	dir with space/file name.txt
100644 blob e5c5c5583f49a34e86ce622b59363df99e09d4c6	lf.txt
120000 blob 934e2ae319ffce66c7278c255ef10440c9ed7865	link
100644 blob 0967ef424bce6791893e9a57bb952f80fd536e93	metadata.json
100644 blob fa4665e97505b2a2f243527a696b947843637735	plain.txt
100755 blob 039e4d0069c5c26909f86c505b9de66182e6d1f3	run.sh
100644 blob 5134f8db0a7d9c0212a25f1e84f081fe5f2e198c	sub/metadata.json
100644 blob 89f9f82472c28346d996925d034168dd77ac5da5	"unicod\303\251/\351\233\252.txt"
160000 commit 3fadd769e8d901d107861776309699201f31540f	vendor/submodule
"""
_CONTENT_ID_VECTOR_CANONICAL_LISTING = r"""100644 blob 3190dbbebe345ad88c4267721535251ac3d50cb9	dir with space/file name.txt
100644 blob 5134f8db0a7d9c0212a25f1e84f081fe5f2e198c	sub/metadata.json
100644 blob 89f9f82472c28346d996925d034168dd77ac5da5	"unicod\303\251/\351\233\252.txt"
100644 blob cf9b2a85b62bc2fd67c5ed43a1d0009df848ac8a	crlf.txt
100644 blob e5c5c5583f49a34e86ce622b59363df99e09d4c6	lf.txt
100644 blob fa4665e97505b2a2f243527a696b947843637735	plain.txt
100755 blob 039e4d0069c5c26909f86c505b9de66182e6d1f3	run.sh
120000 blob 934e2ae319ffce66c7278c255ef10440c9ed7865	link
160000 commit 3fadd769e8d901d107861776309699201f31540f	vendor/submodule
"""
_CONTENT_ID_VECTOR_SHA256 = "fbe4d1ce900a12e27db9a6bf143f2e5ee8fdf5ab7edcc16d7fa1d5f39cf00842"


def _use_vector_repository(monkeypatch: pytest.MonkeyPatch, repository: Path) -> None:
    monkeypatch.setattr(build_metadata, "ROOT", repository)
    monkeypatch.setattr(build_metadata, "OUTPUT", repository / "metadata.json")
    monkeypatch.setattr(
        build_metadata,
        "_load_project",
        lambda: {
            "version": "1.2.3",
            "requires-python": ">=3.11,<3.14",
            "urls": {"Repository": "https://github.com/emersonfelipesp/netbox-sdk"},
        },
    )
    monkeypatch.setattr(build_metadata, "discover_netbox_versions", lambda _directory: ["4.7"])


def test_content_identity_matches_the_independent_known_vector(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "vector"
    _build_content_identity_vector(repository)
    _use_vector_repository(monkeypatch, repository)
    listing = _run_vector_git(
        repository,
        "-c",
        "core.quotePath=true",
        "ls-tree",
        "-r",
        "--full-tree",
        "HEAD",
    )

    # These literals are transcribed from the hand-computed tree and canonical
    # listings above; they are intentionally independent of
    # build_metadata._canonical_tree_bytes().
    assert f"{listing}\n" == _CONTENT_ID_VECTOR_TREE_LISTING
    assert hashlib.sha256(_CONTENT_ID_VECTOR_CANONICAL_LISTING.encode()).hexdigest() == (
        _CONTENT_ID_VECTOR_SHA256
    )
    assert build_metadata.content_id_for_tree() == _CONTENT_ID_VECTOR_SHA256
    assert _run_vector_git(repository, "ls-tree", "HEAD", "--", "empty").startswith("040000 tree ")
    assert "\tempty\n" not in _CONTENT_ID_VECTOR_CANONICAL_LISTING


@pytest.mark.parametrize("mutation", ["mode", "content", "rename", "nested_metadata"])
def test_content_identity_vector_detects_every_material_mutation(
    mutation: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "vector"
    _build_content_identity_vector(repository)
    _use_vector_repository(monkeypatch, repository)
    if mutation == "mode":
        (repository / "run.sh").chmod(0o644)
    elif mutation == "content":
        (repository / "lf.txt").write_bytes(b"changed\n")
    elif mutation == "rename":
        (repository / "plain.txt").rename(repository / "renamed.txt")
    else:
        (repository / "sub" / "metadata.json").unlink()

    assert build_metadata.content_id_for_worktree() != _CONTENT_ID_VECTOR_SHA256


def test_content_identity_excludes_only_the_root_metadata_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "vector"
    _build_content_identity_vector(repository)
    _use_vector_repository(monkeypatch, repository)
    (repository / "metadata.json").write_bytes(b"changed but excluded\n")
    assert build_metadata.content_id_for_worktree() == _CONTENT_ID_VECTOR_SHA256
    (repository / "sub" / "metadata.json").unlink()
    assert build_metadata.content_id_for_worktree() != _CONTENT_ID_VECTOR_SHA256


def test_default_verify_cli_hashes_head_not_the_dirty_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "vector"
    _build_content_identity_vector(repository)
    _use_vector_repository(monkeypatch, repository)
    metadata = {
        "release": "1.2.3",
        "python": "3.11+",
        "netbox": ["4.7"],
        "generated_at": "2026-09-14T00:00:00Z",
        "source": {
            "repo": "emersonfelipesp/netbox-sdk",
            "version": "1.2.3",
            "commit": "f" * 40,
            "content_id": _CONTENT_ID_VECTOR_SHA256,
        },
    }
    (repository / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (repository / "lf.txt").write_bytes(b"dirty worktree\n")

    assert build_metadata.main(["--verify"]) == 0
    with pytest.raises(RuntimeError, match="does not match the repository content"):
        build_metadata.verify_metadata(use_worktree=True)


def _tree_drifted_commit() -> tuple[str, str] | None:
    """Return a published commit and the project version it declares.

    The pair is chosen so the version comparison passes by construction and only
    the tree comparison can reject it, which isolates the property under test.
    Deriving the version from the commit rather than from the current metadata
    keeps the fixture valid immediately after a version bump, when no older
    commit yet declares the new version.
    """
    history = _run_git("rev-list", "--max-count=60", "HEAD~1")
    if history is None or history.returncode != 0:
        return None
    for candidate in history.stdout.split():
        pyproject = _git_blob_text(candidate, "pyproject.toml")
        if pyproject is None:
            continue
        declared = tomllib.loads(pyproject)["project"]["version"]
        diff = _run_git(
            "diff", "--name-only", candidate, "HEAD", "--", ".", ":(exclude)metadata.json"
        )
        if diff is not None and diff.returncode == 0 and diff.stdout.strip():
            return candidate, declared
    return None


def _require_repository_checkout() -> None:
    git_probe = _run_git("rev-parse", "--show-toplevel")
    assert git_probe is not None and git_probe.returncode == 0, (
        "the traceability predicate cannot be exercised without Git metadata"
    )
    assert Path(git_probe.stdout.strip()).resolve() == REPO_ROOT.resolve()


def test_metadata_traceability_rejects_a_commit_with_a_different_tree() -> None:
    """A commit declaring its own version but another tree must be rejected.

    This is the mutation that matters: the version comparison cannot carry the
    check, because the fixture supplies the version the commit itself declares
    and differs only in tree. Removing the tree comparison from the predicate
    makes this fail.
    """
    _require_repository_checkout()
    fixture = _tree_drifted_commit()
    assert fixture is not None, (
        "no published commit has a tree differing from the candidate, so this "
        "guard cannot observe the property it asserts"
    )
    candidate, declared = fixture
    reason = _metadata_source_mismatch(candidate, declared)
    assert reason is not None and "represent the candidate tree" in reason


def test_metadata_traceability_rejects_a_commit_with_a_different_version() -> None:
    """A commit from an earlier release must be rejected on its version alone."""
    _require_repository_checkout()
    release = json.loads(_read("metadata.json"))["release"]
    reason = _metadata_source_mismatch(_IMMUTABLE_V0_0_10_COMMIT, release)
    assert reason is not None and "same project version" in reason


def test_metadata_traceability_accepts_the_recorded_commit() -> None:
    """The predicate accepts an available informational commit."""
    _require_repository_checkout()
    metadata = json.loads(_read("metadata.json"))
    source_type = _run_git("cat-file", "-t", metadata["source"]["commit"])
    assert source_type is not None
    if source_type.returncode != 0:
        return
    assert source_type.stdout.strip() == "commit"
    assert _metadata_source_mismatch(metadata["source"]["commit"], metadata["release"]) is None


def test_metadata_generation_rejects_invalid_source_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_COMMIT", "not-a-full-sha")
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    with pytest.raises(ValueError, match="full 40-character Git SHA"):
        build_metadata.source_commit()


def test_metadata_generation_fails_without_commit_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SOURCE_COMMIT", raising=False)
    monkeypatch.delenv("GITHUB_SHA", raising=False)

    def _missing_git(*_args: Any, **_kwargs: Any) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(build_metadata.subprocess, "run", _missing_git)
    with pytest.raises(RuntimeError, match="requires SOURCE_COMMIT"):
        build_metadata.source_commit()


def test_metadata_generation_rejects_source_version_mismatch() -> None:
    with pytest.raises(RuntimeError, match="project version"):
        build_metadata.validate_source_provenance(
            "646af6da9276886a0ea32fb518af6b3b9e0eb721",
            _pyproject_version(),
        )


def test_metadata_generation_rejects_materially_different_same_version_ancestor() -> None:
    with pytest.raises(RuntimeError, match="does not match the candidate tree"):
        build_metadata.validate_source_provenance(
            "3d629459cbe43509c4cbe63f0cf660db8da5856f",
            "0.0.10rc1",
        )


def test_metadata_generation_rejects_annotated_tag_object_sha() -> None:
    tag_type = _run_git("cat-file", "-t", _IMMUTABLE_V0_0_10_TAG_OBJECT)
    if tag_type is None or tag_type.returncode != 0:
        pytest.skip("The immutable annotated tag object is unavailable")
    assert tag_type.stdout.strip() == "tag"
    with pytest.raises(RuntimeError, match="must identify a commit object"):
        build_metadata.validate_source_provenance(
            _IMMUTABLE_V0_0_10_TAG_OBJECT,
            "0.0.10",
        )
