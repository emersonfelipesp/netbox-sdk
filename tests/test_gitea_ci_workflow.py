"""Semantic contracts for the secret-free Gitea pull-request quality gate."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / ".gitea" / "workflows" / "ci.yml"
FULL_SHA_ACTION = re.compile(r"^[^\s@]+@[0-9a-f]{40}$")


def _workflow() -> dict[str, Any]:
    value = yaml.load(WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(value, dict)
    return value


def _commands(job: dict[str, Any]) -> str:
    return "\n".join(str(step["run"]) for step in job.get("steps", []) if "run" in step)


def test_gitea_ci_has_bounded_read_only_main_triggers() -> None:
    workflow = _workflow()

    assert workflow["name"] == "Gitea CI"
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["on"]["push"]["branches"] == ["main"]
    assert workflow["on"]["pull_request"]["branches"] == ["main"]
    assert workflow["on"]["pull_request"]["types"] == [
        "opened",
        "synchronize",
        "reopened",
    ]
    assert "workflow_dispatch" in workflow["on"]
    assert workflow["concurrency"] == {
        "group": "gitea-ci-${{ github.ref }}",
        "cancel-in-progress": "true",
    }


def test_every_job_uses_the_untrusted_runner_and_explicit_timeout() -> None:
    jobs = _workflow()["jobs"]

    assert set(jobs) == {"static", "full-tests", "security", "docs-package"}
    for job in jobs.values():
        assert job["runs-on"] == "ci-untrusted-python312"
        assert int(job["timeout-minutes"]) > 0
        assert "environment" not in job
        assert "permissions" not in job


def test_third_party_actions_are_pinned_to_reviewed_commits() -> None:
    for job_name, job in _workflow()["jobs"].items():
        for step in job["steps"]:
            action = step.get("uses")
            if action is not None:
                assert FULL_SHA_ACTION.fullmatch(action), f"{job_name}: {action}"


def test_every_job_uses_the_complete_locked_environment() -> None:
    for job in _workflow()["jobs"].values():
        commands = _commands(job)
        assert "uv lock --check" in commands
        for extra in ("cli", "tui", "demo", "mock", "mcp"):
            assert f"--extra {extra}" in commands
        assert "--locked" in commands


def test_static_job_preserves_type_format_and_workflow_policy() -> None:
    commands = _commands(_workflow()["jobs"]["static"])

    for command in (
        ".github/workflows/*.yml",
        ".gitea/workflows/*.yml",
        "sha256sum --check --strict",
        "--connect-timeout 10 --max-time 120 --retry 3",
        "ty check netbox_sdk netbox_cli netbox_tui netbox_mcp tests",
        "pyright netbox_sdk netbox_cli netbox_tui netbox_mcp",
        "pre-commit run --all-files",
        "--show-diff-on-failure --color=always",
    ):
        assert command in commands


def test_complete_offline_and_security_suites_are_mandatory() -> None:
    jobs = _workflow()["jobs"]
    full_tests = _commands(jobs["full-tests"])
    security = _commands(jobs["security"])

    assert "pytest -v --tb=short -p no:randomly" in full_tests
    assert " -m " not in full_tests
    for module in (
        "tests/test_security_sdk.py",
        "tests/test_security_cli.py",
        "tests/test_security_tui.py",
    ):
        assert module in security


def test_docs_and_package_job_validates_source_and_installed_artifacts() -> None:
    commands = _commands(_workflow()["jobs"]["docs-package"])

    for command in (
        "mkdocs build --strict",
        "tests/test_certification_readiness.py",
        "--with build==1.5.0 python -m build",
        "--with twine==6.2.0 python -m twine check dist/*",
        "uv pip install --python",
        "import netbox_sdk",
        'joinpath("py.typed").is_file()',
        "import netbox_mcp",
    ):
        assert command in commands


def test_pull_request_workflow_has_no_publish_deploy_or_live_authority() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8").lower()

    for forbidden in (
        "secrets.",
        "twine upload",
        "mkdocs gh-deploy",
        "git push",
        "docker ",
        "netbox_url",
        "demo_username",
        "demo_password",
        "netbox.nmulti.cloud",
        "demo.netbox.dev",
        "environment:",
    ):
        assert forbidden not in text
