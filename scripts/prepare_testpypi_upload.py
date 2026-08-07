"""Compare local distributions with a Python package registry before upload.

The local directory must contain exactly one wheel and one source distribution
for the requested package and version. Existing filenames are accepted only
when their published SHA-256 digest matches the local artifact. Approved files
are copied into a fresh upload directory so Twine never consumes an unchecked
``dist/*`` glob or needs ``--skip-existing``. TestPyPI's published wheel URL is
exposed for an exact post-upload installation smoke test. PyPI uses the same
closed-set/hash checks so a partial production upload can resume safely.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from packaging.utils import (
    InvalidSdistFilename,
    InvalidWheelFilename,
    canonicalize_name,
    parse_sdist_filename,
    parse_wheel_filename,
)
from packaging.version import InvalidVersion, Version

TESTPYPI_JSON_BASE = "https://test.pypi.org/pypi"
TESTPYPI_FILE_HOST = "test-files.pythonhosted.org"
PYPI_JSON_BASE = "https://pypi.org/pypi"
PYPI_FILE_HOST = "files.pythonhosted.org"
REGISTRIES = {
    "testpypi": ("TestPyPI", TESTPYPI_JSON_BASE, TESTPYPI_FILE_HOST),
    "pypi": ("PyPI", PYPI_JSON_BASE, PYPI_FILE_HOST),
}


@dataclass(frozen=True)
class PublishedArtifact:
    sha256: str
    url: str


def artifact_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def upload_manifest_path(upload_dir: Path) -> Path:
    """Return the manifest path adjacent to, but outside, the upload directory."""
    return Path(f"{upload_dir}.manifest.json")


def _validated_artifact_url(
    value: object,
    *,
    registry_name: str = "TestPyPI",
    file_host: str = TESTPYPI_FILE_HOST,
) -> str:
    url = str(value)
    parsed = urllib.parse.urlsplit(url)
    if "\r" in url or "\n" in url:
        raise RuntimeError(f"{registry_name} returned an artifact URL containing a line break")
    if parsed.scheme != "https" or parsed.netloc != file_host or parsed.query or parsed.fragment:
        raise RuntimeError(f"{registry_name} returned an unexpected artifact URL: {url!r}")
    return url


def _hash_bound_artifact_url(
    artifact: PublishedArtifact,
    *,
    registry_name: str,
    file_host: str,
) -> str:
    url = _validated_artifact_url(
        artifact.url,
        registry_name=registry_name,
        file_host=file_host,
    )
    return f"{url}#sha256={artifact.sha256}"


def published_artifacts(
    payload: dict[str, Any],
    *,
    registry_name: str = "TestPyPI",
    file_host: str = TESTPYPI_FILE_HOST,
) -> dict[str, PublishedArtifact]:
    artifacts: dict[str, PublishedArtifact] = {}
    urls = payload.get("urls")
    if not isinstance(urls, list):
        raise RuntimeError(f"{registry_name} release metadata does not contain an artifact list")
    for row in urls:
        if not isinstance(row, dict):
            raise RuntimeError(f"{registry_name} returned a malformed artifact entry")
        filename = str(row.get("filename", ""))
        digests = row.get("digests")
        sha256 = str(digests.get("sha256", "")) if isinstance(digests, dict) else ""
        if not filename or re.fullmatch(r"[0-9a-fA-F]{64}", sha256) is None:
            raise RuntimeError(f"{registry_name} returned incomplete artifact provenance")
        artifact = PublishedArtifact(
            sha256=sha256.lower(),
            url=_validated_artifact_url(
                row.get("url", ""),
                registry_name=registry_name,
                file_host=file_host,
            ),
        )
        previous = artifacts.setdefault(filename, artifact)
        if previous != artifact:
            raise RuntimeError(f"{registry_name} returned conflicting records for {filename}")
    return artifacts


def fetch_published_artifacts(
    package: str,
    version: str,
    *,
    registry: str = "testpypi",
) -> dict[str, PublishedArtifact]:
    registry_name, json_base, file_host = REGISTRIES[registry]
    package_path = urllib.parse.quote(package, safe="")
    version_path = urllib.parse.quote(version, safe="")
    request = urllib.request.Request(
        f"{json_base}/{package_path}/{version_path}/json",
        headers={"User-Agent": "netbox-sdk-release-verifier/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {}
        raise RuntimeError(f"{registry_name} metadata request failed with HTTP {exc.code}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{registry_name} metadata request failed") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{registry_name} returned malformed release metadata")
    return published_artifacts(
        payload,
        registry_name=registry_name,
        file_host=file_host,
    )


def validate_local_artifacts(
    dist_dir: Path,
    *,
    package: str,
    version: str,
) -> tuple[Path, Path]:
    """Return the exact wheel/sdist pair after validating its identity."""
    if not dist_dir.is_dir():
        raise RuntimeError(f"Distribution directory does not exist: {dist_dir}")
    try:
        expected_version = Version(version)
    except InvalidVersion as exc:
        raise RuntimeError(f"Invalid expected package version: {version!r}") from exc
    expected_package = canonicalize_name(package)

    entries = sorted(dist_dir.iterdir())
    invalid_entries = [
        path.name
        for path in entries
        if path.is_symlink()
        or not path.is_file()
        or not (path.name.endswith(".whl") or path.name.endswith(".tar.gz"))
    ]
    if invalid_entries:
        names = ", ".join(invalid_entries)
        raise RuntimeError(f"Distribution directory contains unexpected entries: {names}")

    wheels = [path for path in entries if path.name.endswith(".whl")]
    sdists = [path for path in entries if path.name.endswith(".tar.gz")]
    if len(wheels) != 1 or len(sdists) != 1 or len(entries) != 2:
        raise RuntimeError(
            "Distribution directory must contain exactly one wheel and one source distribution; "
            f"found wheels={len(wheels)}, sdists={len(sdists)}, total={len(entries)}"
        )

    wheel = wheels[0]
    sdist = sdists[0]
    try:
        wheel_package, wheel_version, _, _ = parse_wheel_filename(wheel.name)
    except InvalidWheelFilename as exc:
        raise RuntimeError(f"Invalid wheel filename: {wheel.name}") from exc
    try:
        sdist_package, sdist_version = parse_sdist_filename(sdist.name)
    except InvalidSdistFilename as exc:
        raise RuntimeError(f"Invalid source distribution filename: {sdist.name}") from exc

    identities = (
        ("wheel", canonicalize_name(str(wheel_package)), wheel_version),
        ("source distribution", canonicalize_name(str(sdist_package)), sdist_version),
    )
    for artifact_type, artifact_package, artifact_version in identities:
        if artifact_package != expected_package or artifact_version != expected_version:
            raise RuntimeError(
                f"Local {artifact_type} identity mismatch: "
                f"got {artifact_package}=={artifact_version}, "
                f"expected {expected_package}=={expected_version}"
            )
    return wheel, sdist


def prepare_upload(
    dist_dir: Path,
    upload_dir: Path,
    published: dict[str, PublishedArtifact],
    *,
    package: str,
    version: str,
    require_published: bool = False,
    registry_name: str = "TestPyPI",
    file_host: str = TESTPYPI_FILE_HOST,
) -> tuple[list[Path], str | None]:
    artifacts = sorted(validate_local_artifacts(dist_dir, package=package, version=version))
    local_names = {artifact.name for artifact in artifacts}
    unexpected = sorted(set(published) - local_names)
    if unexpected:
        names = ", ".join(unexpected)
        raise RuntimeError(f"{registry_name} exposed unexpected artifact(s): {names}")
    missing: list[Path] = []
    wheel_url: str | None = None
    for artifact in artifacts:
        local_sha256 = artifact_sha256(artifact)
        remote = published.get(artifact.name)
        if remote is None:
            missing.append(artifact)
            continue
        _validated_artifact_url(
            remote.url,
            registry_name=registry_name,
            file_host=file_host,
        )
        if remote.sha256 != local_sha256:
            raise RuntimeError(
                f"Published {registry_name} artifact hash mismatch for {artifact.name}: "
                f"local={local_sha256}, published={remote.sha256}"
            )
        if artifact.name.endswith(".whl"):
            wheel_url = _hash_bound_artifact_url(
                remote,
                registry_name=registry_name,
                file_host=file_host,
            )

    if require_published and missing:
        names = ", ".join(path.name for path in missing)
        raise RuntimeError(f"{registry_name} is missing uploaded artifact(s): {names}")
    if require_published and wheel_url is None:
        raise RuntimeError(f"{registry_name} did not expose the uploaded wheel")
    if upload_dir.exists():
        raise RuntimeError(f"Upload directory must not already exist: {upload_dir}")
    manifest_path = upload_manifest_path(upload_dir)
    if manifest_path.exists():
        raise RuntimeError(f"Upload manifest must not already exist: {manifest_path}")
    upload_dir.mkdir(parents=True)
    manifest_artifacts: dict[str, str] = {}
    for artifact in missing:
        expected_sha256 = artifact_sha256(artifact)
        destination = upload_dir / artifact.name
        shutil.copy2(artifact, destination)
        copied_sha256 = artifact_sha256(destination)
        if copied_sha256 != expected_sha256:
            raise RuntimeError(f"Copied upload artifact hash mismatch for {artifact.name}")
        manifest_artifacts[artifact.name] = expected_sha256
    manifest = {
        "package": canonicalize_name(package),
        "version": str(Version(version)),
        "artifacts": manifest_artifacts,
    }
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    return missing, wheel_url


def validate_approved_upload(
    dist_dir: Path,
    upload_dir: Path,
    *,
    package: str,
    version: str,
) -> list[Path]:
    """Revalidate a manifest-bound staging directory immediately before upload."""
    artifacts = sorted(validate_local_artifacts(dist_dir, package=package, version=version))
    sources = {artifact.name: artifact for artifact in artifacts}
    manifest_path = upload_manifest_path(upload_dir)
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise RuntimeError(f"Approved upload manifest is missing or unsafe: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("Approved upload manifest is unreadable") from exc
    if not isinstance(manifest, dict):
        raise RuntimeError("Approved upload manifest is malformed")
    expected_identity = (canonicalize_name(package), str(Version(version)))
    if (manifest.get("package"), manifest.get("version")) != expected_identity:
        raise RuntimeError("Approved upload manifest package/version mismatch")
    manifest_artifacts = manifest.get("artifacts")
    if not isinstance(manifest_artifacts, dict) or any(
        not isinstance(name, str)
        or not isinstance(digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        for name, digest in manifest_artifacts.items()
    ):
        raise RuntimeError("Approved upload manifest artifact set is malformed")
    if upload_dir.is_symlink() or not upload_dir.is_dir():
        raise RuntimeError(f"Approved upload directory is missing or unsafe: {upload_dir}")
    entries = sorted(upload_dir.iterdir())
    entry_names = {entry.name for entry in entries}
    if entry_names != set(manifest_artifacts):
        raise RuntimeError("Approved upload directory does not match its manifest")
    for entry in entries:
        if entry.is_symlink() or not entry.is_file() or entry.name not in sources:
            raise RuntimeError(f"Approved upload artifact is unsafe: {entry.name}")
        expected_sha256 = manifest_artifacts[entry.name]
        if artifact_sha256(sources[entry.name]) != expected_sha256:
            raise RuntimeError(f"Source artifact changed after approval: {entry.name}")
        if artifact_sha256(entry) != expected_sha256:
            raise RuntimeError(f"Approved upload artifact hash mismatch: {entry.name}")
    return entries


def _write_actions_outputs(*, upload_required: bool, wheel_url: str | None) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with Path(output_path).open("a", encoding="utf-8") as stream:
        stream.write(f"upload_required={'true' if upload_required else 'false'}\n")
        stream.write(f"wheel_url={wheel_url or ''}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--dist-dir", type=Path, required=True)
    parser.add_argument("--upload-dir", type=Path)
    parser.add_argument("--require-published", action="store_true")
    parser.add_argument("--registry", choices=sorted(REGISTRIES), default="testpypi")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--verify-upload-dir", action="store_true")
    args = parser.parse_args()

    if args.validate_only:
        if (
            args.upload_dir is not None
            or args.require_published
            or args.registry != "testpypi"
            or args.verify_upload_dir
        ):
            parser.error("--validate-only cannot be combined with upload options")
        wheel, sdist = validate_local_artifacts(
            args.dist_dir,
            package=args.package,
            version=args.version,
        )
        print(f"local artifacts passed: wheel={wheel.name}, sdist={sdist.name}")
        return 0
    if args.upload_dir is None:
        parser.error("--upload-dir is required unless --validate-only is used")
    if args.verify_upload_dir:
        if args.require_published or args.registry != "testpypi":
            parser.error("--verify-upload-dir cannot be combined with registry options")
        approved = validate_approved_upload(
            args.dist_dir,
            args.upload_dir,
            package=args.package,
            version=args.version,
        )
        print("approved upload passed: " + ", ".join(path.name for path in approved))
        return 0

    registry_name, _, file_host = REGISTRIES[args.registry]
    published = fetch_published_artifacts(
        args.package,
        args.version,
        registry=args.registry,
    )
    missing, wheel_url = prepare_upload(
        args.dist_dir,
        args.upload_dir,
        published,
        package=args.package,
        version=args.version,
        require_published=args.require_published,
        registry_name=registry_name,
        file_host=file_host,
    )
    _write_actions_outputs(upload_required=bool(missing), wheel_url=wheel_url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
