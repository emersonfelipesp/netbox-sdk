from __future__ import annotations

import base64
import csv
import gzip
import hashlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import zipfile
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts.gitea_release import (
    MANIFEST_NAME,
    SEAL_NAME,
    ArtifactRecord,
    BoundedHttpClient,
    GiteaRegistry,
    ReleaseError,
    RemoteState,
    TransferManifest,
    _main_publish,
    _main_validate_tag,
    _manifest_payload,
    _run_twine_upload,
    _validate_wheel_record,
    classify_remote_state,
    compare_builds,
    harden_downloaded_seal,
    normalize_build,
    prepare_transfer,
    reconcile_publication,
    seal_transfer,
    validate_archive_source_binding,
    validate_release_tag_protection,
    validate_seal,
    validate_transfer,
    validate_trusted_source_checkout,
)
from scripts.release_policy import (
    validate_exact_canonical_source,
    validate_gitea_candidate_tag,
    validated_commit_epoch,
)

pytestmark = pytest.mark.suite_sdk

PACKAGE = "netbox-sdk"
VERSION = "0.0.11rc2"
SOURCE_SHA = "a" * 40
SOURCE_EPOCH = 1700000000
WHEEL = "netbox_sdk-0.0.11rc2-py3-none-any.whl"
SDIST = "netbox_sdk-0.0.11rc2.tar.gz"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def _commit(repo: Path) -> str:
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "candidate")
    return _git(repo, "rev-parse", "HEAD")


def _source_repo(tmp_path: Path) -> tuple[Path, str]:
    repo = tmp_path / "source"
    (repo / "demo").mkdir(parents=True)
    (repo / "tests").mkdir()
    (repo / "pyproject.toml").write_text(
        """[project]
name = "netbox-sdk"
version = "0.0.11rc2"
description = "Fixture"
readme = "README.md"
license = "Apache-2.0"
license-files = ["LICENSE.txt"]
requires-python = ">=3.11,<3.14"
authors = [{name = "Release Author", email = "author@example.invalid"}]
maintainers = [{name = "Release Maintainer", email = "maintainer@example.invalid"}]
keywords = ["fixture", "release"]
classifiers = ["Development Status :: 3 - Alpha", "Typing :: Typed"]
dependencies = ["demo-dependency>=1"]

[project.urls]
Homepage = "https://example.invalid/project"
Documentation = "https://example.invalid/docs"

[project.optional-dependencies]
all = ["extra-dependency>=2"]
empty = []

[project.scripts]
nbx = "demo:main"
nbx-mcp = "demo:mcp"
nbx-mock = "demo:mock"

[tool.setuptools.packages.find]
include = ["demo*"]

[tool.setuptools.package-data]
demo = ["py.typed"]
""",
        encoding="utf-8",
    )
    (repo / "README.md").write_text("fixture\n", encoding="utf-8")
    (repo / "LICENSE.txt").write_text("license\n", encoding="utf-8")
    (repo / "demo" / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / "demo" / "py.typed").write_text("", encoding="utf-8")
    (repo / "tests" / "test_demo.py").write_text("def test_demo(): pass\n", encoding="utf-8")
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Release Test")
    _git(repo, "config", "user.email", "release@example.invalid")
    return repo, _commit(repo)


def _metadata() -> bytes:
    return (
        b"Metadata-Version: 2.4\n"
        b"Name: netbox-sdk\n"
        b"Version: 0.0.11rc2\n"
        b"Summary: Fixture\n"
        b"Author-email: Release Author <author@example.invalid>\n"
        b"Maintainer-email: Release Maintainer <maintainer@example.invalid>\n"
        b"License-Expression: Apache-2.0\n"
        b"Project-URL: Homepage, https://example.invalid/project\n"
        b"Project-URL: Documentation, https://example.invalid/docs\n"
        b"Keywords: fixture,release\n"
        b"Classifier: Development Status :: 3 - Alpha\n"
        b"Classifier: Typing :: Typed\n"
        b"Requires-Python: <3.14,>=3.11\n"
        b"Description-Content-Type: text/markdown\n"
        b"License-File: LICENSE.txt\n"
        b"Requires-Dist: demo-dependency>=1\n"
        b'Requires-Dist: extra-dependency>=2; extra == "all"\n'
        b"Provides-Extra: all\n"
        b"Provides-Extra: empty\n"
        b"Dynamic: license-file\n\n"
        b"fixture\n"
    )


def _wheel_members(repo: Path) -> dict[str, bytes]:
    dist_info = "netbox_sdk-0.0.11rc2.dist-info"
    members = {
        "demo/__init__.py": (repo / "demo/__init__.py").read_bytes(),
        "demo/py.typed": b"",
        f"{dist_info}/METADATA": _metadata(),
        f"{dist_info}/WHEEL": (
            b"Wheel-Version: 1.0\nGenerator: setuptools (80.9.0)\n"
            b"Root-Is-Purelib: true\nTag: py3-none-any\n\n"
        ),
        f"{dist_info}/entry_points.txt": (
            b"[console_scripts]\nnbx = demo:main\nnbx-mcp = demo:mcp\nnbx-mock = demo:mock\n"
        ),
        f"{dist_info}/licenses/LICENSE.txt": (repo / "LICENSE.txt").read_bytes(),
        f"{dist_info}/top_level.txt": b"demo\n",
    }
    record_name = f"{dist_info}/RECORD"
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    for name, payload in members.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode()
        writer.writerow((name, f"sha256={digest}", len(payload)))
    writer.writerow((record_name, "", ""))
    members[record_name] = output.getvalue().encode()
    return members


def _write_wheel(path: Path, members: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in members.items():
            archive.writestr(name, payload)


def _sdist_members(repo: Path) -> dict[str, bytes]:
    egg = "netbox_sdk.egg-info"
    entry_points = b"[console_scripts]\nnbx = demo:main\nnbx-mcp = demo:mcp\nnbx-mock = demo:mock\n"
    members = {
        "LICENSE.txt": (repo / "LICENSE.txt").read_bytes(),
        "README.md": (repo / "README.md").read_bytes(),
        "pyproject.toml": (repo / "pyproject.toml").read_bytes(),
        "demo/__init__.py": (repo / "demo/__init__.py").read_bytes(),
        "demo/py.typed": b"",
        "tests/test_demo.py": (repo / "tests/test_demo.py").read_bytes(),
        "PKG-INFO": _metadata(),
        "setup.cfg": b"[egg_info]\ntag_build = \ntag_date = 0\n\n",
        f"{egg}/PKG-INFO": _metadata(),
        f"{egg}/dependency_links.txt": b"\n",
        f"{egg}/entry_points.txt": entry_points,
        f"{egg}/requires.txt": (b"demo-dependency>=1\n\n[all]\nextra-dependency>=2\n\n[empty]\n\n"),
        f"{egg}/top_level.txt": b"demo\n",
    }
    sources_name = f"{egg}/SOURCES.txt"
    source_names = set(members) - {"PKG-INFO", "setup.cfg"}
    source_names.add(sources_name)
    members[sources_name] = ("\n".join(sorted(source_names)) + "\n").encode()
    return members


def _write_sdist(path: Path, members: dict[str, bytes]) -> None:
    prefix = "netbox_sdk-0.0.11rc2"
    with tarfile.open(path, "w:gz") as archive:
        for name, payload in members.items():
            info = tarfile.TarInfo(f"{prefix}/{name}")
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))


def _transfer(tmp_path: Path) -> tuple[Path, TransferManifest, Path]:
    repo, source_sha = _source_repo(tmp_path)
    transfer = tmp_path / "transfer"
    transfer.mkdir()
    _write_wheel(transfer / WHEEL, _wheel_members(repo))
    _write_sdist(transfer / SDIST, _sdist_members(repo))
    source_epoch = validated_commit_epoch(commit_ref=source_sha, repo=repo)
    normalize_build(
        dist_dir=transfer,
        package=PACKAGE,
        version=VERSION,
        source_epoch=source_epoch,
    )
    artifacts = tuple(
        ArtifactRecord(
            path.name, path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest()
        )
        for path in (transfer / WHEEL, transfer / SDIST)
    )
    manifest = TransferManifest(
        PACKAGE,
        VERSION,
        source_sha,
        artifacts,
        source_epoch,
    )
    (transfer / MANIFEST_NAME).write_text(
        json.dumps(_manifest_payload(manifest), sort_keys=True), encoding="utf-8"
    )
    return transfer, manifest, repo


def _rewrite_transfer_manifest(
    transfer: Path,
    manifest: TransferManifest,
) -> TransferManifest:
    artifacts = tuple(
        ArtifactRecord(
            path.name,
            path.stat().st_size,
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        for path in (transfer / WHEEL, transfer / SDIST)
    )
    rewritten = TransferManifest(
        manifest.package,
        manifest.version,
        manifest.source_sha,
        artifacts,
        manifest.source_epoch,
    )
    (transfer / MANIFEST_NAME).write_text(
        json.dumps(_manifest_payload(rewritten), sort_keys=True),
        encoding="utf-8",
    )
    return rewritten


def test_transfer_and_archives_bind_to_independent_git_objects(tmp_path: Path) -> None:
    transfer, manifest, repo = _transfer(tmp_path)
    assert (
        validate_transfer(
            transfer_dir=transfer,
            expected_package=PACKAGE,
            expected_version=VERSION,
            expected_source_sha=manifest.source_sha,
        )
        == manifest
    )
    validate_archive_source_binding(transfer_dir=transfer, manifest=manifest, source_root=repo)


def test_transfer_rejects_extra_files_and_wrong_source(tmp_path: Path) -> None:
    transfer, manifest, _repo = _transfer(tmp_path)
    (transfer / "unexpected").write_bytes(b"extra")
    with pytest.raises(ReleaseError, match="exact bounded file set"):
        validate_transfer(
            transfer_dir=transfer,
            expected_package=PACKAGE,
            expected_version=VERSION,
            expected_source_sha=manifest.source_sha,
        )
    (transfer / "unexpected").unlink()
    with pytest.raises(ReleaseError, match="identity mismatch"):
        validate_transfer(
            transfer_dir=transfer,
            expected_package=PACKAGE,
            expected_version=VERSION,
            expected_source_sha="b" * 40,
        )


def test_prepare_transfer_cleans_partial_destination_on_copy_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / WHEEL).write_bytes(b"wheel")
    (dist / SDIST).write_bytes(b"sdist")
    calls = 0

    def fail_second_copy(source: Path, destination: Path, *, follow_symlinks: bool) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("copy failed")
        destination.write_bytes(source.read_bytes())

    monkeypatch.setattr("scripts.gitea_release.shutil.copyfile", fail_second_copy)
    transfer = tmp_path / "transfer"
    with pytest.raises(OSError, match="copy failed"):
        prepare_transfer(
            dist_dir=dist,
            transfer_dir=transfer,
            package=PACKAGE,
            version=VERSION,
            source_sha=SOURCE_SHA,
            source_epoch=SOURCE_EPOCH,
        )
    assert not transfer.exists()


def test_archive_normalization_makes_independent_builds_byte_identical(
    tmp_path: Path,
) -> None:
    repo, _source_sha = _source_repo(tmp_path)
    first = tmp_path / "dist-a"
    second = tmp_path / "dist-b"
    first.mkdir()
    second.mkdir()
    wheel_members = _wheel_members(repo)
    sdist_members = _sdist_members(repo)
    _write_wheel(first / WHEEL, wheel_members)
    _write_sdist(first / SDIST, sdist_members)
    _write_wheel(second / WHEEL, dict(reversed(tuple(wheel_members.items()))))
    _write_sdist(second / SDIST, dict(reversed(tuple(sdist_members.items()))))
    assert (first / WHEEL).read_bytes() != (second / WHEEL).read_bytes()
    assert (first / SDIST).read_bytes() != (second / SDIST).read_bytes()

    normalize_build(
        dist_dir=first,
        package=PACKAGE,
        version=VERSION,
        source_epoch=SOURCE_EPOCH,
    )
    normalize_build(
        dist_dir=second,
        package=PACKAGE,
        version=VERSION,
        source_epoch=SOURCE_EPOCH,
    )
    compare_builds(first_dir=first, second_dir=second, package=PACKAGE, version=VERSION)
    assert (first / WHEEL).read_bytes() == (second / WHEEL).read_bytes()
    assert (first / SDIST).read_bytes() == (second / SDIST).read_bytes()
    with zipfile.ZipFile(first / WHEEL) as archive:
        infos = archive.infolist()
        assert [info.filename for info in infos] == sorted(info.filename for info in infos)
        assert {info.date_time for info in infos} == {(2023, 11, 14, 22, 13, 20)}
        assert {info.external_attr >> 16 for info in infos} == {stat.S_IFREG | 0o644}
    assert int.from_bytes((first / SDIST).read_bytes()[4:8], "little") == SOURCE_EPOCH
    with tarfile.open(first / SDIST) as archive:
        members = archive.getmembers()
        assert [member.name for member in members] == sorted(member.name for member in members)
        assert {member.mtime for member in members} == {SOURCE_EPOCH}
        assert {(member.uid, member.gid, member.uname, member.gname) for member in members} == {
            (0, 0, "", "")
        }
        assert all(member.mode == (0o755 if member.isdir() else 0o644) for member in members)

    (second / SDIST).write_bytes((second / SDIST).read_bytes() + b"mutation")
    with pytest.raises(ReleaseError, match="byte-identical"):
        compare_builds(first_dir=first, second_dir=second, package=PACKAGE, version=VERSION)


def _mutate_archive_envelope(transfer: Path, repo: Path, mutation: str) -> None:
    wheel = transfer / WHEEL
    sdist = transfer / SDIST
    if mutation == "zip-comment":
        with zipfile.ZipFile(wheel, "a") as archive:
            archive.comment = b"untrusted builder comment"
        return
    if mutation == "zip-preamble":
        wheel.write_bytes(b"untrusted-preamble" + wheel.read_bytes())
        return
    if mutation == "zip-trailer":
        wheel.write_bytes(wheel.read_bytes() + b"untrusted-trailer")
        return
    if mutation == "zip-local-central-extra":
        with zipfile.ZipFile(wheel, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for index, (name, payload) in enumerate(_wheel_members(repo).items()):
                info = zipfile.ZipInfo(name)
                if index == 0:
                    info.extra = b"\x01\x00\x00\x00"
                archive.writestr(info, payload)
        raw = bytearray(wheel.read_bytes())
        assert raw[:4] == b"PK\x03\x04"
        filename_size = int.from_bytes(raw[26:28], "little")
        extra_size = int.from_bytes(raw[28:30], "little")
        assert extra_size == 4
        raw[30 + filename_size : 32 + filename_size] = b"\x02\x00"
        wheel.write_bytes(raw)
        return
    if mutation == "gzip-header":
        raw = bytearray(sdist.read_bytes())
        raw[9] = 3 if raw[9] != 3 else 255
        sdist.write_bytes(raw)
        return
    if mutation == "gzip-concatenated-member":
        sdist.write_bytes(sdist.read_bytes() + gzip.compress(b"", mtime=SOURCE_EPOCH))
        return
    if mutation in {"tar-metadata", "pax-metadata"}:
        prefix = "netbox_sdk-0.0.11rc2"
        with tarfile.open(sdist, "w:gz", format=tarfile.PAX_FORMAT) as archive:
            for index, (name, payload) in enumerate(_sdist_members(repo).items()):
                info = tarfile.TarInfo(f"{prefix}/{name}")
                info.size = len(payload)
                if mutation == "tar-metadata" and index == 0:
                    info.uid = 42
                    info.uname = "untrusted"
                if mutation == "pax-metadata" and index == 0:
                    info.pax_headers = {"comment": "untrusted"}
                archive.addfile(info, io.BytesIO(payload))
        return
    raise AssertionError(f"unknown mutation: {mutation}")


@pytest.mark.parametrize(
    "mutation",
    [
        "zip-comment",
        "zip-preamble",
        "zip-trailer",
        "zip-local-central-extra",
        "gzip-header",
        "gzip-concatenated-member",
        "tar-metadata",
        "pax-metadata",
    ],
)
def test_trusted_seal_rejects_noncanonical_archive_envelopes_without_mutating_input(
    tmp_path: Path,
    mutation: str,
) -> None:
    transfer, manifest, repo = _transfer(tmp_path)
    _mutate_archive_envelope(transfer, repo, mutation)
    manifest = _rewrite_transfer_manifest(transfer, manifest)
    before = {name: (transfer / name).read_bytes() for name in (WHEEL, SDIST, MANIFEST_NAME)}
    with pytest.raises(ReleaseError, match="canonical"):
        seal_transfer(
            transfer_dir=transfer,
            sealed_dir=tmp_path / "sealed",
            source_root=repo,
            expected_package=PACKAGE,
            expected_version=VERSION,
            expected_source_sha=manifest.source_sha,
            expected_source_epoch=manifest.source_epoch,
        )
    assert {name: (transfer / name).read_bytes() for name in before} == before
    assert not (tmp_path / "sealed").exists()


def test_source_epoch_is_exact_commit_authority(tmp_path: Path) -> None:
    repo, source_sha = _source_repo(tmp_path)
    epoch = validated_commit_epoch(commit_ref=source_sha, repo=repo)
    assert epoch == int(_git(repo, "show", "-s", "--format=%ct", source_sha))
    transfer, manifest, source_repo = _transfer(tmp_path / "second")
    altered = TransferManifest(
        manifest.package,
        manifest.version,
        manifest.source_sha,
        manifest.artifacts,
        manifest.source_epoch - 1,
    )
    with pytest.raises(ReleaseError, match="epoch"):
        validate_archive_source_binding(
            transfer_dir=transfer,
            manifest=altered,
            source_root=source_repo,
        )


def test_corrupt_reachable_git_object_fails_without_lazy_fetch(tmp_path: Path) -> None:
    repo, source_sha = _source_repo(tmp_path)
    validate_trusted_source_checkout(source_root=repo, source_sha=source_sha)
    object_path = repo / ".git" / "objects" / source_sha[:2] / source_sha[2:]
    object_path.chmod(object_path.stat().st_mode | stat.S_IWUSR)
    object_path.write_bytes(b"corrupt loose commit")

    with pytest.raises(ReleaseError, match="could not be validated"):
        validate_trusted_source_checkout(source_root=repo, source_sha=source_sha)


@pytest.mark.parametrize("target", ["wheel-code", "wheel-metadata", "sdist-code"])
def test_builder_cannot_bless_hostile_archives_with_a_matching_manifest(
    tmp_path: Path,
    target: str,
) -> None:
    transfer, manifest, repo = _transfer(tmp_path)
    if target.startswith("wheel"):
        members = _wheel_members(repo)
        if target == "wheel-code":
            members["demo/__init__.py"] = b"raise SystemExit('hostile')\n"
        else:
            name = "netbox_sdk-0.0.11rc2.dist-info/METADATA"
            members[name] = members[name].replace(b"\n\n", b"\nRequires-Dist: hostile\n\n", 1)
        record = "netbox_sdk-0.0.11rc2.dist-info/RECORD"
        del members[record]
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        for name, payload in members.items():
            digest = (
                base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode()
            )
            writer.writerow((name, f"sha256={digest}", len(payload)))
        writer.writerow((record, "", ""))
        members[record] = output.getvalue().encode()
        _write_wheel(transfer / WHEEL, members)
    else:
        members = _sdist_members(repo)
        members["demo/__init__.py"] = b"raise SystemExit('hostile')\n"
        _write_sdist(transfer / SDIST, members)

    records = tuple(
        ArtifactRecord(
            path.name, path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest()
        )
        for path in (transfer / WHEEL, transfer / SDIST)
    )
    hostile = TransferManifest(
        PACKAGE,
        VERSION,
        manifest.source_sha,
        records,
        manifest.source_epoch,
    )
    (transfer / MANIFEST_NAME).write_text(json.dumps(_manifest_payload(hostile)), encoding="utf-8")
    validate_transfer(
        transfer_dir=transfer,
        expected_package=PACKAGE,
        expected_version=VERSION,
        expected_source_sha=manifest.source_sha,
    )
    with pytest.raises(ReleaseError, match="trusted|differs"):
        validate_archive_source_binding(transfer_dir=transfer, manifest=hostile, source_root=repo)


def _rewrite_wheel_record(members: dict[str, bytes]) -> None:
    record = "netbox_sdk-0.0.11rc2.dist-info/RECORD"
    members.pop(record, None)
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    for name, payload in members.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode()
        writer.writerow((name, f"sha256={digest}", len(payload)))
    writer.writerow((record, "", ""))
    members[record] = output.getvalue().encode()


@pytest.mark.parametrize(
    ("original", "replacement"),
    [
        (b"Metadata-Version: 2.4", b"Metadata-Version: 2.3"),
        (
            b"Author-email: Release Author <author@example.invalid>",
            b"Author-email: Hostile <hostile@example.invalid>",
        ),
        (
            b"Maintainer-email: Release Maintainer <maintainer@example.invalid>",
            b"Maintainer-email: Hostile <hostile@example.invalid>",
        ),
        (b"Keywords: fixture,release", b"Keywords: hostile"),
        (b"Classifier: Typing :: Typed", b"Classifier: Private :: Hostile"),
        (
            b"Project-URL: Homepage, https://example.invalid/project",
            b"Project-URL: Homepage, https://hostile.invalid/project",
        ),
        (b"Description-Content-Type: text/markdown", b"Description-Content-Type: text/html"),
        (b"\n\nfixture\n", b"\n\nhostile\n"),
    ],
)
@pytest.mark.parametrize("metadata_location", ["wheel", "sdist-root", "sdist-egg"])
def test_all_core_metadata_and_readme_copies_are_source_authoritative(
    tmp_path: Path,
    metadata_location: str,
    original: bytes,
    replacement: bytes,
) -> None:
    transfer, manifest, repo = _transfer(tmp_path)
    if metadata_location == "wheel":
        members = _wheel_members(repo)
        metadata_name = "netbox_sdk-0.0.11rc2.dist-info/METADATA"
        members[metadata_name] = members[metadata_name].replace(original, replacement, 1)
        _rewrite_wheel_record(members)
        _write_wheel(transfer / WHEEL, members)
    else:
        members = _sdist_members(repo)
        metadata_name = (
            "PKG-INFO" if metadata_location == "sdist-root" else "netbox_sdk.egg-info/PKG-INFO"
        )
        members[metadata_name] = members[metadata_name].replace(original, replacement, 1)
        _write_sdist(transfer / SDIST, members)
    records = tuple(
        ArtifactRecord(
            path.name,
            path.stat().st_size,
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        for path in (transfer / WHEEL, transfer / SDIST)
    )
    mutated = TransferManifest(
        PACKAGE,
        VERSION,
        manifest.source_sha,
        records,
        manifest.source_epoch,
    )
    with pytest.raises(ReleaseError, match="metadata"):
        validate_archive_source_binding(
            transfer_dir=transfer,
            manifest=mutated,
            source_root=repo,
        )


@pytest.mark.parametrize(
    "injected_header",
    [
        b"Author: Hostile Builder\n",
        b"License: permissive-ish\n",
        b"X-Builder-Directive: run-this\n",
        b"Summary: Duplicate summary\n",
    ],
)
@pytest.mark.parametrize("metadata_location", ["wheel", "sdist-root", "sdist-egg"])
def test_complete_metadata_header_multimap_rejects_injected_and_duplicate_headers(
    tmp_path: Path,
    metadata_location: str,
    injected_header: bytes,
) -> None:
    transfer, manifest, repo = _transfer(tmp_path)
    if metadata_location == "wheel":
        members = _wheel_members(repo)
        metadata_name = "netbox_sdk-0.0.11rc2.dist-info/METADATA"
        members[metadata_name] = members[metadata_name].replace(
            b"\n\n", b"\n" + injected_header + b"\n", 1
        )
        _rewrite_wheel_record(members)
        _write_wheel(transfer / WHEEL, members)
    else:
        members = _sdist_members(repo)
        metadata_name = (
            "PKG-INFO" if metadata_location == "sdist-root" else "netbox_sdk.egg-info/PKG-INFO"
        )
        members[metadata_name] = members[metadata_name].replace(
            b"\n\n", b"\n" + injected_header + b"\n", 1
        )
        _write_sdist(transfer / SDIST, members)
    mutated = _rewrite_transfer_manifest(transfer, manifest)
    with pytest.raises(ReleaseError, match="metadata"):
        validate_archive_source_binding(
            transfer_dir=transfer,
            manifest=mutated,
            source_root=repo,
        )


def test_wheel_record_rejects_unbound_or_mismatched_members() -> None:
    with pytest.raises(ReleaseError, match="exact member set"):
        _validate_wheel_record(
            record_bytes=b"a,sha256=bad,1\n",
            member_bytes={"a": b"x", "extra": b"y"},
            record_name="record",
        )


def _manifest() -> TransferManifest:
    return TransferManifest(
        PACKAGE,
        VERSION,
        SOURCE_SHA,
        (ArtifactRecord(WHEEL, 5, "1" * 64), ArtifactRecord(SDIST, 5, "2" * 64)),
        SOURCE_EPOCH,
    )


def test_credential_free_validation_creates_a_private_exact_seal(tmp_path: Path) -> None:
    transfer, manifest, repo = _transfer(tmp_path)
    sealed = tmp_path / "sealed"
    incoming = {name: (transfer / name).read_bytes() for name in (WHEEL, SDIST, MANIFEST_NAME)}
    assert (
        seal_transfer(
            transfer_dir=transfer,
            sealed_dir=sealed,
            source_root=repo,
            expected_package=PACKAGE,
            expected_version=VERSION,
            expected_source_sha=manifest.source_sha,
            expected_source_epoch=manifest.source_epoch,
        )
        == manifest
    )
    assert {name: (transfer / name).read_bytes() for name in incoming} == incoming
    assert {path.name for path in sealed.iterdir()} == {SEAL_NAME, WHEEL, SDIST}
    assert stat.S_IMODE(sealed.stat().st_mode) == 0o500
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o400 for path in sealed.iterdir())
    assert (
        validate_seal(
            sealed_dir=sealed,
            expected_package=PACKAGE,
            expected_version=VERSION,
            expected_source_sha=manifest.source_sha,
            expected_source_epoch=manifest.source_epoch,
        )
        == manifest
    )

    sealed.chmod(0o700)
    for path in sealed.iterdir():
        path.chmod(0o600)
    assert (
        harden_downloaded_seal(
            sealed_dir=sealed,
            expected_package=PACKAGE,
            expected_version=VERSION,
            expected_source_sha=manifest.source_sha,
            expected_source_epoch=manifest.source_epoch,
        )
        == manifest
    )

    artifact = sealed / WHEEL
    artifact.chmod(0o600)
    artifact.write_bytes(artifact.read_bytes() + b"hostile")
    artifact.chmod(0o400)
    with pytest.raises(ReleaseError, match="does not match"):
        validate_seal(
            sealed_dir=sealed,
            expected_package=PACKAGE,
            expected_version=VERSION,
            expected_source_sha=manifest.source_sha,
            expected_source_epoch=manifest.source_epoch,
        )


def test_token_command_uses_only_small_seal_validation_and_registry_operations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transfer, manifest, repo = _transfer(tmp_path)
    sealed = tmp_path / "sealed"
    seal_transfer(
        transfer_dir=transfer,
        sealed_dir=sealed,
        source_root=repo,
        expected_package=PACKAGE,
        expected_version=VERSION,
        expected_source_sha=manifest.source_sha,
        expected_source_epoch=manifest.source_epoch,
    )

    def forbidden(*args: object, **kwargs: object) -> None:
        del args, kwargs
        pytest.fail("complex source/archive parser ran while the package token was live")

    monkeypatch.setattr("scripts.gitea_release.validate_transfer", forbidden)
    monkeypatch.setattr("scripts.gitea_release.validate_trusted_source_checkout", forbidden)
    monkeypatch.setattr("scripts.gitea_release.validate_archive_source_binding", forbidden)

    class FakeClient:
        origin = "https://packages.example.invalid"

        def __init__(self, **kwargs: object) -> None:
            assert kwargs["token"] == "ephemeral-secret"

        def remaining(self) -> float:
            return 10.0

    class FakeRegistry:
        def __init__(self, **kwargs: object) -> None:
            assert isinstance(kwargs["client"], FakeClient)

    validations: list[bool] = []

    def fake_reconcile(**kwargs: object) -> str:
        assert kwargs["manifest"] == manifest
        callback = kwargs["revalidate_seal"]
        assert callable(callback)
        callback()
        validations.append(True)
        return "already exact"

    monkeypatch.setattr("scripts.gitea_release.BoundedHttpClient", FakeClient)
    monkeypatch.setattr("scripts.gitea_release.GiteaRegistry", FakeRegistry)
    monkeypatch.setattr("scripts.gitea_release.reconcile_publication", fake_reconcile)
    monkeypatch.setenv("GITEA_TOKEN", "ephemeral-secret")
    args = SimpleNamespace(
        token_env="GITEA_TOKEN",
        sealed_dir=sealed,
        package=PACKAGE,
        version=VERSION,
        source_sha=manifest.source_sha,
        source_epoch=manifest.source_epoch,
        server_url="https://packages.example.invalid",
        deadline_seconds=180.0,
        request_timeout=15.0,
        owner="emersonfelipesp",
        repository="netbox-sdk",
        username="emersonfelipesp",
        python=Path("/trusted/python"),
    )
    assert _main_publish(args) == 0
    assert validations == [True]


def test_twine_receives_only_the_minimal_allowlisted_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        captured["command"] = command
        captured.update(kwargs)
        return SimpleNamespace(returncode=0)

    monkeypatch.setenv("HOSTILE_PARENT_VALUE", "must-not-flow")
    monkeypatch.setattr("scripts.gitea_release.subprocess.run", fake_run)
    _run_twine_upload(
        python=Path("/trusted/python"),
        server_url="https://packages.example.invalid",
        owner="emersonfelipesp",
        username="emersonfelipesp",
        token="ephemeral-secret",
        artifact_paths=(tmp_path / WHEEL, tmp_path / SDIST),
        timeout=10,
    )
    assert captured["env"] == {
        "PYTHONNOUSERSITE": "1",
        "PYTHONUTF8": "1",
        "TWINE_NON_INTERACTIVE": "1",
        "TWINE_PASSWORD": "ephemeral-secret",
        "TWINE_USERNAME": "emersonfelipesp",
    }
    assert "ephemeral-secret" not in " ".join(captured["command"])


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ((ArtifactRecord(WHEEL, 5, "1" * 64),), "partially"),
        (
            (
                ArtifactRecord(WHEEL, 5, "1" * 64),
                ArtifactRecord(SDIST, 5, "2" * 64),
                ArtifactRecord("extra.whl", 1, "3" * 64),
            ),
            "extra",
        ),
        (
            (ArtifactRecord(WHEEL, 6, "1" * 64), ArtifactRecord(SDIST, 5, "2" * 64)),
            "mismatch",
        ),
    ],
)
def test_remote_partial_extra_and_mismatch_fail_closed(
    rows: tuple[ArtifactRecord, ...], message: str
) -> None:
    with pytest.raises(ReleaseError, match=message):
        classify_remote_state(RemoteState(True, "emersonfelipesp/netbox-sdk", rows), _manifest())


class _Registry:
    expected_repository = "emersonfelipesp/netbox-sdk"

    def __init__(self, states: list[RemoteState], *, link_error: bool = False) -> None:
        self.states = states
        self.link_error = link_error
        self.link_calls = 0

    def inspect(self, manifest: TransferManifest) -> RemoteState:
        del manifest
        return self.states.pop(0)

    def link(self, manifest: TransferManifest) -> None:
        del manifest
        self.link_calls += 1
        if self.link_error:
            raise OSError("ambiguous")


def _state(*, exists: bool = True, repository: str | None = None) -> RemoteState:
    return RemoteState(exists, repository, _manifest().artifacts if exists else ())


def test_existing_exact_associated_state_is_idempotent() -> None:
    registry = _Registry(
        [_state(repository=registry_name) for registry_name in ["emersonfelipesp/netbox-sdk"]] * 2
    )
    uploads: list[bool] = []
    result = reconcile_publication(
        manifest=_manifest(),
        registry=registry,
        upload=lambda: uploads.append(True),
        revalidate_seal=lambda: None,
    )
    assert result == "already exact"
    assert uploads == []
    assert registry.link_calls == 0


def test_wrong_repository_association_fails_before_upload() -> None:
    uploads: list[bool] = []
    with pytest.raises(ReleaseError, match="different repository"):
        reconcile_publication(
            manifest=_manifest(),
            registry=_Registry([_state(repository="other/repository")]),
            upload=lambda: uploads.append(True),
            revalidate_seal=lambda: None,
        )
    assert uploads == []


class _RouteClient:
    def __init__(self, manifest: TransferManifest) -> None:
        self.manifest = manifest
        self.paths: list[tuple[str, str]] = []

    def request_json(self, *, path: str, allow_not_found: bool = False) -> object:
        del allow_not_found
        self.paths.append(("GET", path))
        if path.endswith("/files"):
            return [
                {"name": row.name, "size": row.size, "sha256": row.sha256}
                for row in self.manifest.artifacts
            ]
        return {
            "type": "pypi",
            "name": PACKAGE,
            "version": VERSION,
            "repository": {"full_name": "emersonfelipesp/netbox-sdk"},
        }

    def request_bytes(self, *, method: str, path: str, maximum: int) -> bytes:
        self.paths.append((method, path))
        record = next(row for row in self.manifest.artifacts if path.endswith(row.name))
        payload = b"wheel" if record.name == WHEEL else b"sdist"
        assert len(payload) <= maximum
        return payload

    def post_empty(self, *, path: str) -> None:
        self.paths.append(("POST", path))


def test_registry_uses_exact_gitea_routes_and_downloads_remote_content() -> None:
    manifest = TransferManifest(
        PACKAGE,
        VERSION,
        SOURCE_SHA,
        tuple(
            ArtifactRecord(name, len(payload), hashlib.sha256(payload).hexdigest())
            for name, payload in ((WHEEL, b"wheel"), (SDIST, b"sdist"))
        ),
        SOURCE_EPOCH,
    )
    client = _RouteClient(manifest)
    registry = GiteaRegistry(client=client, owner="emersonfelipesp", repository="netbox-sdk")
    assert classify_remote_state(registry.inspect(manifest), manifest) == "exact"
    registry.link(manifest)
    assert client.paths == [
        ("GET", "/api/v1/packages/emersonfelipesp/pypi/netbox-sdk/0.0.11rc2"),
        ("GET", "/api/v1/packages/emersonfelipesp/pypi/netbox-sdk/0.0.11rc2/files"),
        (
            "GET",
            "/api/packages/emersonfelipesp/pypi/files/netbox-sdk/0.0.11rc2/"
            "netbox_sdk-0.0.11rc2-py3-none-any.whl",
        ),
        (
            "GET",
            "/api/packages/emersonfelipesp/pypi/files/netbox-sdk/0.0.11rc2/"
            "netbox_sdk-0.0.11rc2.tar.gz",
        ),
        ("POST", "/api/v1/packages/emersonfelipesp/pypi/netbox-sdk/-/link/netbox-sdk"),
    ]


@pytest.mark.parametrize("upload_raises", [False, True])
def test_absent_upload_recovers_only_to_exact_state_and_revalidates(
    upload_raises: bool,
) -> None:
    registry = _Registry(
        [_state(exists=False), _state(), _state(repository="emersonfelipesp/netbox-sdk")]
    )
    validations: list[bool] = []

    def upload() -> None:
        if upload_raises:
            raise OSError("ambiguous")

    assert (
        reconcile_publication(
            manifest=_manifest(),
            registry=registry,
            upload=upload,
            revalidate_seal=lambda: validations.append(True),
        )
        == "published exact"
    )
    assert registry.link_calls == 1
    assert len(validations) == 3


def test_ambiguous_association_post_recovers_with_get_first_exact_state() -> None:
    registry = _Registry(
        [
            _state(),
            _state(repository="emersonfelipesp/netbox-sdk"),
            _state(repository="emersonfelipesp/netbox-sdk"),
        ],
        link_error=True,
    )
    assert (
        reconcile_publication(
            manifest=_manifest(),
            registry=registry,
            upload=lambda: pytest.fail("must not upload"),
            revalidate_seal=lambda: None,
        )
        == "already exact"
    )


class _Socket:
    def __init__(self) -> None:
        self.timeout = 0.0
        self.timeouts: list[float] = []

    def settimeout(self, value: float) -> None:
        self.timeout = value
        self.timeouts.append(value)


class _Response:
    def __init__(
        self,
        *,
        status: int = 200,
        chunks: list[bytes] | None = None,
        length: str | None = None,
        delay: float = 0,
        clock: list[float] | None = None,
        sock: _Socket | None = None,
    ) -> None:
        self.status = status
        self.chunks = chunks or []
        self.length = length
        self.delay = delay
        self.clock = clock
        self.sock = sock

    def getheader(self, name: str) -> str | None:
        return self.length if name == "Content-Length" else None

    def read(self, maximum: int) -> bytes:
        del maximum
        if self.delay and self.clock is not None and self.sock is not None:
            if self.delay > self.sock.timeout:
                self.clock[0] += self.sock.timeout
                raise TimeoutError
            self.clock[0] += self.delay
        return self.chunks.pop(0) if self.chunks else b""


class _Connection:
    def __init__(self, response_factory: Callable[[_Socket], _Response]) -> None:
        self.sock = _Socket()
        self.response = response_factory(self.sock)
        self.headers: dict[str, str] = {}

    def request(self, method: str, url: str, body: bytes | None, headers: dict[str, str]) -> None:
        del method, url, body
        self.headers = headers

    def getresponse(self) -> _Response:
        return self.response

    def close(self) -> None:
        pass


def test_http_client_enforces_a_shrinking_whole_operation_deadline() -> None:
    clock = [0.0]
    connection = _Connection(
        lambda sock: _Response(
            chunks=[b"a"] * 5,
            delay=1.1,
            clock=clock,
            sock=sock,
        )
    )
    client = BoundedHttpClient(
        server_url="https://packages.example.invalid",
        token="secret-value",
        deadline_seconds=3,
        request_timeout=2,
        connection_factory=lambda host, timeout: connection,
        clock=lambda: clock[0],
    )
    with pytest.raises(ReleaseError, match="failed or timed out") as exc_info:
        client.request_bytes(method="GET", path="/bounded", maximum=10)
    assert clock[0] == pytest.approx(3)
    assert connection.sock.timeouts == pytest.approx([2, 1.9, 0.8])
    assert "secret-value" not in str(exc_info.value)


@pytest.mark.parametrize(
    "response",
    [_Response(status=302), _Response(length="100", chunks=[b"x"])],
)
def test_http_client_refuses_redirects_and_oversized_bodies(response: _Response) -> None:
    connection = _Connection(lambda sock: response)
    client = BoundedHttpClient(
        server_url="https://packages.example.invalid",
        token="secret-value",
        deadline_seconds=3,
        connection_factory=lambda host, timeout: connection,
    )
    with pytest.raises(ReleaseError):
        client.request_bytes(method="GET", path="/bounded", maximum=10)


def test_gitea_tag_policy_and_validated_action_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    validate_gitea_candidate_tag(event_name="push", ref_name=f"v{VERSION}", version=VERSION)
    for invalid in ("v0.0.11rc1", "0.0.11rc2", "v0.0.11"):
        with pytest.raises(RuntimeError):
            validate_gitea_candidate_tag(event_name="push", ref_name=invalid, version=VERSION)
    with pytest.raises(RuntimeError, match="Unsupported"):
        validate_gitea_candidate_tag(
            event_name="workflow_dispatch", ref_name=f"v{VERSION}", version=VERSION
        )
    output = tmp_path / "output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    assert _main_validate_tag(SimpleNamespace(event_name="push", tag=f"v{VERSION}")) == 0
    assert output.read_text() == f"tag=v{VERSION}\n"


def _tag_protection_evidence() -> list[dict[str, object]]:
    return [
        {
            "id": 7,
            "name_pattern": "v*",
            "whitelist_usernames": ["emersonfelipesp"],
            "whitelist_teams": [],
            "created_at": "2026-08-12T00:00:00Z",
            "updated_at": "2026-08-12T00:00:00Z",
        }
    ]


def test_repository_release_tag_policy_requires_exact_server_evidence(tmp_path: Path) -> None:
    policy = Path(".gitea/release-tag-policy.json")
    evidence_file = tmp_path / "tag-protections.json"
    evidence_file.write_text(json.dumps(_tag_protection_evidence()), encoding="utf-8")
    validate_release_tag_protection(policy_file=policy, evidence_file=evidence_file)
    command = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.gitea_release",
            "validate-tag-protection",
            "--policy-file",
            str(policy),
            "--evidence-file",
            str(evidence_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert command.returncode == 0, command.stderr
    assert "matches repository policy" in command.stdout

    mutations: tuple[Callable[[list[dict[str, object]]], None], ...] = (
        lambda rows: rows[0].__setitem__("name_pattern", "v*rc*"),
        lambda rows: rows[0].__setitem__("whitelist_usernames", []),
        lambda rows: rows[0].__setitem__(
            "whitelist_usernames", ["emersonfelipesp", "another-user"]
        ),
        lambda rows: rows[0].__setitem__("whitelist_teams", ["release-team"]),
        lambda rows: rows.append(dict(rows[0], id=8, name_pattern="v0.*")),
        lambda rows: rows[0].__setitem__("unexpected", True),
    )
    for mutate in mutations:
        evidence = _tag_protection_evidence()
        mutate(evidence)
        evidence_file.write_text(json.dumps(evidence), encoding="utf-8")
        with pytest.raises(ReleaseError, match="release-tag|Release-tag|Server-side"):
            validate_release_tag_protection(policy_file=policy, evidence_file=evidence_file)

    policy_data = json.loads(policy.read_text(encoding="utf-8"))
    policy_data["required_rule"]["name_pattern"] = "v*rc*"
    altered_policy = tmp_path / "policy.json"
    altered_policy.write_text(json.dumps(policy_data), encoding="utf-8")
    evidence_file.write_text(json.dumps(_tag_protection_evidence()), encoding="utf-8")
    with pytest.raises(ReleaseError, match="policy"):
        validate_release_tag_protection(
            policy_file=altered_policy,
            evidence_file=evidence_file,
        )


def test_publisher_helper_import_depends_on_exact_tool_root_layout(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    tool_root = workspace / "publisher-tool"
    workspace.mkdir()
    shutil.copytree(Path("scripts"), tool_root / "scripts")
    environment = {
        key: value for key, value in os.environ.items() if key not in {"PYTHONPATH", "PYTHONHOME"}
    }
    command = [sys.executable, "-m", "scripts.gitea_release", "--help"]
    outside = subprocess.run(
        command,
        cwd=workspace,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert outside.returncode != 0
    assert "No module named 'scripts'" in outside.stderr
    inside = subprocess.run(
        command,
        cwd=tool_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert inside.returncode == 0, inside.stderr


def test_release_source_must_equal_canonical_main(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Release Test")
    _git(repo, "config", "user.email", "release@example.invalid")
    (repo / "file").write_text("one")
    first = _commit(repo)
    assert (
        validate_exact_canonical_source(candidate_ref=first, canonical_main_ref=first, repo=repo)
        == first
    )
    (repo / "file").write_text("two")
    second = _commit(repo)
    with pytest.raises(RuntimeError, match="must equal"):
        validate_exact_canonical_source(candidate_ref=first, canonical_main_ref=second, repo=repo)


def _assert_workflow_policy(text: str) -> None:
    required = (
        '      - "v*rc*"',
        "group: private-package-${{ github.repository }}-netbox-sdk-${{ github.ref }}",
        "runs-on: ci-untrusted-python312",
        "runs-on: mirror-host",
        "contents: read",
        "packages: write",
        "--no-isolation",
        "uv sync --locked --only-group publish --no-install-project",
        "uv 0.11.28",
        "3.12.13",
        "for BUILD_ID in a b",
        'SOURCE_DATE_EPOCH="$SOURCE_EPOCH" PYTHONHASHSEED=0',
        "normalize-build",
        "compare-builds",
        "seal-transfer",
        '--sealed-dir "$PUBLISH_ROOT/sealed"',
        "timeout-minutes: 5",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
        "actions/download-artifact@fa0a91b85d4f404e444e00e005971372dc801d16",
        "token: ''",
        "GITEA_TOKEN: ${{ github.token }}",
        'test "$VERIFIED_SOURCE_SHA" = "$EVENT_SOURCE_SHA"',
        'cd "$TOOL_ROOT"',
    )
    assert all(value in text for value in required)
    assert "GITHUB_ENV" not in text
    assert text.count("${{ github.token }}") == 1
    assert text.count("runs-on: ci-untrusted-python312") == 1
    assert text.count("runs-on: mirror-host") == 2
    assert text.count("uv 0.11.28") == 3
    assert text.count("contents: read") == 4
    assert text.count("packages: write") == 1
    assert text.count("token: ''") == 2
    assert "workflow_dispatch:" not in text
    assert "pull_request:" not in text and "release:" not in text
    concurrency = next(line for line in text.splitlines() if line.lstrip().startswith("group:"))
    assert "run_id" not in concurrency and "run_attempt" not in concurrency
    publish_step = text.index("- name: Publish the sealed exact package")
    seal_step = text.index(
        "- name: Validate source and create private publication seal without credentials"
    )
    assert publish_step > seal_step
    assert text.index("${{ github.token }}") > publish_step
    assert "${{ github.token }}" not in text[:publish_step]
    token_block = text[publish_step:]
    assert "--source-root" not in token_block
    assert "--transfer-dir" not in token_block
    for line in text.splitlines():
        if "uses:" in line:
            assert "@" in line and len(line.split("@", 1)[1].split()[0]) == 40
    assert "${{ inputs." not in text
    parsed = yaml.load(text, Loader=yaml.BaseLoader)
    assert parsed["on"] == {"push": {"tags": ["v*rc*"]}}
    jobs = parsed["jobs"]
    assert set(jobs) == {"build-candidate", "verify-and-seal", "publish-candidate"}
    assert jobs["build-candidate"]["permissions"] == {"contents": "read"}
    assert jobs["verify-and-seal"]["needs"] == "build-candidate"
    assert jobs["verify-and-seal"]["permissions"] == {"contents": "read"}
    assert jobs["publish-candidate"]["needs"] == "verify-and-seal"
    assert jobs["publish-candidate"]["permissions"] == {
        "contents": "read",
        "packages": "write",
    }
    verify_job = str(jobs["verify-and-seal"])
    publisher_job = str(jobs["publish-candidate"])
    assert "seal-transfer" in verify_job and "GITEA_TOKEN" not in verify_job
    assert "netbox-sdk-private-seal" in verify_job
    assert "netbox-sdk-private-seal" in publisher_job
    assert "seal-transfer" not in publisher_job
    assert "validate_archive_source_binding" not in publisher_job
    assert "--source-root" not in publisher_job and "--transfer-dir" not in publisher_job
    assert publisher_job.count("${{ github.token }}") == 1
    publisher_checkout = jobs["publish-candidate"]["steps"][0]
    assert publisher_checkout["with"]["ref"] == "${{ github.sha }}"
    assert publisher_checkout["with"]["token"] == ""
    authority = jobs["publish-candidate"]["steps"][1]
    assert authority["id"] == "authority"
    assert authority["env"] == {
        "EVENT_SOURCE_SHA": "${{ github.sha }}",
        "TOOL_ROOT": "${{ github.workspace }}/publisher-tool-${{ github.run_id }}-${{ github.run_attempt }}",
        "VERIFIED_SOURCE_SHA": "${{ needs.verify-and-seal.outputs.source_sha }}",
    }
    assert 'test "$VERIFIED_SOURCE_SHA" = "$EVENT_SOURCE_SHA"' in authority["run"]
    assert 'git -C "$TOOL_ROOT" rev-parse HEAD' in authority["run"]
    assert 'git -C "$TOOL_ROOT" show -s --format=%ct "$EVENT_SOURCE_SHA"' in authority["run"]
    final_steps = {
        step["name"]: step for step in jobs["publish-candidate"]["steps"] if "run" in step
    }
    for name in (
        "Restore and validate private seal permissions",
        "Publish the sealed exact package",
    ):
        step = final_steps[name]
        assert step["env"]["TOOL_ROOT"] == authority["env"]["TOOL_ROOT"]
        assert step["env"]["SOURCE_SHA"] == "${{ github.sha }}"
        assert step["env"]["SOURCE_EPOCH"] == "${{ steps.authority.outputs.source_epoch }}"
        assert 'cd "$TOOL_ROOT"' in step["run"]
        assert step["run"].index('cd "$TOOL_ROOT"') < step["run"].index("-m scripts.gitea_release")


def test_private_registry_workflow_security_contract_and_mutations() -> None:
    workflow = Path(".gitea/workflows/publish-package.yml").read_text(encoding="utf-8")
    _assert_workflow_policy(workflow)
    mutations = (
        ("  push:\n", "  workflow_dispatch:\n"),
        ("packages: write", "packages: read"),
        ("runs-on: mirror-host", "runs-on: ci-untrusted-python312"),
        ("token: ''", "token: ${{ github.token }}"),
        ("--no-isolation", "--isolation"),
        ("uv 0.11.28", "uv 0.11.29"),
        ("@ea165f8d65b6e75b540449e92b4886f43607fa02", "@v4"),
        (
            "group: private-package-${{ github.repository }}-netbox-sdk-${{ github.ref }}",
            "group: private-package-${{ github.run_id }}",
        ),
        ("for BUILD_ID in a b", "for BUILD_ID in a"),
        ("compare-builds", "compare_artifacts"),
        ("timeout-minutes: 5", "timeout-minutes-disabled: 5"),
        (
            "ref: ${{ github.sha }}",
            "ref: main",
        ),
        (
            'test "$VERIFIED_SOURCE_SHA" = "$EVENT_SOURCE_SHA"',
            'test -n "$VERIFIED_SOURCE_SHA"',
        ),
        ('cd "$TOOL_ROOT"', 'cd "$PUBLISH_ROOT"'),
        (
            "SOURCE_SHA: ${{ github.sha }}",
            "SOURCE_SHA: ${{ needs.verify-and-seal.outputs.source_sha }}",
        ),
    )
    for old, new in mutations:
        mutated = workflow.replace(old, new, 1)
        with pytest.raises(AssertionError):
            _assert_workflow_policy(mutated)
    (seal_transfer,)
    (validate_seal,)


def test_release_docs_require_external_tag_policy_preflight_and_terminal_recovery() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    compact_readme = " ".join(readme.split())
    api_command = (
        "nms git api GET /repos/emersonfelipesp/netbox-sdk/tag_protections "
        "\\ --output /tmp/netbox-sdk-tag-protections.json"
    )
    validator = (
        "python -m scripts.gitea_release validate-tag-protection "
        "\\ --policy-file .gitea/release-tag-policy.json "
        "\\ --evidence-file /tmp/netbox-sdk-tag-protections.json"
    )
    assert api_command in compact_readme
    assert validator in compact_readme
    assert readme.index("nms git api GET") < readme.index("git tag -a v0.0.11rc2")
    assert readme.index("validate-tag-protection") < readme.index("git tag -a v0.0.11rc2")
    assert "workflow cannot and does not self-verify" in compact_readme
    assert "never delete files, overwrite them, or retry the same version" in compact_readme
    assert "git push gitea v0.0.11rc2" in readme

    policy = json.loads(Path(".gitea/release-tag-policy.json").read_text(encoding="utf-8"))
    assert policy == {
        "schema": 1,
        "owner": "emersonfelipesp",
        "repository": "netbox-sdk",
        "api_path": "/repos/emersonfelipesp/netbox-sdk/tag_protections",
        "required_rule": {
            "name_pattern": "v*",
            "whitelist_usernames": ["emersonfelipesp"],
            "whitelist_teams": [],
        },
    }
    for guide in (
        "CLAUDE.md",
        "AGENTS.md",
        ".github/CLAUDE.md",
        ".github/AGENTS.md",
    ):
        text = " ".join(Path(guide).read_text(encoding="utf-8").split())
        assert "/repos/emersonfelipesp/netbox-sdk/tag_protections" in text
        assert "not self-verified" in text
        assert "next unused `rcN`" in text
