from __future__ import annotations

import json
import re
import subprocess
import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml

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


_SOURCE_CANDIDATE_SNIPPETS = (
    "docs/snippets/package-version.txt",
    "docs/snippets/documented-release-en.md",
    "docs/snippets/documented-release-pt.md",
)

_PUBLISHED_INSTALL_SNIPPETS = (
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
    for rel in _SOURCE_CANDIDATE_SNIPPETS:
        text = _read(rel)
        assert version in text, f"{rel} must include project version {version!r}"


def test_default_index_install_snippets_reference_published_final() -> None:
    published = _read("docs/snippets/published-package-version.txt").strip()
    assert is_public_pypi_version(published), (
        "the default-index install version must be a public final or post-release"
    )
    for rel in _PUBLISHED_INSTALL_SNIPPETS:
        assert published in _read(rel), f"{rel} must include published final {published!r}"


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
    assert f"netbox-sdk[all]=={published}" in readme
    assert f"git push gitea v{version}" in readme
    assert "gh release create vX.Y.Z" in readme
    assert '--title "netbox-sdk vX.Y.Z"' in readme


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


def test_metadata_writer_is_main_only_and_does_not_persist_credentials() -> None:
    workflow = _load_workflow(".github/workflows/publish-metadata.yml")
    triggers = workflow["on"]
    assert triggers["push"]["branches"] == ["main"]
    assert "tags" not in triggers["push"]
    assert "workflow_dispatch" not in triggers
    assert workflow["permissions"] == {"contents": "read"}

    generator = workflow["jobs"]["generate-metadata"]
    assert "github.ref == 'refs/heads/main'" in str(generator["if"])
    assert generator["permissions"] == {"contents": "read"}
    checkout = generator["steps"][0]
    assert checkout["with"]["persist-credentials"] == "false"

    writer = workflow["jobs"]["publish-metadata"]
    assert writer["needs"] == "generate-metadata"
    assert "github.ref == 'refs/heads/main'" in str(writer["if"])
    assert writer["permissions"] == {"contents": "read"}
    assert len(writer["steps"]) == 1
    push_step = writer["steps"][0]
    assert "uses" not in push_step
    assert push_step["env"]["METADATA_WRITE_TOKEN"] == ("${{ secrets.METADATA_WRITE_TOKEN }}")
    assert "github.token" not in str(writer)
    assert "git clone --no-tags --single-branch --branch main" in push_step["run"]
    assert 'test "$(git -C writer rev-parse HEAD)" = "$SOURCE_SHA"' in push_step["run"]


@pytest.mark.parametrize(
    "path",
    [
        ".github/workflows/publish-testpypi.yml",
        ".github/workflows/publish-metadata.yml",
    ],
)
def test_credentialed_release_workflows_use_immutable_actions(path: str) -> None:
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


def test_metadata_has_traceable_source_commit() -> None:
    metadata = json.loads(_read("metadata.json"))
    commit = metadata["source"]["commit"]
    assert metadata["release"] == _pyproject_version()
    assert re.fullmatch(r"[0-9a-f]{40}", commit), "metadata source.commit must be a full SHA"

    git_probe = _run_git("rev-parse", "--show-toplevel")
    if (
        git_probe is None
        or git_probe.returncode != 0
        or Path(git_probe.stdout.strip()).resolve() != REPO_ROOT.resolve()
    ):
        return
    source_type = _run_git("cat-file", "-t", commit)
    assert source_type is not None and source_type.returncode == 0
    assert source_type.stdout.strip() == "commit", (
        "metadata source.commit must identify a commit object in repository history"
    )
    ancestor = _run_git("merge-base", "--is-ancestor", commit, "HEAD")
    assert ancestor is not None and ancestor.returncode == 0, (
        "metadata source.commit must be in candidate ancestry"
    )

    pending_parent = _run_git("rev-parse", "--verify", "MERGE_HEAD^{}")
    if pending_parent is not None and pending_parent.returncode == 0:
        head = _run_git("rev-parse", "HEAD")
        assert head is not None and head.returncode == 0
        assert commit == head.stdout.strip(), (
            "pending integration metadata must identify the first-parent checkout; "
            "regenerate it against the integration commit immediately after committing"
        )
        return

    source_pyproject = _run_git("show", f"{commit}:pyproject.toml")
    assert source_pyproject is not None and source_pyproject.returncode == 0
    source_version = tomllib.loads(source_pyproject.stdout)["project"]["version"]
    assert source_version == metadata["release"], (
        "metadata must be a follow-up to an ancestor containing the same project version"
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
    assert source_diff is not None and source_diff.returncode == 0
    assert not source_diff.stdout.strip(), (
        "metadata source.commit must represent the candidate tree outside metadata.json"
    )


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
    with pytest.raises(RuntimeError, match="commit the integration first"):
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
