"""The model-build catalog must be reachable from a wheel, not only a checkout.

Fifty-odd build artifacts lived at ``django_models_builds/`` in the repository
root — outside every package, so no distribution could carry them. The SDK
resolved that root by walking up from its own module (correct in a checkout,
pointing outside the package in an installation) and the TUI walked up one level
too far, so it found nothing *even in a checkout*.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import sysconfig
import zipfile
from pathlib import Path

import pytest

from netbox_sdk.django_models import catalog
from netbox_sdk.django_models.fetcher import available_build_tags, build_exists, builds_dir
from netbox_sdk.versioning import SUPPORTED_NETBOX_VERSIONS
from netbox_tui.django_model_app import _discover_versions

pytestmark = pytest.mark.suite_sdk

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_bundled_catalog_is_not_empty() -> None:
    assert catalog.bundled_tags(), "the distribution ships no builds at all"


def test_manifest_declares_a_build_for_every_supported_line_it_can() -> None:
    """The manifest is the deliberate supported set, so it must be explicit."""
    manifest = catalog.supported_manifest()

    assert manifest, "no supported-build manifest is published"
    for line, tag in manifest.items():
        assert line in SUPPORTED_NETBOX_VERSIONS, f"{line} is not a supported release line"
        assert tag in catalog.bundled_tags(), f"{line} declares {tag}, which is not bundled"


def test_sdk_and_tui_return_the_same_ordered_tags() -> None:
    """The TUI used to resolve its own path, one level too high, and find nothing."""
    assert [tag for _label, tag in _discover_versions()] == available_build_tags()
    assert available_build_tags() == catalog.available_tags()


def test_tags_are_ordered_newest_first_numerically() -> None:
    """String ordering puts v4.5.9 above v4.5.10; version ordering must not."""
    tags = catalog.available_tags()

    assert tags == sorted(tags, key=catalog._version_key, reverse=True)
    if "v4.5.10" in tags and "v4.5.9" in tags:
        assert tags.index("v4.5.10") < tags.index("v4.5.9")


def test_packaged_builds_carry_no_build_machine_paths() -> None:
    """``/tmp/netbox-<tag>/`` provenance says nothing to a consumer and leaks layout."""
    for tag in catalog.bundled_tags():
        payload = json.dumps(catalog.load_build(tag))
        assert "/tmp/netbox-" not in payload, f"{tag} still carries transient build paths"


def test_downloads_target_a_writable_location_not_site_packages() -> None:
    """``site-packages`` is frequently read-only; generated builds must not go there."""
    target = builds_dir()
    purelib = Path(sysconfig.get_paths()["purelib"]).resolve()

    assert target == catalog.user_builds_dir()
    assert purelib not in target.resolve().parents
    assert target.resolve() != purelib


def test_user_store_is_redirectable_and_shadows_a_bundled_tag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A downloaded build is the more specific artifact and must win."""
    monkeypatch.setenv("NETBOX_SDK_MODEL_BUILDS_DIR", str(tmp_path))
    bundled = catalog.bundled_tags()[0]
    (tmp_path / f"{bundled}{catalog.BUILD_SUFFIX}").write_text(
        json.dumps({"models": {}, "marker": "from-user-store"}), encoding="utf-8"
    )

    assert catalog.load_build(bundled)["marker"] == "from-user-store"
    assert catalog.available_tags().count(bundled) == 1, "shadowing must not duplicate the tag"


def test_missing_tag_raises_rather_than_returning_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NETBOX_SDK_MODEL_BUILDS_DIR", "/nonexistent-netbox-sdk-store")

    assert not build_exists("v0.0.0-not-a-release")
    with pytest.raises(FileNotFoundError):
        catalog.load_build("v0.0.0-not-a-release")


@pytest.mark.slow
def test_built_wheel_exposes_the_catalog_outside_the_checkout(tmp_path: Path) -> None:
    """The acceptance criterion: the catalog must survive packaging.

    Builds a real wheel, unpacks it into a throwaway prefix, and imports it with
    the checkout **removed** from the path — a checkout on ``sys.path`` satisfies
    every import regardless of what the wheel contains, which is exactly how this
    defect stayed invisible.

    Uses ``uv``, the repository's build tool (the managed virtualenv ships no
    ``pip``). If it cannot run, this test **fails**: a packaging guard that
    reports success when it could not evaluate is worse than no guard at all.
    """
    uv = shutil.which("uv")
    assert uv is not None, "uv is required to verify the built distribution"

    dist = tmp_path / "dist"
    build = subprocess.run(
        [uv, "build", "--wheel", "--out-dir", str(dist), str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, f"wheel build failed:\n{build.stdout}\n{build.stderr}"

    wheels = list(dist.glob("netbox_sdk-*.whl"))
    assert wheels, f"no wheel produced in {dist}"

    # Unpack rather than install: this asserts on the artifact's own contents,
    # with no resolver able to substitute anything else.
    target = tmp_path / "site"
    with zipfile.ZipFile(wheels[0]) as archive:
        packaged = [n for n in archive.namelist() if "/model_builds/" in n]
        archive.extractall(target)

    assert packaged, "the wheel carries no model_builds artifacts"

    probe = (
        "import json;"
        "from netbox_sdk.django_models import catalog;"
        "print(json.dumps({'tags': catalog.bundled_tags(),"
        " 'manifest': catalog.supported_manifest()}))"
    )
    run = subprocess.run(
        [sys.executable, "-I", "-c", probe],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env={
            "PATH": "/usr/bin:/bin",
            "PYTHONPATH": str(target),
            "HOME": str(tmp_path),
            # Point the writable store at an empty dir so downloaded builds on
            # this machine cannot be mistaken for packaged ones.
            "NETBOX_SDK_MODEL_BUILDS_DIR": str(tmp_path / "empty-store"),
        },
    )
    assert run.returncode == 0, f"installed wheel could not read its catalog:\n{run.stderr}"

    payload = json.loads(run.stdout)
    assert payload["tags"], "the installed wheel exposes no builds"
    assert set(payload["tags"]) == set(catalog.bundled_tags())
    assert payload["manifest"] == catalog.supported_manifest()
