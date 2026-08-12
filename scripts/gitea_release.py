"""Build-to-publisher transfer and exact-state private registry publication.

The credential-free builder creates a closed transfer set: one universal wheel,
one source distribution, and a manifest binding their names, sizes, SHA-256
digests, project version, and canonical source commit.  The publisher validates
that set without importing or executing package code, compares it with the
registry, and publishes only from an entirely absent state.  An already exact
state is success; partial, extra, mismatched, or wrongly associated states fail
closed.
"""

from __future__ import annotations

import argparse
import base64
import csv
import gzip
import hashlib
import http.client
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import tomllib
import urllib.parse
import zipfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from email.parser import BytesParser
from pathlib import Path
from typing import Any, BinaryIO, Protocol

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import Version

from scripts.prepare_testpypi_upload import validate_local_artifacts
from scripts.release_policy import (
    ROOT,
    release_context,
    validate_exact_canonical_source,
    validate_gitea_candidate_tag,
    validate_immutable_tag,
    validated_commit_epoch,
)

MANIFEST_NAME = "release-manifest.json"
MANIFEST_SCHEMA = 2
SEAL_NAME = "release-seal.json"
SEAL_SCHEMA = 1
MAX_MANIFEST_BYTES = 64 * 1024
MAX_SEAL_BYTES = 16 * 1024
MAX_TAG_POLICY_BYTES = 16 * 1024
MAX_TAG_POLICY_EVIDENCE_BYTES = 64 * 1024
MAX_JSON_BYTES = 1024 * 1024
MAX_ARTIFACT_BYTES = 128 * 1024 * 1024
MAX_ARCHIVE_MEMBERS = 4096
MAX_UNPACKED_BYTES = 256 * 1024 * 1024
SHA256_RE = re.compile(r"[0-9a-f]{64}")
FULL_SHA_RE = re.compile(r"[0-9a-f]{40}")
SAFE_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


class ReleaseError(RuntimeError):
    """A secret-silent release validation or publication failure."""


@dataclass(frozen=True)
class ArtifactRecord:
    name: str
    size: int
    sha256: str


@dataclass(frozen=True)
class TransferManifest:
    package: str
    version: str
    source_sha: str
    artifacts: tuple[ArtifactRecord, ...]
    source_epoch: int

    def artifact_map(self) -> dict[str, ArtifactRecord]:
        """Return manifest artifacts keyed by their exact filename."""
        return {artifact.name: artifact for artifact in self.artifacts}


@dataclass(frozen=True)
class RemoteState:
    version_exists: bool
    repository: str | None
    artifacts: tuple[ArtifactRecord, ...]

    def artifact_map(self) -> dict[str, ArtifactRecord]:
        """Return remote artifacts keyed by their exact filename."""
        return {artifact.name: artifact for artifact in self.artifacts}


def _json_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ReleaseError("JSON document contains duplicate keys")
        value[key] = item
    return value


def _load_json_bytes(payload: bytes, *, description: str) -> Any:
    try:
        return json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_json_without_duplicate_keys,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReleaseError(f"{description} is not valid bounded JSON") from exc


def _load_bounded_json_file(path: Path, *, maximum: int, description: str) -> Any:
    descriptor = -1
    try:
        file_stat = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(file_stat.st_mode):
            raise ReleaseError(f"{description} must be a regular non-symlink file")
        if file_stat.st_size > maximum:
            raise ReleaseError(f"{description} exceeds the allowed size")
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        opened_stat = os.fstat(descriptor)
        identity = lambda value: (  # noqa: E731 - compact immutable file identity tuple.
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )
        if identity(opened_stat) != identity(file_stat):
            raise ReleaseError(f"{description} changed before it was opened")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            payload = stream.read(maximum + 1)
        if len(payload) > maximum or identity(os.fstat(descriptor)) != identity(file_stat):
            raise ReleaseError(f"{description} changed or exceeded its bound")
    except OSError as exc:
        raise ReleaseError(f"{description} is unavailable") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    return _load_json_bytes(payload, description=description)


def validate_release_tag_protection(*, policy_file: Path, evidence_file: Path) -> None:
    """Validate separately captured server-side release-tag protection evidence."""
    policy = _load_bounded_json_file(
        policy_file,
        maximum=MAX_TAG_POLICY_BYTES,
        description="Release-tag policy",
    )
    expected_path = "/repos/emersonfelipesp/netbox-sdk/tag_protections"
    if not isinstance(policy, dict) or set(policy) != {
        "schema",
        "owner",
        "repository",
        "api_path",
        "required_rule",
    }:
        raise ReleaseError("Release-tag policy schema is not exact")
    if (
        type(policy["schema"]) is not int
        or policy["schema"] != 1
        or policy["owner"] != "emersonfelipesp"
        or policy["repository"] != "netbox-sdk"
        or policy["api_path"] != expected_path
    ):
        raise ReleaseError("Release-tag policy identity is not exact")
    expected_rule = policy["required_rule"]
    if not isinstance(expected_rule, dict) or set(expected_rule) != {
        "name_pattern",
        "whitelist_usernames",
        "whitelist_teams",
    }:
        raise ReleaseError("Release-tag protection rule schema is not exact")
    if expected_rule != {
        "name_pattern": "v*",
        "whitelist_usernames": ["emersonfelipesp"],
        "whitelist_teams": [],
    }:
        raise ReleaseError("Release-tag protection rule is not the required closed policy")

    evidence = _load_bounded_json_file(
        evidence_file,
        maximum=MAX_TAG_POLICY_EVIDENCE_BYTES,
        description="Release-tag protection evidence",
    )
    if not isinstance(evidence, list) or len(evidence) != 1:
        raise ReleaseError("Release-tag protection evidence must contain the exact single rule")
    actual = evidence[0]
    if not isinstance(actual, dict) or set(actual) != {
        "id",
        "name_pattern",
        "whitelist_usernames",
        "whitelist_teams",
        "created_at",
        "updated_at",
    }:
        raise ReleaseError("Release-tag protection evidence schema is not exact")
    if (
        type(actual["id"]) is not int
        or actual["id"] <= 0
        or not isinstance(actual["created_at"], str)
        or not actual["created_at"]
        or not isinstance(actual["updated_at"], str)
        or not actual["updated_at"]
        or {key: actual[key] for key in expected_rule} != expected_rule
    ):
        raise ReleaseError("Server-side release-tag protection does not match policy")


def _artifact_names(package: str, version: str) -> tuple[str, str]:
    normalized_package = canonicalize_name(package).replace("-", "_")
    normalized_version = str(Version(version))
    return (
        f"{normalized_package}-{normalized_version}-py3-none-any.whl",
        f"{normalized_package}-{normalized_version}.tar.gz",
    )


def _hash_stream(stream: BinaryIO, *, maximum: int = MAX_ARTIFACT_BYTES) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        size += len(chunk)
        if size > maximum:
            raise ReleaseError("Release artifact exceeds the allowed size")
        digest.update(chunk)
    return size, digest.hexdigest()


def _safe_file_record(path: Path) -> ArtifactRecord:
    if path.name != Path(path.name).name or SAFE_NAME_RE.fullmatch(path.name) is None:
        raise ReleaseError("Release artifact has an unsafe filename")
    try:
        file_stat = path.lstat()
    except OSError as exc:
        raise ReleaseError("Release artifact is unavailable") from exc
    if not stat.S_ISREG(file_stat.st_mode) or path.is_symlink():
        raise ReleaseError("Release artifact must be a regular non-symlink file")
    try:
        with path.open("rb") as stream:
            size, digest = _hash_stream(stream)
    except OSError as exc:
        raise ReleaseError("Release artifact could not be read") from exc
    if size != file_stat.st_size:
        raise ReleaseError("Release artifact changed while it was being inspected")
    return ArtifactRecord(name=path.name, size=size, sha256=digest)


def _manifest_payload(manifest: TransferManifest) -> dict[str, Any]:
    return {
        "schema": MANIFEST_SCHEMA,
        "package": manifest.package,
        "version": manifest.version,
        "source_sha": manifest.source_sha,
        "source_epoch": manifest.source_epoch,
        "artifacts": [
            {"name": row.name, "size": row.size, "sha256": row.sha256} for row in manifest.artifacts
        ],
    }


def _validate_manifest_value(payload: Any) -> TransferManifest:
    if not isinstance(payload, dict) or set(payload) != {
        "schema",
        "package",
        "version",
        "source_sha",
        "source_epoch",
        "artifacts",
    }:
        raise ReleaseError("Transfer manifest has an unexpected shape")
    if payload["schema"] != MANIFEST_SCHEMA:
        raise ReleaseError("Transfer manifest schema is unsupported")
    package = canonicalize_name(str(payload["package"]))
    version = str(Version(str(payload["version"])))
    source_sha = str(payload["source_sha"])
    if FULL_SHA_RE.fullmatch(source_sha) is None:
        raise ReleaseError("Transfer manifest source SHA must be a full commit SHA")
    source_epoch = payload["source_epoch"]
    if (
        isinstance(source_epoch, bool)
        or not isinstance(source_epoch, int)
        or not 315532800 <= source_epoch <= 4294967295
    ):
        raise ReleaseError("Transfer manifest source epoch is outside archive bounds")
    rows = payload["artifacts"]
    if not isinstance(rows, list) or len(rows) != 2:
        raise ReleaseError("Transfer manifest must bind exactly two artifacts")
    artifacts: list[ArtifactRecord] = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"name", "size", "sha256"}:
            raise ReleaseError("Transfer manifest artifact entry is malformed")
        name = str(row["name"])
        size = row["size"]
        sha256 = str(row["sha256"])
        if (
            SAFE_NAME_RE.fullmatch(name) is None
            or isinstance(size, bool)
            or not isinstance(size, int)
            or not 0 < size <= MAX_ARTIFACT_BYTES
            or SHA256_RE.fullmatch(sha256) is None
        ):
            raise ReleaseError("Transfer manifest artifact identity is invalid")
        artifacts.append(ArtifactRecord(name=name, size=size, sha256=sha256))
    expected_names = set(_artifact_names(package, version))
    actual_names = {artifact.name for artifact in artifacts}
    if len(actual_names) != 2 or actual_names != expected_names:
        raise ReleaseError("Transfer manifest does not contain the exact wheel and sdist names")
    return TransferManifest(
        package=package,
        version=version,
        source_sha=source_sha,
        artifacts=tuple(sorted(artifacts, key=lambda row: row.name)),
        source_epoch=source_epoch,
    )


def prepare_transfer(
    *,
    dist_dir: Path,
    transfer_dir: Path,
    package: str,
    version: str,
    source_sha: str,
    source_epoch: int,
) -> TransferManifest:
    """Copy an exact build result into a new manifest-bound transfer directory."""
    normalized_package = canonicalize_name(package)
    normalized_version = str(Version(version))
    if FULL_SHA_RE.fullmatch(source_sha) is None:
        raise ReleaseError("Source SHA must be a full commit SHA")
    if not 315532800 <= source_epoch <= 4294967295:
        raise ReleaseError("Source epoch is outside archive bounds")
    wheel, sdist = validate_local_artifacts(
        dist_dir,
        package=normalized_package,
        version=normalized_version,
    )
    paths = (wheel, sdist)
    if {path.name for path in paths} != set(_artifact_names(package, version)):
        raise ReleaseError("Build output filenames do not match the immutable release contract")
    if transfer_dir.exists() or transfer_dir.is_symlink():
        raise ReleaseError("Transfer directory must not already exist")
    try:
        transfer_dir.mkdir(parents=True, mode=0o700)
        records: list[ArtifactRecord] = []
        for source in paths:
            source_record = _safe_file_record(source)
            destination = transfer_dir / source.name
            shutil.copyfile(source, destination, follow_symlinks=False)
            destination_record = _safe_file_record(destination)
            if destination_record != source_record:
                raise ReleaseError("Transferred artifact differs from validated build output")
            records.append(destination_record)
        manifest = TransferManifest(
            package=normalized_package,
            version=normalized_version,
            source_sha=source_sha,
            artifacts=tuple(sorted(records, key=lambda row: row.name)),
            source_epoch=source_epoch,
        )
        manifest_bytes = (
            json.dumps(_manifest_payload(manifest), sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        if len(manifest_bytes) > MAX_MANIFEST_BYTES:
            raise ReleaseError("Transfer manifest exceeds the allowed size")
        manifest_path = transfer_dir / MANIFEST_NAME
        with manifest_path.open("xb") as stream:
            stream.write(manifest_bytes)
        return validate_transfer(
            transfer_dir=transfer_dir,
            expected_package=normalized_package,
            expected_version=normalized_version,
            expected_source_sha=source_sha,
            expected_source_epoch=source_epoch,
        )
    except Exception:
        shutil.rmtree(transfer_dir, ignore_errors=True)
        raise


def validate_transfer(
    *,
    transfer_dir: Path,
    expected_package: str,
    expected_version: str,
    expected_source_sha: str,
    expected_source_epoch: int | None = None,
) -> TransferManifest:
    """Validate a downloaded transfer without importing or extracting candidate code."""
    if transfer_dir.is_symlink() or not transfer_dir.is_dir():
        raise ReleaseError("Transfer directory is missing or unsafe")
    entries = sorted(transfer_dir.iterdir(), key=lambda path: path.name)
    expected_entries = {MANIFEST_NAME, *_artifact_names(expected_package, expected_version)}
    if {path.name for path in entries} != expected_entries:
        raise ReleaseError("Transfer directory does not contain the exact bounded file set")
    if any(path.is_symlink() or not path.is_file() for path in entries):
        raise ReleaseError("Transfer directory contains an unsafe entry")
    manifest_path = transfer_dir / MANIFEST_NAME
    try:
        if manifest_path.stat().st_size > MAX_MANIFEST_BYTES:
            raise ReleaseError("Transfer manifest exceeds the allowed size")
        payload = _load_json_bytes(manifest_path.read_bytes(), description="Transfer manifest")
    except OSError as exc:
        raise ReleaseError("Transfer manifest is unreadable") from exc
    manifest = _validate_manifest_value(payload)
    expected_identity = (
        canonicalize_name(expected_package),
        str(Version(expected_version)),
        expected_source_sha,
    )
    if (manifest.package, manifest.version, manifest.source_sha) != expected_identity:
        raise ReleaseError("Transfer manifest project, version, or source identity mismatch")
    if expected_source_epoch is not None and manifest.source_epoch != expected_source_epoch:
        raise ReleaseError("Transfer manifest source epoch mismatch")
    for expected in manifest.artifacts:
        actual = _safe_file_record(transfer_dir / expected.name)
        if actual != expected:
            raise ReleaseError("Transferred artifact does not match its manifest")
    return manifest


def _temporary_archive_path(path: Path) -> Path:
    try:
        descriptor, value = tempfile.mkstemp(
            prefix=f".{path.name}.canonical-",
            suffix=".tmp",
            dir=path.parent,
        )
        os.close(descriptor)
    except OSError as exc:
        raise ReleaseError("Canonical archive temporary file could not be created") from exc
    return Path(value)


def _zip_timestamp(source_epoch: int) -> tuple[int, int, int, int, int, int]:
    timestamp = time.gmtime(source_epoch)
    return (
        timestamp.tm_year,
        timestamp.tm_mon,
        timestamp.tm_mday,
        timestamp.tm_hour,
        timestamp.tm_min,
        timestamp.tm_sec,
    )


def _canonicalize_wheel(path: Path, *, source_epoch: int) -> None:
    temporary = _temporary_archive_path(path)
    try:
        with zipfile.ZipFile(path, "r") as source:
            infos = source.infolist()
            if not 0 < len(infos) <= MAX_ARCHIVE_MEMBERS:
                raise ReleaseError("Wheel member count is outside the allowed bound")
            names = [_safe_archive_path(info.filename) for info in infos]
            if len(names) != len(set(names)) or any(info.is_dir() for info in infos):
                raise ReleaseError("Wheel contains duplicate or directory members")
            if sum(info.file_size for info in infos) > MAX_UNPACKED_BYTES:
                raise ReleaseError("Wheel unpacked content exceeds the allowed size")
            by_name = dict(zip(names, infos, strict=True))
            with zipfile.ZipFile(
                temporary,
                "w",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=9,
                allowZip64=True,
            ) as target:
                for name in sorted(by_name):
                    payload = _read_zip_member(source, by_name[name])
                    canonical = zipfile.ZipInfo(name, date_time=_zip_timestamp(source_epoch))
                    canonical.compress_type = zipfile.ZIP_DEFLATED
                    canonical.create_system = 3
                    canonical.external_attr = (stat.S_IFREG | 0o644) << 16
                    canonical.flag_bits = 0
                    target.writestr(canonical, payload, compress_type=zipfile.ZIP_DEFLATED)
        if temporary.lstat().st_size > MAX_ARTIFACT_BYTES:
            raise ReleaseError("Canonical wheel exceeds the allowed size")
        os.replace(temporary, path)
    except (OSError, RuntimeError, zipfile.BadZipFile) as exc:
        if isinstance(exc, ReleaseError):
            raise
        raise ReleaseError("Wheel canonicalization failed") from exc
    finally:
        temporary.unlink(missing_ok=True)


def _canonicalize_sdist(path: Path, *, source_epoch: int) -> None:
    temporary = _temporary_archive_path(path)
    try:
        with tarfile.open(path, mode="r:gz") as source:
            members = source.getmembers()
            if not 0 < len(members) <= MAX_ARCHIVE_MEMBERS:
                raise ReleaseError("Source-distribution member count is outside the allowed bound")
            names = [_safe_archive_path(member.name) for member in members]
            if len(names) != len(set(names)):
                raise ReleaseError("Source distribution contains duplicate members")
            total = 0
            for member in members:
                if not (member.isdir() or member.isfile()):
                    raise ReleaseError("Source distribution contains a link or special member")
                total += member.size
                if member.size < 0 or total > MAX_UNPACKED_BYTES:
                    raise ReleaseError("Source-distribution content exceeds the allowed size")
            by_name = dict(zip(names, members, strict=True))
            with temporary.open("wb") as raw_target:
                with gzip.GzipFile(
                    filename="",
                    mode="wb",
                    compresslevel=9,
                    fileobj=raw_target,
                    mtime=source_epoch,
                ) as compressed:
                    with tarfile.open(
                        fileobj=compressed,
                        mode="w",
                        format=tarfile.PAX_FORMAT,
                    ) as target:
                        for name in sorted(by_name):
                            member = by_name[name]
                            canonical = tarfile.TarInfo(name)
                            canonical.uid = 0
                            canonical.gid = 0
                            canonical.uname = ""
                            canonical.gname = ""
                            canonical.mtime = source_epoch
                            canonical.mode = 0o755 if member.isdir() else 0o644
                            if member.isdir():
                                canonical.type = tarfile.DIRTYPE
                                target.addfile(canonical)
                                continue
                            canonical.size = member.size
                            stream = source.extractfile(member)
                            if stream is None:
                                raise ReleaseError("Source-distribution member is unreadable")
                            with stream:
                                target.addfile(canonical, stream)
        if temporary.lstat().st_size > MAX_ARTIFACT_BYTES:
            raise ReleaseError("Canonical source distribution exceeds the allowed size")
        os.replace(temporary, path)
    except (OSError, tarfile.TarError) as exc:
        if isinstance(exc, ReleaseError):
            raise
        raise ReleaseError("Source-distribution canonicalization failed") from exc
    finally:
        temporary.unlink(missing_ok=True)


def normalize_build(
    *,
    dist_dir: Path,
    package: str,
    version: str,
    source_epoch: int,
) -> tuple[ArtifactRecord, ArtifactRecord]:
    """Normalize one exact wheel/sdist pair to deterministic archive bytes."""
    if not 315532800 <= source_epoch <= 4294967295:
        raise ReleaseError("Source epoch is outside archive bounds")
    wheel, sdist = validate_local_artifacts(dist_dir, package=package, version=version)
    _canonicalize_wheel(wheel, source_epoch=source_epoch)
    _canonicalize_sdist(sdist, source_epoch=source_epoch)
    validated_wheel, validated_sdist = validate_local_artifacts(
        dist_dir,
        package=package,
        version=version,
    )
    return _safe_file_record(validated_wheel), _safe_file_record(validated_sdist)


def _files_are_equal(first: Path, second: Path) -> bool:
    first_record = _safe_file_record(first)
    second_record = _safe_file_record(second)
    if first_record != second_record:
        return False
    with first.open("rb") as first_stream, second.open("rb") as second_stream:
        while True:
            first_chunk = first_stream.read(1024 * 1024)
            second_chunk = second_stream.read(1024 * 1024)
            if first_chunk != second_chunk:
                return False
            if not first_chunk:
                return True


def compare_builds(*, first_dir: Path, second_dir: Path, package: str, version: str) -> None:
    """Require two independently built exact artifact pairs to be byte-identical."""
    first = validate_local_artifacts(first_dir, package=package, version=version)
    second = validate_local_artifacts(second_dir, package=package, version=version)
    for first_path, second_path in zip(first, second, strict=True):
        if first_path.name != second_path.name or not _files_are_equal(first_path, second_path):
            raise ReleaseError("Independent release builds are not byte-identical")


def _safe_archive_path(value: str) -> str:
    if not value or "\\" in value or "\x00" in value:
        raise ReleaseError("Release archive contains an unsafe path")
    parts = value.rstrip("/").split("/")
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ReleaseError("Release archive contains an unsafe path")
    return "/".join(parts)


def _git_bytes(source_root: Path, source_sha: str, *args: str) -> bytes:
    env = {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": "",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "PATH": os.environ.get("PATH", os.defpath),
    }
    try:
        return subprocess.run(
            ["git", "-c", "core.autocrlf=false", *args],
            cwd=source_root,
            env=env,
            capture_output=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseError(f"Trusted Git object {source_sha} could not be read") from exc


def _git_blob(source_root: Path, source_sha: str, relative: str) -> bytes:
    _safe_archive_path(relative)
    identity = (
        _git_bytes(
            source_root,
            source_sha,
            "rev-parse",
            "--verify",
            f"{source_sha}:{relative}",
        )
        .decode()
        .strip()
    )
    payload = _git_bytes(source_root, source_sha, "cat-file", "blob", identity)
    actual = hashlib.sha1(  # noqa: S324 - Git's SHA-1 object format is the identity contract.
        f"blob {len(payload)}\0".encode() + payload
    ).hexdigest()
    if actual != identity:
        raise ReleaseError("Trusted Git blob failed independent object re-hashing")
    return payload


def _git_tree_files(source_root: Path, source_sha: str, directory: str) -> list[str]:
    listing = _git_bytes(
        source_root,
        source_sha,
        "ls-tree",
        "-r",
        "-z",
        source_sha,
        "--",
        directory,
    )
    result: list[str] = []
    for row in listing.rstrip(b"\0").split(b"\0"):
        if not row:
            continue
        try:
            metadata, encoded = row.split(b"\t", 1)
            mode, object_type, _object_id = metadata.split(b" ", 2)
            relative = encoded.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as exc:
            raise ReleaseError("Trusted source tree entry is malformed") from exc
        if object_type != b"blob" or mode not in {b"100644", b"100755"}:
            raise ReleaseError("Trusted source package tree contains a link or gitlink")
        _safe_archive_path(relative)
        result.append(relative)
    return result


def _source_distribution_files(
    source_root: Path,
    source_sha: str,
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Derive exact package payload bytes from the trusted Git object database."""
    try:
        project = tomllib.loads(_git_blob(source_root, source_sha, "pyproject.toml").decode())
        setuptools = project["tool"]["setuptools"]
        includes = setuptools["packages"]["find"]["include"]
        package_data = setuptools["package-data"]
    except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
        raise ReleaseError("Trusted source packaging configuration is invalid") from exc
    if not isinstance(includes, list) or not isinstance(package_data, dict):
        raise ReleaseError("Trusted source package selection is invalid")

    result: dict[str, bytes] = {}
    package_roots: set[str] = set()
    for include in includes:
        if not isinstance(include, str) or not include.endswith("*"):
            raise ReleaseError("Trusted source package selection is unsupported")
        package_root = include[:-1]
        if not package_root.isidentifier():
            raise ReleaseError("Trusted source package selection is unsafe")
        package_roots.add(package_root)
        for relative in _git_tree_files(source_root, source_sha, package_root):
            if relative.endswith(".py"):
                result[relative] = _git_blob(source_root, source_sha, relative)

    for package, patterns in package_data.items():
        if package not in package_roots or not isinstance(patterns, list):
            raise ReleaseError("Trusted source package-data selection is unsupported")
        for pattern in patterns:
            if not isinstance(pattern, str) or pattern.startswith(("/", "..")):
                raise ReleaseError("Trusted source package-data pattern is unsafe")
            for relative in _git_tree_files(source_root, source_sha, package):
                package_relative = relative.removeprefix(f"{package}/")
                if Path(package_relative).match(pattern):
                    result[relative] = _git_blob(source_root, source_sha, relative)

    if not result:
        raise ReleaseError("Trusted source package payload is empty")
    return result, project


def _expected_requirements(project: Mapping[str, Any]) -> tuple[set[Requirement], set[str]]:
    requirements = {Requirement(value) for value in project["project"]["dependencies"]}
    extras = set(project["project"]["optional-dependencies"])
    for extra, values in project["project"]["optional-dependencies"].items():
        normalized_extra = canonicalize_name(extra)
        for value in values:
            requirements.add(Requirement(f"{value}; extra == '{normalized_extra}'"))
    return requirements, {canonicalize_name(value) for value in extras}


def _normalized_metadata_values(field: str, values: list[str]) -> list[str]:
    try:
        if field == "Requires-Dist":
            return sorted(str(Requirement(value)) for value in values)
        if field == "Provides-Extra":
            return sorted(canonicalize_name(value) for value in values)
        if field == "Requires-Python":
            return [str(SpecifierSet(value)) for value in values]
    except Exception as exc:
        raise ReleaseError("Distribution metadata is malformed") from exc
    return values


def _expected_core_metadata(
    project: Mapping[str, Any], manifest: TransferManifest
) -> dict[str, list[str]]:
    expected_requirements, expected_extras = _expected_requirements(project)
    expected_license_files = project["project"].get("license-files", [])
    if not isinstance(expected_license_files, list) or not all(
        isinstance(value, str) for value in expected_license_files
    ):
        raise ReleaseError("Trusted project license-file metadata is malformed")
    expected: dict[str, list[str]] = {
        "Metadata-Version": ["2.4"],
        "Name": [str(project["project"]["name"])],
        "Version": [manifest.version],
        "Summary": [str(project["project"]["description"])],
        "Author-email": _expected_people(project, "authors"),
        "Maintainer-email": _expected_people(project, "maintainers"),
        "License-Expression": [str(project["project"]["license"])],
        "Project-URL": [
            f"{name}, {url}" for name, url in project["project"].get("urls", {}).items()
        ],
        "Keywords": [",".join(project["project"].get("keywords", []))],
        "Classifier": list(project["project"].get("classifiers", [])),
        "Requires-Python": [str(SpecifierSet(project["project"]["requires-python"]))],
        "Description-Content-Type": ["text/markdown"],
        "License-File": expected_license_files,
        "Requires-Dist": sorted(str(requirement) for requirement in expected_requirements),
        "Provides-Extra": sorted(expected_extras),
        "Dynamic": ["license-file"],
    }
    return {field: values for field, values in expected.items() if values}


def _expected_people(project: Mapping[str, Any], field: str) -> list[str]:
    people = project["project"].get(field, [])
    if not isinstance(people, list):
        raise ReleaseError("Trusted project people metadata is malformed")
    rendered: list[str] = []
    for person in people:
        if not isinstance(person, dict) or set(person) != {"name", "email"}:
            raise ReleaseError("Trusted project people metadata is unsupported")
        name = person["name"]
        email = person["email"]
        if not isinstance(name, str) or not isinstance(email, str) or not name or not email:
            raise ReleaseError("Trusted project people metadata is invalid")
        rendered.append(f"{name} <{email}>")
    return [", ".join(rendered)] if rendered else []


def _metadata_body(payload: bytes) -> bytes:
    separators = [
        position for value in (b"\n\n", b"\r\n\r\n") if (position := payload.find(value)) >= 0
    ]
    if not separators:
        raise ReleaseError("Distribution metadata has no description separator")
    position = min(separators)
    separator_length = 4 if payload[position : position + 4] == b"\r\n\r\n" else 2
    return payload[position + separator_length :]


def _validate_core_metadata(
    payload: bytes,
    manifest: TransferManifest,
    project: Mapping[str, Any],
    readme: bytes,
) -> None:
    if len(payload) > MAX_JSON_BYTES:
        raise ReleaseError("Distribution metadata exceeds the allowed size")
    try:
        metadata = BytesParser().parsebytes(payload, headersonly=True)
        actual: dict[str, list[str]] = {}
        for field, value in metadata.raw_items():
            actual.setdefault(field, []).append(value)
        actual = {
            field: _normalized_metadata_values(field, values) for field, values in actual.items()
        }
    except Exception as exc:
        if isinstance(exc, ReleaseError):
            raise
        raise ReleaseError("Distribution metadata is malformed") from exc
    expected = _expected_core_metadata(project, manifest)
    expected_scripts = project["project"]["scripts"]
    if (
        actual != expected
        or canonicalize_name(actual.get("Name", [""])[0]) != manifest.package
        or project["project"].get("readme") != "README.md"
        or _metadata_body(payload) != readme
        or set(expected_scripts) != {"nbx", "nbx-mock", "nbx-mcp"}
    ):
        raise ReleaseError("Distribution metadata does not match trusted release configuration")


def _read_zip_member(archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> bytes:
    if info.file_size < 0 or info.file_size > MAX_ARTIFACT_BYTES:
        raise ReleaseError("Wheel member exceeds the allowed size")
    if info.flag_bits & 0x1:
        raise ReleaseError("Encrypted wheel members are not allowed")
    with archive.open(info, "r") as stream:
        payload = stream.read(info.file_size + 1)
    if len(payload) != info.file_size:
        raise ReleaseError("Wheel member size is inconsistent")
    return payload


def _validate_wheel_record(
    *,
    record_bytes: bytes,
    member_bytes: Mapping[str, bytes],
    record_name: str,
) -> None:
    try:
        rows = list(csv.reader(record_bytes.decode("utf-8").splitlines()))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ReleaseError("Wheel RECORD is malformed") from exc
    records: dict[str, tuple[str, str]] = {}
    for row in rows:
        if len(row) != 3 or row[0] in records:
            raise ReleaseError("Wheel RECORD is malformed")
        records[row[0]] = (row[1], row[2])
    if set(records) != set(member_bytes):
        raise ReleaseError("Wheel RECORD does not bind the exact member set")
    for name, payload in member_bytes.items():
        digest, size = records[name]
        if name == record_name:
            if digest or size:
                raise ReleaseError("Wheel RECORD self-entry must be unhashed")
            continue
        encoded = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode()
        if digest != f"sha256={encoded}" or size != str(len(payload)):
            raise ReleaseError("Wheel RECORD member digest or size mismatch")


def _validate_wheel_source(
    *,
    wheel_path: Path,
    manifest: TransferManifest,
    source_files: Mapping[str, bytes],
    source_blobs: Mapping[str, bytes],
    project: Mapping[str, Any],
) -> None:
    dist_info = f"{manifest.package.replace('-', '_')}-{manifest.version}.dist-info"
    generated = {
        f"{dist_info}/METADATA",
        f"{dist_info}/WHEEL",
        f"{dist_info}/entry_points.txt",
        f"{dist_info}/licenses/LICENSE.txt",
        f"{dist_info}/RECORD",
        f"{dist_info}/top_level.txt",
    }
    try:
        with zipfile.ZipFile(wheel_path, "r") as archive:
            infos = archive.infolist()
            if not 0 < len(infos) <= MAX_ARCHIVE_MEMBERS:
                raise ReleaseError("Wheel member count is outside the allowed bound")
            names = [_safe_archive_path(info.filename) for info in infos]
            if len(names) != len(set(names)) or any(info.is_dir() for info in infos):
                raise ReleaseError("Wheel contains duplicate or unexpected directory members")
            expected_names = set(source_files) | generated
            if set(names) != expected_names:
                raise ReleaseError("Wheel payload is not the exact trusted-source file set")
            if sum(info.file_size for info in infos) > MAX_UNPACKED_BYTES:
                raise ReleaseError("Wheel unpacked content exceeds the allowed size")
            member_bytes = {
                name: _read_zip_member(archive, info)
                for name, info in zip(names, infos, strict=True)
            }
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        if isinstance(exc, ReleaseError):
            raise
        raise ReleaseError("Wheel is not a valid bounded archive") from exc

    for relative, source in source_files.items():
        if member_bytes[relative] != source:
            raise ReleaseError("Wheel package payload differs from trusted canonical source")
    if member_bytes[f"{dist_info}/licenses/LICENSE.txt"] != source_blobs["LICENSE.txt"]:
        raise ReleaseError("Wheel license differs from trusted canonical source")
    _validate_core_metadata(
        member_bytes[f"{dist_info}/METADATA"],
        manifest,
        project,
        source_blobs["README.md"],
    )
    wheel_headers = BytesParser().parsebytes(member_bytes[f"{dist_info}/WHEEL"], headersonly=True)
    if wheel_headers.get("Root-Is-Purelib") != "true" or wheel_headers.get_all("Tag") != [
        "py3-none-any"
    ]:
        raise ReleaseError("Wheel compatibility metadata is not the required universal tag")
    expected_entries = "[console_scripts]\n" + "".join(
        f"{name} = {target}\n" for name, target in sorted(project["project"]["scripts"].items())
    )
    if member_bytes[f"{dist_info}/entry_points.txt"].decode("utf-8") != expected_entries:
        raise ReleaseError("Wheel entry points differ from trusted canonical source")
    expected_top_level = "".join(
        f"{name.removesuffix('*')}\n"
        for name in sorted(project["tool"]["setuptools"]["packages"]["find"]["include"])
    )
    if member_bytes[f"{dist_info}/top_level.txt"].decode() != expected_top_level:
        raise ReleaseError("Wheel top-level packages differ from trusted configuration")
    _validate_wheel_record(
        record_bytes=member_bytes[f"{dist_info}/RECORD"],
        member_bytes=member_bytes,
        record_name=f"{dist_info}/RECORD",
    )


def _read_tar_member(archive: tarfile.TarFile, member: tarfile.TarInfo) -> bytes:
    if member.size < 0 or member.size > MAX_ARTIFACT_BYTES:
        raise ReleaseError("Source-distribution member exceeds the allowed size")
    stream = archive.extractfile(member)
    if stream is None:
        raise ReleaseError("Source-distribution member is unreadable")
    with stream:
        payload = stream.read(member.size + 1)
    if len(payload) != member.size:
        raise ReleaseError("Source-distribution member size is inconsistent")
    return payload


def _validate_sdist_source(
    *,
    sdist_path: Path,
    manifest: TransferManifest,
    source_files: Mapping[str, bytes],
    test_files: Mapping[str, bytes],
    source_blobs: Mapping[str, bytes],
    project: Mapping[str, Any],
) -> None:
    prefix = f"{manifest.package.replace('-', '_')}-{manifest.version}"
    egg_info = f"{manifest.package.replace('-', '_')}.egg-info"
    generated = {
        "PKG-INFO",
        "setup.cfg",
        f"{egg_info}/PKG-INFO",
        f"{egg_info}/SOURCES.txt",
        f"{egg_info}/dependency_links.txt",
        f"{egg_info}/entry_points.txt",
        f"{egg_info}/requires.txt",
        f"{egg_info}/top_level.txt",
    }
    trusted_root_files = dict(source_blobs)
    expected_files = set(source_files) | set(test_files) | set(trusted_root_files) | generated
    payloads: dict[str, bytes] = {}
    try:
        with tarfile.open(sdist_path, mode="r:gz") as archive:
            members = archive.getmembers()
            if not 0 < len(members) <= MAX_ARCHIVE_MEMBERS:
                raise ReleaseError("Source-distribution member count is outside the allowed bound")
            total = 0
            seen: set[str] = set()
            for member in members:
                name = _safe_archive_path(member.name)
                if name == prefix and member.isdir():
                    continue
                if not name.startswith(f"{prefix}/"):
                    raise ReleaseError("Source distribution has an unexpected archive root")
                relative = name[len(prefix) + 1 :]
                if relative in seen:
                    raise ReleaseError("Source distribution contains duplicate members")
                seen.add(relative)
                if member.isdir():
                    continue
                if not member.isfile():
                    raise ReleaseError("Source distribution contains a link or special member")
                total += member.size
                if total > MAX_UNPACKED_BYTES:
                    raise ReleaseError("Source-distribution content exceeds the allowed size")
                payloads[relative] = _read_tar_member(archive, member)
    except (OSError, tarfile.TarError) as exc:
        if isinstance(exc, ReleaseError):
            raise
        raise ReleaseError("Source distribution is not a valid bounded archive") from exc

    if set(payloads) != expected_files:
        raise ReleaseError("Source distribution is not the exact trusted-source file set")
    for relative, source in {**source_files, **test_files, **trusted_root_files}.items():
        if payloads[relative] != source:
            raise ReleaseError("Source-distribution payload differs from trusted canonical source")
    _validate_core_metadata(payloads["PKG-INFO"], manifest, project, source_blobs["README.md"])
    _validate_core_metadata(
        payloads[f"{egg_info}/PKG-INFO"],
        manifest,
        project,
        source_blobs["README.md"],
    )
    expected_entries = "[console_scripts]\n" + "".join(
        f"{name} = {target}\n" for name, target in sorted(project["project"]["scripts"].items())
    )
    if payloads[f"{egg_info}/entry_points.txt"].decode() != expected_entries:
        raise ReleaseError("Source-distribution entry points differ from trusted configuration")
    expected_top_level = "".join(
        f"{name.removesuffix('*')}\n"
        for name in sorted(project["tool"]["setuptools"]["packages"]["find"]["include"])
    )
    if payloads[f"{egg_info}/top_level.txt"].decode() != expected_top_level:
        raise ReleaseError(
            "Source-distribution top-level packages differ from trusted configuration"
        )
    if payloads[f"{egg_info}/dependency_links.txt"] not in {b"", b"\n"}:
        raise ReleaseError("Source distribution contains unexpected dependency links")
    parsed_requirements: set[Requirement] = set()
    extra: str | None = None
    try:
        for line in payloads[f"{egg_info}/requires.txt"].decode().splitlines():
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                extra = canonicalize_name(line[1:-1])
                continue
            parsed_requirements.add(
                Requirement(line if extra is None else f"{line}; extra == '{extra}'")
            )
    except Exception as exc:
        raise ReleaseError("Source-distribution requirements file is malformed") from exc
    expected_requirements, _ = _expected_requirements(project)
    if parsed_requirements != expected_requirements:
        raise ReleaseError("Source-distribution requirements differ from trusted configuration")
    source_rows = set(payloads[f"{egg_info}/SOURCES.txt"].decode().splitlines())
    if source_rows != expected_files - {"PKG-INFO", "setup.cfg"}:
        raise ReleaseError("Source-distribution SOURCES manifest is not exact")
    if payloads["setup.cfg"] != b"[egg_info]\ntag_build = \ntag_date = 0\n\n":
        raise ReleaseError("Source-distribution setup configuration is unexpected")


def validate_archive_source_binding(
    *,
    transfer_dir: Path,
    manifest: TransferManifest,
    source_root: Path,
) -> None:
    """Bind both archives to canonical source without importing or extracting them."""
    if (
        validated_commit_epoch(commit_ref=manifest.source_sha, repo=source_root)
        != manifest.source_epoch
    ):
        raise ReleaseError("Transfer source epoch differs from the trusted source commit")
    source_files, project = _source_distribution_files(source_root, manifest.source_sha)
    project_identity = (
        canonicalize_name(str(project["project"]["name"])),
        str(Version(str(project["project"]["version"]))),
    )
    if project_identity != (manifest.package, manifest.version):
        raise ReleaseError("Trusted source project identity does not match the transfer")
    test_files = {
        relative: _git_blob(source_root, manifest.source_sha, relative)
        for relative in _git_tree_files(source_root, manifest.source_sha, "tests")
        if relative.startswith("tests/test_") and relative.endswith(".py")
    }
    source_blobs = {
        name: _git_blob(source_root, manifest.source_sha, name)
        for name in ("LICENSE.txt", "README.md", "pyproject.toml")
    }
    wheel_name, sdist_name = _artifact_names(manifest.package, manifest.version)
    _validate_wheel_source(
        wheel_path=transfer_dir / wheel_name,
        manifest=manifest,
        source_files=source_files,
        source_blobs=source_blobs,
        project=project,
    )
    _validate_sdist_source(
        sdist_path=transfer_dir / sdist_name,
        manifest=manifest,
        source_files=source_files,
        test_files=test_files,
        source_blobs=source_blobs,
        project=project,
    )


def validate_trusted_source_checkout(*, source_root: Path, source_sha: str) -> None:
    """Require a closed, clean, fully verified checkout at the exact source commit."""
    try:
        head = (
            _git_bytes(source_root, source_sha, "rev-parse", "--verify", "HEAD^{commit}")
            .decode()
            .strip()
        )
        status = _git_bytes(
            source_root,
            source_sha,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        )
        object_format = (
            _git_bytes(
                source_root,
                source_sha,
                "rev-parse",
                "--show-object-format",
            )
            .decode()
            .strip()
        )
        replacements = _git_bytes(source_root, source_sha, "replace", "--list")
        local_config = _git_bytes(source_root, source_sha, "config", "--local", "--null", "--list")
        _git_bytes(source_root, source_sha, "fsck", "--strict")
        commit = _git_bytes(source_root, source_sha, "cat-file", "commit", source_sha)
    except ReleaseError as exc:
        raise ReleaseError("Trusted source checkout could not be validated") from exc
    actual_commit = hashlib.sha1(  # noqa: S324 - Git's SHA-1 object format is the identity contract.
        f"commit {len(commit)}\0".encode() + commit
    ).hexdigest()
    git_dir = source_root / ".git"
    forbidden_git_state = (
        (git_dir / "objects/info/alternates").exists()
        or (git_dir / "shallow").exists()
        or (git_dir / "info/grafts").exists()
    )
    forbidden_config_prefixes = (
        b"credential.",
        b"extensions.partialclone",
        b"filter.",
        b"http.",
        b"include.",
        b"remote.origin.promisor",
        b"url.",
    )
    config_keys = [entry.split(b"\n", 1)[0].lower() for entry in local_config.split(b"\0") if entry]
    if (
        head != source_sha
        or status
        or object_format != "sha1"
        or replacements
        or actual_commit != source_sha
        or forbidden_git_state
        or any(key.startswith(forbidden_config_prefixes) for key in config_keys)
    ):
        raise ReleaseError("Trusted source checkout is not clean at the exact source commit")


def _seal_payload(manifest: TransferManifest) -> dict[str, Any]:
    payload = _manifest_payload(manifest)
    payload["schema"] = SEAL_SCHEMA
    return payload


def seal_transfer(
    *,
    transfer_dir: Path,
    sealed_dir: Path,
    source_root: Path,
    expected_package: str,
    expected_version: str,
    expected_source_sha: str,
    expected_source_epoch: int,
) -> TransferManifest:
    """Perform complex credential-free validation and create a private exact seal."""
    manifest = validate_transfer(
        transfer_dir=transfer_dir,
        expected_package=expected_package,
        expected_version=expected_version,
        expected_source_sha=expected_source_sha,
        expected_source_epoch=expected_source_epoch,
    )
    validate_trusted_source_checkout(source_root=source_root, source_sha=expected_source_sha)
    validate_archive_source_binding(
        transfer_dir=transfer_dir,
        manifest=manifest,
        source_root=source_root,
    )
    if sealed_dir.exists() or sealed_dir.is_symlink():
        raise ReleaseError("Sealed directory must not already exist")
    canonical_dir: Path | None = None
    try:
        canonical_dir = Path(tempfile.mkdtemp(prefix=".release-canonical-", dir=sealed_dir.parent))
        canonical_dir.chmod(0o700)
        for expected in manifest.artifacts:
            shutil.copyfile(
                transfer_dir / expected.name,
                canonical_dir / expected.name,
                follow_symlinks=False,
            )
        normalize_build(
            dist_dir=canonical_dir,
            package=manifest.package,
            version=manifest.version,
            source_epoch=manifest.source_epoch,
        )
        for expected in manifest.artifacts:
            incoming = transfer_dir / expected.name
            canonical = canonical_dir / expected.name
            if _safe_file_record(canonical) != expected or not _files_are_equal(
                incoming, canonical
            ):
                raise ReleaseError("Release archive bytes are not exact canonical output")

        sealed_dir.mkdir(parents=True, mode=0o700)
        for expected in manifest.artifacts:
            destination = sealed_dir / expected.name
            shutil.copyfile(canonical_dir / expected.name, destination, follow_symlinks=False)
            if _safe_file_record(destination) != expected:
                raise ReleaseError("Sealed artifact differs from the validated transfer")
            destination.chmod(0o400)
        seal_bytes = (
            json.dumps(_seal_payload(manifest), sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        if len(seal_bytes) > MAX_SEAL_BYTES:
            raise ReleaseError("Release seal exceeds the allowed size")
        seal_path = sealed_dir / SEAL_NAME
        with seal_path.open("xb") as stream:
            stream.write(seal_bytes)
        seal_path.chmod(0o400)
        sealed_dir.chmod(0o500)
        return validate_seal(
            sealed_dir=sealed_dir,
            expected_package=expected_package,
            expected_version=expected_version,
            expected_source_sha=expected_source_sha,
            expected_source_epoch=expected_source_epoch,
        )
    except Exception:
        if sealed_dir.exists():
            sealed_dir.chmod(0o700)
        shutil.rmtree(sealed_dir, ignore_errors=True)
        raise
    finally:
        if canonical_dir is not None:
            shutil.rmtree(canonical_dir, ignore_errors=True)


def harden_downloaded_seal(
    *,
    sealed_dir: Path,
    expected_package: str,
    expected_version: str,
    expected_source_sha: str,
    expected_source_epoch: int,
) -> TransferManifest:
    """Restore private modes lost by artifact transport, then validate the seal."""
    try:
        directory_stat = sealed_dir.lstat()
        entries = sorted(sealed_dir.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        raise ReleaseError("Downloaded sealed directory is unavailable") from exc
    expected_entries = {SEAL_NAME, *_artifact_names(expected_package, expected_version)}
    if (
        sealed_dir.is_symlink()
        or not stat.S_ISDIR(directory_stat.st_mode)
        or directory_stat.st_uid != os.geteuid()
        or {path.name for path in entries} != expected_entries
    ):
        raise ReleaseError("Downloaded sealed directory has an unsafe shape")
    for path in entries:
        file_stat = path.lstat()
        if (
            path.is_symlink()
            or not stat.S_ISREG(file_stat.st_mode)
            or file_stat.st_uid != os.geteuid()
            or stat.S_IMODE(file_stat.st_mode) & 0o022
        ):
            raise ReleaseError("Downloaded sealed file is unsafe")
        path.chmod(0o400)
    sealed_dir.chmod(0o500)
    return validate_seal(
        sealed_dir=sealed_dir,
        expected_package=expected_package,
        expected_version=expected_version,
        expected_source_sha=expected_source_sha,
        expected_source_epoch=expected_source_epoch,
    )


def validate_seal(
    *,
    sealed_dir: Path,
    expected_package: str,
    expected_version: str,
    expected_source_sha: str,
    expected_source_epoch: int,
) -> TransferManifest:
    """Validate only a bounded private seal and re-hash its exact regular files."""
    try:
        directory_stat = sealed_dir.lstat()
    except OSError as exc:
        raise ReleaseError("Sealed directory is unavailable") from exc
    if (
        sealed_dir.is_symlink()
        or not stat.S_ISDIR(directory_stat.st_mode)
        or directory_stat.st_uid != os.geteuid()
        or stat.S_IMODE(directory_stat.st_mode) != 0o500
    ):
        raise ReleaseError("Sealed directory is not private")
    entries = sorted(sealed_dir.iterdir(), key=lambda path: path.name)
    expected_entries = {SEAL_NAME, *_artifact_names(expected_package, expected_version)}
    if {path.name for path in entries} != expected_entries:
        raise ReleaseError("Sealed directory does not contain the exact file set")
    for path in entries:
        file_stat = path.lstat()
        if (
            path.is_symlink()
            or not stat.S_ISREG(file_stat.st_mode)
            or file_stat.st_uid != os.geteuid()
            or stat.S_IMODE(file_stat.st_mode) != 0o400
        ):
            raise ReleaseError("Sealed directory contains a non-private file")
    seal_path = sealed_dir / SEAL_NAME
    try:
        if seal_path.stat().st_size > MAX_SEAL_BYTES:
            raise ReleaseError("Release seal exceeds the allowed size")
        payload = _load_json_bytes(seal_path.read_bytes(), description="Release seal")
    except OSError as exc:
        raise ReleaseError("Release seal is unreadable") from exc
    if not isinstance(payload, dict) or payload.get("schema") != SEAL_SCHEMA:
        raise ReleaseError("Release seal schema is unsupported")
    manifest_payload = dict(payload)
    manifest_payload["schema"] = MANIFEST_SCHEMA
    manifest = _validate_manifest_value(manifest_payload)
    expected_identity = (
        canonicalize_name(expected_package),
        str(Version(expected_version)),
        expected_source_sha,
        expected_source_epoch,
    )
    if (
        manifest.package,
        manifest.version,
        manifest.source_sha,
        manifest.source_epoch,
    ) != expected_identity:
        raise ReleaseError("Release seal identity mismatch")
    for expected in manifest.artifacts:
        if _safe_file_record(sealed_dir / expected.name) != expected:
            raise ReleaseError("Sealed artifact does not match its seal")
    return manifest


class _HttpConnection(Protocol):
    sock: Any

    def request(
        self, method: str, url: str, body: bytes | None, headers: Mapping[str, str]
    ) -> None: ...

    def getresponse(self) -> Any: ...

    def close(self) -> None: ...


class BoundedHttpClient:
    """Small no-redirect HTTP client with body, request, and wall-clock bounds."""

    def __init__(
        self,
        *,
        server_url: str,
        token: str,
        deadline_seconds: float = 180.0,
        request_timeout: float = 15.0,
        connection_factory: Callable[[str, float], _HttpConnection] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        parsed = urllib.parse.urlsplit(server_url)
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ReleaseError("Registry server URL must be a credential-free HTTPS origin")
        if not token:
            raise ReleaseError("The ephemeral package token is unavailable")
        if not 0 < deadline_seconds <= 600 or not 0 < request_timeout <= 60:
            raise ReleaseError("Registry timeout bounds are invalid")
        self._origin = f"{parsed.scheme}://{parsed.netloc}"
        self._host = parsed.netloc
        self._token = token
        self._clock = clock
        self._deadline = clock() + deadline_seconds
        self._request_timeout = request_timeout
        self._connection_factory = connection_factory or (
            lambda host, timeout: http.client.HTTPSConnection(host, timeout=timeout)
        )

    @property
    def origin(self) -> str:
        """Return the validated credential-free registry origin."""
        return self._origin

    def remaining(self) -> float:
        """Return remaining wall-clock time or fail the bounded operation."""
        remaining = self._deadline - self._clock()
        if remaining <= 0:
            raise ReleaseError("Registry operation exceeded its deadline")
        return remaining

    def _read_bounded(
        self,
        response: Any,
        *,
        connection: _HttpConnection,
        maximum: int,
    ) -> bytes:
        length_value = response.getheader("Content-Length")
        if length_value is not None:
            try:
                content_length = int(length_value)
            except ValueError as exc:
                raise ReleaseError("Registry returned an invalid Content-Length") from exc
            if content_length < 0 or content_length > maximum:
                raise ReleaseError("Registry response exceeds the allowed size")
            if content_length == 0:
                self.remaining()
                return b""
        result = bytearray()
        while True:
            remaining = self.remaining()
            if connection.sock is None:
                raise ReleaseError("Registry connection did not expose a bounded socket")
            connection.sock.settimeout(min(self._request_timeout, remaining))
            chunk = response.read(min(64 * 1024, maximum + 1 - len(result)))
            if not chunk:
                break
            result.extend(chunk)
            if len(result) > maximum:
                raise ReleaseError("Registry response exceeds the allowed size")
        self.remaining()
        return bytes(result)

    def request_bytes(
        self,
        *,
        method: str,
        path: str,
        maximum: int,
        allow_not_found: bool = False,
    ) -> bytes | None:
        """Perform one authenticated no-redirect request and return bounded bytes."""
        if not path.startswith("/") or "\r" in path or "\n" in path:
            raise ReleaseError("Registry request path is invalid")
        connection = self._connection_factory(
            self._host,
            min(self._request_timeout, self.remaining()),
        )
        try:
            connection.request(
                method,
                path,
                b"" if method == "POST" else None,
                {
                    "Authorization": f"token {self._token}",
                    "Accept": "application/json",
                    "User-Agent": "netbox-sdk-private-release/1",
                },
            )
            response = connection.getresponse()
            status = int(response.status)
            if status == 404 and allow_not_found:
                return None
            if 300 <= status < 400:
                raise ReleaseError("Registry redirect was refused") from None
            if not 200 <= status < 300:
                raise ReleaseError(f"Registry request failed with HTTP {status}")
            return self._read_bounded(response, connection=connection, maximum=maximum)
        except (TimeoutError, http.client.HTTPException, OSError):
            raise ReleaseError("Registry request failed or timed out") from None
        finally:
            connection.close()

    def request_json(self, *, path: str, allow_not_found: bool = False) -> Any | None:
        """Return a bounded JSON response."""
        payload = self.request_bytes(
            method="GET",
            path=path,
            maximum=MAX_JSON_BYTES,
            allow_not_found=allow_not_found,
        )
        if payload is None:
            return None
        return _load_json_bytes(payload, description="Registry response")

    def post_empty(self, *, path: str) -> None:
        """Perform a bounded POST whose response body is ignored but capped."""
        self.request_bytes(method="POST", path=path, maximum=MAX_JSON_BYTES)


def _quote(value: str) -> str:
    if not value or SAFE_NAME_RE.fullmatch(value) is None:
        raise ReleaseError("Registry identity contains unsupported characters")
    return urllib.parse.quote(value, safe="")


def _repository_identity(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        raise ReleaseError("Registry package metadata is malformed")
    repository = payload.get("repository")
    if repository is None:
        return None
    if not isinstance(repository, dict):
        raise ReleaseError("Registry repository association is malformed")
    full_name = repository.get("full_name")
    if not isinstance(full_name, str) or "/" not in full_name:
        raise ReleaseError("Registry repository association is incomplete")
    return full_name


class GiteaRegistry:
    """Exact-state view of the Gitea PyPI and package-management APIs."""

    def __init__(
        self,
        *,
        client: BoundedHttpClient,
        owner: str,
        repository: str,
    ) -> None:
        self.client = client
        self.owner = _quote(owner)
        self.repository = _quote(repository)

    @property
    def expected_repository(self) -> str:
        """Return the exact owner/repository association required by policy."""
        return f"{urllib.parse.unquote(self.owner)}/{urllib.parse.unquote(self.repository)}"

    def _package_path(self, manifest: TransferManifest) -> str:
        return (
            f"/api/v1/packages/{self.owner}/pypi/"
            f"{_quote(manifest.package)}/{_quote(manifest.version)}"
        )

    def inspect(self, manifest: TransferManifest) -> RemoteState:
        """Inspect metadata, association, API hashes, and exact downloaded bytes."""
        package_path = self._package_path(manifest)
        package_payload = self.client.request_json(path=package_path, allow_not_found=True)
        version_exists = package_payload is not None
        if version_exists:
            if not isinstance(package_payload, dict):
                raise ReleaseError("Registry package metadata is malformed")
            identity = (
                str(package_payload.get("type", "")),
                canonicalize_name(str(package_payload.get("name", ""))),
                str(package_payload.get("version", "")),
            )
            if identity != ("pypi", manifest.package, manifest.version):
                raise ReleaseError("Registry package metadata identity mismatch")
            repository = _repository_identity(package_payload)
        else:
            latest_path = f"/api/v1/packages/{self.owner}/pypi/{_quote(manifest.package)}/-/latest"
            latest_payload = self.client.request_json(path=latest_path, allow_not_found=True)
            repository = (
                _repository_identity(latest_payload) if latest_payload is not None else None
            )

        files_payload = self.client.request_json(
            path=f"{package_path}/files",
            allow_not_found=True,
        )
        if files_payload is None:
            if version_exists:
                raise ReleaseError("Registry package version exists without a file inventory")
            return RemoteState(False, repository, ())
        if not version_exists or not isinstance(files_payload, list):
            raise ReleaseError("Registry file inventory is inconsistent")

        expected = manifest.artifact_map()
        records: list[ArtifactRecord] = []
        seen: set[str] = set()
        for row in files_payload:
            if not isinstance(row, dict):
                raise ReleaseError("Registry file inventory entry is malformed")
            name = row.get("name")
            size = row.get("size")
            digest = row.get("sha256")
            if (
                not isinstance(name, str)
                or SAFE_NAME_RE.fullmatch(name) is None
                or name in seen
                or isinstance(size, bool)
                or not isinstance(size, int)
                or size < 0
                or size > MAX_ARTIFACT_BYTES
                or not isinstance(digest, str)
                or SHA256_RE.fullmatch(digest.lower()) is None
            ):
                raise ReleaseError("Registry file inventory identity is invalid")
            seen.add(name)
            api_record = ArtifactRecord(name=name, size=size, sha256=digest.lower())
            expected_record = expected.get(name)
            if expected_record is not None and api_record == expected_record:
                download_path = (
                    f"/api/packages/{self.owner}/pypi/files/"
                    f"{_quote(manifest.package)}/{_quote(manifest.version)}/{_quote(name)}"
                )
                content = self.client.request_bytes(
                    method="GET",
                    path=download_path,
                    maximum=expected_record.size,
                )
                if content is None:
                    raise ReleaseError("Registry artifact download unexpectedly disappeared")
                downloaded = ArtifactRecord(
                    name=name,
                    size=len(content),
                    sha256=hashlib.sha256(content).hexdigest(),
                )
                if downloaded != expected_record:
                    raise ReleaseError("Registry artifact bytes do not match their API provenance")
            records.append(api_record)
        return RemoteState(
            version_exists=True,
            repository=repository,
            artifacts=tuple(sorted(records, key=lambda row: row.name)),
        )

    def link(self, manifest: TransferManifest) -> None:
        """Associate the package name with its exact repository."""
        path = (
            f"/api/v1/packages/{self.owner}/pypi/{_quote(manifest.package)}"
            f"/-/link/{self.repository}"
        )
        self.client.post_empty(path=path)


def classify_remote_state(state: RemoteState, manifest: TransferManifest) -> str:
    """Classify only the two allowed registry states: absent or exact."""
    local = manifest.artifact_map()
    remote = state.artifact_map()
    if not state.version_exists and not remote:
        return "absent"
    extra = sorted(set(remote) - set(local))
    missing = sorted(set(local) - set(remote))
    if extra:
        raise ReleaseError("Registry version contains unexpected extra artifacts")
    if missing:
        raise ReleaseError("Registry version is only partially published")
    if any(remote[name] != local[name] for name in local):
        raise ReleaseError("Registry artifact size or digest mismatch")
    if not state.version_exists:
        raise ReleaseError("Registry version state is inconsistent")
    return "exact"


def _require_allowed_association(state: RemoteState, expected_repository: str) -> None:
    if state.repository is not None and state.repository != expected_repository:
        raise ReleaseError("Package is associated with a different repository")


def reconcile_publication(
    *,
    manifest: TransferManifest,
    registry: GiteaRegistry,
    upload: Callable[[], None],
    revalidate_seal: Callable[[], None],
) -> str:
    """Publish from absent state or accept an independently verified exact state."""
    revalidate_seal()
    state = registry.inspect(manifest)
    _require_allowed_association(state, registry.expected_repository)
    classification = classify_remote_state(state, manifest)
    if classification == "absent":
        try:
            upload()
        except Exception:
            revalidate_seal()
            recovered = registry.inspect(manifest)
            _require_allowed_association(recovered, registry.expected_repository)
            if classify_remote_state(recovered, manifest) != "exact":
                raise ReleaseError(
                    "Registry upload did not reach an exact recoverable state"
                ) from None
            state = recovered
        else:
            revalidate_seal()
            state = registry.inspect(manifest)
            _require_allowed_association(state, registry.expected_repository)
            if classify_remote_state(state, manifest) != "exact":
                raise ReleaseError("Registry upload did not produce the exact artifact set")

    if state.repository is None:
        try:
            registry.link(manifest)
        except Exception:
            recovered = registry.inspect(manifest)
            _require_allowed_association(recovered, registry.expected_repository)
            if recovered.repository != registry.expected_repository:
                raise ReleaseError("Repository association did not reach an exact state") from None

    revalidate_seal()
    final_state = registry.inspect(manifest)
    _require_allowed_association(final_state, registry.expected_repository)
    if final_state.repository != registry.expected_repository:
        raise ReleaseError("Package repository association is missing")
    if classify_remote_state(final_state, manifest) != "exact":
        raise ReleaseError("Final registry state is not exact")
    return "already exact" if classification == "exact" else "published exact"


def _run_twine_upload(
    *,
    python: Path,
    server_url: str,
    owner: str,
    username: str,
    token: str,
    artifact_paths: Sequence[Path],
    timeout: float,
) -> None:
    if not username or not token:
        raise ReleaseError("Publisher identity or ephemeral token is unavailable")
    repository_url = f"{server_url}/api/packages/{urllib.parse.quote(owner, safe='')}/pypi"
    env = {
        "PYTHONNOUSERSITE": "1",
        "PYTHONUTF8": "1",
        "TWINE_NON_INTERACTIVE": "1",
        "TWINE_PASSWORD": token,
        "TWINE_USERNAME": username,
    }
    command = [
        str(python),
        "-m",
        "twine",
        "upload",
        "--non-interactive",
        "--repository-url",
        repository_url,
        *(str(path) for path in artifact_paths),
    ]
    try:
        result = subprocess.run(
            command,
            check=False,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise ReleaseError("Registry upload failed or timed out") from None
    if result.returncode != 0:
        raise ReleaseError("Registry upload failed")


def _write_actions_outputs(values: Mapping[str, str]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with Path(output_path).open("a", encoding="utf-8") as stream:
        for key, value in values.items():
            if "\n" in value or "\r" in value:
                raise ReleaseError("Workflow output contains a line break")
            stream.write(f"{key}={value}\n")


def validate_release_policy(
    *,
    event_name: str,
    tag: str,
    tag_ref: str,
    canonical_main_ref: str,
    immutable_tag_ref: str,
    immutable_tag_object: str,
    immutable_tag_commit: str,
    repo: Path = ROOT,
) -> tuple[str, str, str, int]:
    """Validate exact tag/version/source and the immutable release lineage."""
    context = release_context(expected_package="netbox-sdk", pyproject=repo / "pyproject.toml")
    validate_gitea_candidate_tag(event_name=event_name, ref_name=tag, version=context.version)
    source_sha = validate_exact_canonical_source(
        candidate_ref=tag_ref,
        canonical_main_ref=canonical_main_ref,
        repo=repo,
    )
    validate_immutable_tag(
        tag_ref=immutable_tag_ref,
        expected_tag_object=immutable_tag_object,
        expected_commit=immutable_tag_commit,
        repo=repo,
    )
    source_epoch = validated_commit_epoch(commit_ref=source_sha, repo=repo)
    return context.package_name, context.version, source_sha, source_epoch


def _add_policy_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--tag-ref", required=True)
    parser.add_argument("--canonical-main-ref", required=True)
    parser.add_argument("--immutable-tag-ref", required=True)
    parser.add_argument("--immutable-tag-object", required=True)
    parser.add_argument("--immutable-tag-commit", required=True)


def _main_policy(args: argparse.Namespace) -> int:
    package, version, source_sha, source_epoch = validate_release_policy(
        event_name=args.event_name,
        tag=args.tag,
        tag_ref=args.tag_ref,
        canonical_main_ref=args.canonical_main_ref,
        immutable_tag_ref=args.immutable_tag_ref,
        immutable_tag_object=args.immutable_tag_object,
        immutable_tag_commit=args.immutable_tag_commit,
    )
    _write_actions_outputs(
        {
            "package_name": package,
            "version": version,
            "source_sha": source_sha,
            "source_epoch": str(source_epoch),
        }
    )
    print(
        f"private release policy passed: version={version}, "
        f"source={source_sha}, epoch={source_epoch}"
    )
    return 0


def _main_validate_tag(args: argparse.Namespace) -> int:
    context = release_context(expected_package="netbox-sdk")
    validate_gitea_candidate_tag(
        event_name=args.event_name,
        ref_name=args.tag,
        version=context.version,
    )
    _write_actions_outputs({"tag": args.tag})
    print("release tag input passed")
    return 0


def _main_validate_tag_protection(args: argparse.Namespace) -> int:
    validate_release_tag_protection(
        policy_file=args.policy_file,
        evidence_file=args.evidence_file,
    )
    print("server-side release-tag protection evidence matches repository policy")
    return 0


def _main_prepare(args: argparse.Namespace) -> int:
    manifest = prepare_transfer(
        dist_dir=args.dist_dir,
        transfer_dir=args.transfer_dir,
        package=args.package,
        version=args.version,
        source_sha=args.source_sha,
        source_epoch=args.source_epoch,
    )
    print(
        "release transfer passed: "
        + ", ".join(f"{row.name}:{row.size}:{row.sha256}" for row in manifest.artifacts)
    )
    return 0


def _main_normalize(args: argparse.Namespace) -> int:
    records = normalize_build(
        dist_dir=args.dist_dir,
        package=args.package,
        version=args.version,
        source_epoch=args.source_epoch,
    )
    print("canonical build passed: " + ", ".join(row.sha256 for row in records))
    return 0


def _main_compare(args: argparse.Namespace) -> int:
    compare_builds(
        first_dir=args.first_dir,
        second_dir=args.second_dir,
        package=args.package,
        version=args.version,
    )
    print("independent release builds are byte-identical")
    return 0


def _main_seal(args: argparse.Namespace) -> int:
    manifest = seal_transfer(
        transfer_dir=args.transfer_dir,
        sealed_dir=args.sealed_dir,
        source_root=args.source_root,
        expected_package=args.package,
        expected_version=args.version,
        expected_source_sha=args.source_sha,
        expected_source_epoch=args.source_epoch,
    )
    print(
        "credential-free source seal passed: "
        + ", ".join(f"{row.name}:{row.sha256}" for row in manifest.artifacts)
    )
    return 0


def _main_harden_seal(args: argparse.Namespace) -> int:
    harden_downloaded_seal(
        sealed_dir=args.sealed_dir,
        expected_package=args.package,
        expected_version=args.version,
        expected_source_sha=args.source_sha,
        expected_source_epoch=args.source_epoch,
    )
    print("downloaded release seal is private and exact")
    return 0


def _main_publish(args: argparse.Namespace) -> int:
    token = os.environ.get(args.token_env, "")

    def revalidate() -> None:
        validate_seal(
            sealed_dir=args.sealed_dir,
            expected_package=args.package,
            expected_version=args.version,
            expected_source_sha=args.source_sha,
            expected_source_epoch=args.source_epoch,
        )

    manifest = validate_seal(
        sealed_dir=args.sealed_dir,
        expected_package=args.package,
        expected_version=args.version,
        expected_source_sha=args.source_sha,
        expected_source_epoch=args.source_epoch,
    )
    client = BoundedHttpClient(
        server_url=args.server_url,
        token=token,
        deadline_seconds=args.deadline_seconds,
        request_timeout=args.request_timeout,
    )
    registry = GiteaRegistry(
        client=client,
        owner=args.owner,
        repository=args.repository,
    )
    artifact_paths = tuple(args.sealed_dir / row.name for row in manifest.artifacts)
    result = reconcile_publication(
        manifest=manifest,
        registry=registry,
        upload=lambda: _run_twine_upload(
            python=args.python,
            server_url=client.origin,
            owner=args.owner,
            username=args.username,
            token=token,
            artifact_paths=artifact_paths,
            timeout=client.remaining(),
        ),
        revalidate_seal=revalidate,
    )
    print(f"private registry publication passed: {result}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    validate_tag = commands.add_parser("validate-tag")
    validate_tag.add_argument("--event-name", required=True)
    validate_tag.add_argument("--tag", required=True)
    validate_tag.set_defaults(handler=_main_validate_tag)

    validate_tag_protection = commands.add_parser("validate-tag-protection")
    validate_tag_protection.add_argument("--policy-file", type=Path, required=True)
    validate_tag_protection.add_argument("--evidence-file", type=Path, required=True)
    validate_tag_protection.set_defaults(handler=_main_validate_tag_protection)

    policy = commands.add_parser("policy")
    _add_policy_arguments(policy)
    policy.set_defaults(handler=_main_policy)

    prepare = commands.add_parser("prepare-transfer")
    prepare.add_argument("--dist-dir", type=Path, required=True)
    prepare.add_argument("--transfer-dir", type=Path, required=True)
    prepare.add_argument("--package", required=True)
    prepare.add_argument("--version", required=True)
    prepare.add_argument("--source-sha", required=True)
    prepare.add_argument("--source-epoch", type=int, required=True)
    prepare.set_defaults(handler=_main_prepare)

    normalize = commands.add_parser("normalize-build")
    normalize.add_argument("--dist-dir", type=Path, required=True)
    normalize.add_argument("--package", required=True)
    normalize.add_argument("--version", required=True)
    normalize.add_argument("--source-epoch", type=int, required=True)
    normalize.set_defaults(handler=_main_normalize)

    compare = commands.add_parser("compare-builds")
    compare.add_argument("--first-dir", type=Path, required=True)
    compare.add_argument("--second-dir", type=Path, required=True)
    compare.add_argument("--package", required=True)
    compare.add_argument("--version", required=True)
    compare.set_defaults(handler=_main_compare)

    seal = commands.add_parser("seal-transfer")
    seal.add_argument("--transfer-dir", type=Path, required=True)
    seal.add_argument("--sealed-dir", type=Path, required=True)
    seal.add_argument("--source-root", type=Path, required=True)
    seal.add_argument("--package", required=True)
    seal.add_argument("--version", required=True)
    seal.add_argument("--source-sha", required=True)
    seal.add_argument("--source-epoch", type=int, required=True)
    seal.set_defaults(handler=_main_seal)

    harden_seal = commands.add_parser("harden-seal")
    harden_seal.add_argument("--sealed-dir", type=Path, required=True)
    harden_seal.add_argument("--package", required=True)
    harden_seal.add_argument("--version", required=True)
    harden_seal.add_argument("--source-sha", required=True)
    harden_seal.add_argument("--source-epoch", type=int, required=True)
    harden_seal.set_defaults(handler=_main_harden_seal)

    publish = commands.add_parser("publish")
    publish.add_argument("--sealed-dir", type=Path, required=True)
    publish.add_argument("--package", required=True)
    publish.add_argument("--version", required=True)
    publish.add_argument("--source-sha", required=True)
    publish.add_argument("--source-epoch", type=int, required=True)
    publish.add_argument("--server-url", required=True)
    publish.add_argument("--owner", required=True)
    publish.add_argument("--repository", required=True)
    publish.add_argument("--username", required=True)
    publish.add_argument("--token-env", default="GITEA_TOKEN")
    publish.add_argument("--python", type=Path, required=True)
    publish.add_argument("--deadline-seconds", type=float, default=180.0)
    publish.add_argument("--request-timeout", type=float, default=15.0)
    publish.set_defaults(handler=_main_publish)

    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (ReleaseError, RuntimeError, ValueError) as exc:
        print(f"private release gate failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
