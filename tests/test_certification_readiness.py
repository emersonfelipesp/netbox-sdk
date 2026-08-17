from __future__ import annotations

import re
import tomllib
from pathlib import Path

from netbox_sdk.versioning import SUPPORTED_NETBOX_VERSIONS

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_package_metadata_declares_sdk_certification_basics() -> None:
    data = tomllib.loads(_read("pyproject.toml"))
    project = data["project"]

    assert project["name"] == "netbox-sdk"
    assert project["license"] == "Apache-2.0"
    assert project["license-files"] == ["LICENSE.txt"]
    assert project["requires-python"] == ">=3.11,<3.14"
    assert "License :: OSI Approved :: Apache Software License" not in project["classifiers"]
    assert project["urls"]["Repository"] == "https://github.com/emersonfelipesp/netbox-sdk"
    assert project["urls"]["Documentation"] == "https://emersonfelipesp.github.io/netbox-sdk/"
    assert (ROOT / "LICENSE.txt").is_file()


def test_public_version_and_docs_metadata_stay_aligned() -> None:
    data = tomllib.loads(_read("pyproject.toml"))
    pyproject_version = data["project"]["version"]
    init_text = _read("netbox_sdk/__init__.py")
    version_match = re.search(r'__version__ = "([^"]+)"', init_text)

    assert version_match is not None
    assert version_match.group(1) == pyproject_version
    assert _read("docs/snippets/package-version.txt").strip() == pyproject_version
    assert f'package_version: "{pyproject_version}"' in _read("mkdocs.yml")
    documented_release = _read("docs/snippets/documented-release-en.md")
    published_version = _read("docs/snippets/published-package-version.txt").strip()
    assert f"netbox-sdk {pyproject_version} source candidate" in documented_release
    assert f"default PyPI index is **{published_version}**" in documented_release


def test_certification_release_checklist_separates_candidate_and_pypi_final() -> None:
    checklist = _read("CERTIFICATION.md")
    assert "source/TestPyPI release examples match the candidate" in checklist
    assert "default-index pins match `docs/snippets/published-package-version.txt`" in checklist
    assert "pinned install snippets" not in checklist


def test_integration_certification_packet_is_present() -> None:
    root_packet = _read("CERTIFICATION.md")
    docs_packet = _read("docs/certification.md")
    readme = _read("README.md")

    for text in (root_packet, docs_packet, readme):
        assert "integration package" in text.lower()
        assert "not a NetBox plugin" in text
        assert "v4.6.6" in text
        assert "v4.6.3" in text
        assert "v4.6.2" in text
        assert "v4.5.10" in text

    assert (ROOT / "docs/certification.pt.md").is_file()
    assert "Certification Readiness: certification.md" in _read("mkdocs.yml")


def test_supported_netbox_release_lines_have_committed_artifacts() -> None:
    """Certification evidence must cover every *registered* line.

    Hardcoding the list meant a newly registered line contributed no certification
    evidence at all, which is how 4.7 shipped outside this gate.
    """
    assert SUPPORTED_NETBOX_VERSIONS, "no release lines registered"
    for line in SUPPORTED_NETBOX_VERSIONS:
        suffix = line.replace(".", "_")
        assert (ROOT / f"netbox_sdk/models/v{suffix}.py").is_file()
        assert (ROOT / f"netbox_sdk/typed_versions/v{suffix}.py").is_file()
        assert (ROOT / f"netbox_sdk/reference/openapi/netbox-openapi-{line}.json").is_file()


def test_ci_contains_certification_package_and_docs_gates() -> None:
    certification_workflow = _read(".github/workflows/certification.yml")
    docs_workflow = _read(".github/workflows/docs.yml")
    tests_workflow = _read(".github/workflows/test.yml")
    gitea_workflow = _read(".gitea/workflows/ci.yml")

    assert "python -m build" in certification_workflow
    assert "twine check dist/*" in certification_workflow
    assert "tests/test_certification_readiness.py" in certification_workflow
    assert "mkdocs build --strict" in docs_workflow
    assert "pull_request:" in docs_workflow
    assert 'netbox-version: ["v4.5.10", "v4.6.2", "v4.6.3", "v4.6.6"]' in tests_workflow
    assert "needs.changes.outputs.sdk == 'true'" in tests_workflow
    assert "tests/test_typed_generation.py" in tests_workflow
    assert "tests/test_live_netbox.py" in tests_workflow
    assert "tests/test_certification_readiness.py" in gitea_workflow
    assert "mkdocs build --strict" in gitea_workflow
    assert "python -m build" in gitea_workflow
    assert "twine check dist/*" in gitea_workflow
    assert "tests/test_security_sdk.py" in gitea_workflow
