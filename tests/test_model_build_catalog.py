"""The model-build catalog must be reachable from a wheel, not only a checkout.

Fifty-odd build artifacts lived at ``django_models_builds/`` in the repository
root — outside every package, so no distribution could carry them. The SDK
resolved that root by walking up from its own module (correct in a checkout,
pointing outside the package in an installation) and the TUI walked up one level
too far, so it found nothing *even in a checkout*.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import sysconfig
import zipfile
from pathlib import Path

import pytest

from netbox_sdk.django_models import catalog
from netbox_sdk.django_models.fetcher import (
    _match_tag,
    available_build_tags,
    build_exists,
    builds_dir,
)
from netbox_sdk.django_models.paths import normalize_build_paths
from netbox_sdk.django_models.store import DjangoModelStore
from netbox_sdk.versioning import SUPPORTED_NETBOX_VERSIONS, latest_stable_line
from netbox_tui.django_model_app import _discover_versions
from scripts import build_model_catalog, refresh_django_model_builds

pytestmark = pytest.mark.suite_sdk

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_bundled_catalog_is_not_empty() -> None:
    assert catalog.bundled_tags(), "the distribution ships no builds at all"


def test_manifest_declares_a_build_for_every_supported_line_it_can() -> None:
    """The manifest is the deliberate supported set, so it must be explicit."""
    manifest = catalog.supported_manifest()
    manifest_path = REPO_ROOT / "netbox_sdk" / "django_models" / "model_builds" / "manifest.json"
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest, "no supported-build manifest is published"
    for line, tag in manifest.items():
        assert line in SUPPORTED_NETBOX_VERSIONS, f"{line} is not a supported release line"
        assert tag in catalog.bundled_tags(), f"{line} declares {tag}, which is not bundled"
    assert manifest_payload["exact_builds"] == catalog.bundled_tags()


@pytest.mark.parametrize("tag", ["v4.6.3", "v4.6.10"])
def test_packaged_patch_builds_are_exactly_loadable(
    tag: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("NETBOX_SDK_MODEL_BUILDS_DIR", "/nonexistent-netbox-sdk-store")

    assert tag in catalog.bundled_tags()
    assert catalog.load_build(tag)["models"]


def test_release_line_matching_selects_the_newest_packaged_patch() -> None:
    assert _match_tag("4.6", catalog.bundled_tags()) == "v4.6.10"


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


def test_archive_and_catalog_contain_the_newest_stable_release_line() -> None:
    stable_line = latest_stable_line()
    selected = build_model_catalog.select_tags()

    assert stable_line in selected, (
        f"django_models_builds lacks stable NetBox {stable_line}; download the latest "
        "django-model-builds workflow artifact and run "
        "scripts/refresh_django_model_builds.py before review"
    )
    manifest = catalog.supported_manifest()
    assert manifest.get(stable_line) == selected[stable_line], (
        f"bundled Django model catalog is stale for stable NetBox {stable_line}; run "
        "scripts/refresh_django_model_builds.py before review"
    )


def test_builder_records_paths_relative_to_the_checkout_root(tmp_path: Path) -> None:
    checkout = tmp_path / "netbox-v4.7.0"
    models_dir = checkout / "netbox" / "dcim" / "models"
    models_dir.mkdir(parents=True)
    (models_dir / "devices.py").write_text(
        "class Device(PrimaryModel):\n    name = models.CharField(max_length=64)\n",
        encoding="utf-8",
    )
    output = tmp_path / "build.json"

    graph = DjangoModelStore(cache_path=output).build(checkout / "netbox", apps=("dcim",))

    assert graph["meta"]["source_path"] == "netbox"
    assert graph["models"]["dcim.Device"]["file_path"] == ("netbox/dcim/models/devices.py")
    assert str(tmp_path) not in output.read_text(encoding="utf-8")
    assert "class Device" in DjangoModelStore(
        cache_path=output, checkout_root=checkout
    ).get_model_source("dcim.Device")


@pytest.mark.parametrize(
    "source_root",
    [
        "/home/runner/work/netbox-sdk/netbox-sdk/netbox-v4.7.0/netbox",
        "/home/runner/work/_temp/netbox-v4.7.0.ABC123/netbox",
    ],
)
def test_catalog_normalizes_runner_checkout_paths(source_root: str) -> None:
    payload = {
        "meta": {"source_path": source_root},
        "models": {"dcim.Device": {"file_path": f"{source_root}/dcim/models/devices.py"}},
    }

    normalized = normalize_build_paths(payload)

    assert normalized["meta"]["source_path"] == "netbox"
    assert normalized["models"]["dcim.Device"]["file_path"] == ("netbox/dcim/models/devices.py")


def test_catalog_rejects_an_absolute_path_outside_the_checkout_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    (source_dir / "v4.7.1-django-models-build.json").write_text(
        json.dumps(
            {
                "meta": {"source_path": "/home/runner/work/_temp/netbox-v4.7.1/netbox"},
                "models": {"dcim.Device": {"file_path": "/etc/passwd"}},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(build_model_catalog, "SOURCE_DIR", source_dir)
    monkeypatch.setattr(build_model_catalog, "TARGET_DIR", target_dir)
    monkeypatch.setattr(build_model_catalog, "MANIFEST", target_dir / "manifest.json")

    assert build_model_catalog.main() == 1
    error = capsys.readouterr().err
    assert "absolute recorded path" in error
    assert "regenerate this artifact with a current netbox-sdk builder" in error
    assert not target_dir.exists()


def test_catalog_generation_retains_prior_exact_builds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    target_dir.mkdir()
    current = source_dir / "v4.6.10-django-models-build.json"
    retained = target_dir / "v4.6.3-django-models-build.json"
    payload = json.dumps({"meta": {"source_path": "netbox"}, "models": {}})
    current.write_text(payload, encoding="utf-8")
    retained.write_text(payload, encoding="utf-8")
    monkeypatch.setattr(build_model_catalog, "SOURCE_DIR", source_dir)
    monkeypatch.setattr(build_model_catalog, "TARGET_DIR", target_dir)
    monkeypatch.setattr(build_model_catalog, "MANIFEST", target_dir / "manifest.json")

    assert build_model_catalog.main() == 0

    manifest = json.loads((target_dir / "manifest.json").read_text(encoding="utf-8"))
    assert retained.is_file()
    assert manifest["builds"]["4.6"] == "v4.6.10"
    assert manifest["exact_builds"] == ["v4.6.10", "v4.6.3"]


def test_catalog_prune_requires_the_explicit_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_dir = tmp_path / "source"
    target_dir = tmp_path / "target"
    source_dir.mkdir()
    target_dir.mkdir()
    payload = json.dumps({"meta": {"source_path": "netbox"}, "models": {}})
    (source_dir / "v4.6.10-django-models-build.json").write_text(payload, encoding="utf-8")
    retained = target_dir / "v4.6.3-django-models-build.json"
    retained.write_text(payload, encoding="utf-8")
    monkeypatch.setattr(build_model_catalog, "SOURCE_DIR", source_dir)
    monkeypatch.setattr(build_model_catalog, "TARGET_DIR", target_dir)
    monkeypatch.setattr(build_model_catalog, "MANIFEST", target_dir / "manifest.json")

    assert build_model_catalog.main(prune=True) == 0
    assert not retained.exists()


def test_refresh_imports_and_normalizes_a_downloaded_artifact(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "download" / "django-model-graphs-123"
    artifact_dir.mkdir(parents=True)
    source_root = "/home/runner/work/_temp/netbox-v4.7.1.XYZ/netbox"
    source = artifact_dir / "v4.7.1-django-models-build.json"
    source.write_text(
        json.dumps(
            {
                "meta": {"source_path": source_root},
                "models": {"dcim.Device": {"file_path": f"{source_root}/dcim/models/devices.py"}},
            }
        ),
        encoding="utf-8",
    )

    imported = refresh_django_model_builds.import_artifacts(
        artifact_dir.parent, tmp_path / "archive"
    )

    assert [path.name for path in imported] == [source.name]
    payload = json.loads(imported[0].read_text(encoding="utf-8"))
    assert payload["meta"]["source_path"] == "netbox"
    assert payload["models"]["dcim.Device"]["file_path"] == ("netbox/dcim/models/devices.py")


def _local_netbox_checkout(tmp_path: Path) -> tuple[Path, Path]:
    checkout = tmp_path / "netbox-v4.7.1"
    models_dir = checkout / "netbox" / "dcim" / "models"
    models_dir.mkdir(parents=True)
    model_file = models_dir / "devices.py"
    model_file.write_text(
        "class Device(PrimaryModel):\n    name = models.CharField(max_length=64)\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "--quiet", "--initial-branch=main", str(checkout)], check=True)
    subprocess.run(
        ["git", "-C", str(checkout), "config", "user.name", "Model Catalog Test"],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(checkout),
            "config",
            "user.email",
            "catalog@example.invalid",
        ],
        check=True,
    )
    subprocess.run(["git", "-C", str(checkout), "add", "--all"], check=True)
    subprocess.run(["git", "-C", str(checkout), "commit", "--quiet", "-m", "fixture"], check=True)
    subprocess.run(["git", "-C", str(checkout), "tag", "v4.7.1"], check=True)
    return checkout, model_file


def test_refresh_can_build_from_an_existing_local_checkout(tmp_path: Path) -> None:
    checkout, _model_file = _local_netbox_checkout(tmp_path)

    destination = refresh_django_model_builds.build_local(checkout, "v4.7.1", tmp_path / "archive")

    payload = json.loads(destination.read_text(encoding="utf-8"))
    assert payload["meta"]["source_path"] == "netbox"
    assert payload["models"]["dcim.Device"]["file_path"] == ("netbox/dcim/models/devices.py")


@pytest.mark.parametrize("dirty_kind", ["tracked", "untracked"])
def test_refresh_rejects_dirty_model_files(tmp_path: Path, dirty_kind: str) -> None:
    checkout, model_file = _local_netbox_checkout(tmp_path)
    if dirty_kind == "tracked":
        model_file.write_text("class ChangedDevice:\n    pass\n", encoding="utf-8")
    else:
        model_file.with_name("local_model.py").write_text(
            "class LocalModel:\n    pass\n", encoding="utf-8"
        )

    with pytest.raises(ValueError, match="modified tracked or untracked files"):
        refresh_django_model_builds.build_local(
            checkout,
            "v4.7.1",
            tmp_path / "archive",
        )


def test_refresh_repository_commands_use_argv_only(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[list[str], Path, bool]] = []

    def fake_run(args: list[str], *, cwd: Path, check: bool) -> subprocess.CompletedProcess[str]:
        calls.append((args, cwd, check))
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr(refresh_django_model_builds.subprocess, "run", fake_run)

    refresh_django_model_builds.regenerate_catalog_and_show_status()

    assert calls == [
        (
            [
                sys.executable,
                str(REPO_ROOT / "scripts" / "build_model_catalog.py"),
            ],
            REPO_ROOT,
            False,
        ),
        (["git", "status"], REPO_ROOT, False),
    ]


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

    source = tmp_path / "source"
    shutil.copytree(
        REPO_ROOT,
        source,
        ignore=shutil.ignore_patterns(
            ".git",
            ".tmp",
            ".venv",
            "*.egg-info",
            "__pycache__",
            "build",
        ),
    )
    dist = tmp_path / "dist"
    build = subprocess.run(
        [uv, "build", "--wheel", "--out-dir", str(dist), str(source)],
        capture_output=True,
        env={**os.environ, "UV_OFFLINE": "1"},
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
