from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.prepare_testpypi_upload import (
    PYPI_FILE_HOST,
    PublishedArtifact,
    prepare_upload,
    published_artifacts,
    validate_approved_upload,
    validate_local_artifacts,
)

pytestmark = pytest.mark.suite_sdk
PACKAGE = "netbox-sdk"
VERSION = "0.0.11rc1"


def _published(
    path: Path,
    *,
    sha256: str | None = None,
    file_host: str = "test-files.pythonhosted.org",
) -> PublishedArtifact:
    digest = sha256 or hashlib.sha256(path.read_bytes()).hexdigest()
    return PublishedArtifact(
        sha256=digest,
        url=f"https://{file_host}/packages/{path.name}",
    )


def _dist(tmp_path: Path) -> tuple[Path, Path, Path]:
    dist = tmp_path / "dist"
    dist.mkdir()
    wheel = dist / "netbox_sdk-0.0.11rc1-py3-none-any.whl"
    sdist = dist / "netbox_sdk-0.0.11rc1.tar.gz"
    wheel.write_bytes(b"wheel")
    sdist.write_bytes(b"sdist")
    return dist, wheel, sdist


def test_prepare_upload_skips_identical_file_and_copies_only_missing(tmp_path: Path) -> None:
    dist, wheel, sdist = _dist(tmp_path)

    missing, wheel_url = prepare_upload(
        dist,
        tmp_path / "upload",
        {wheel.name: _published(wheel)},
        package=PACKAGE,
        version=VERSION,
    )

    assert missing == [sdist]
    wheel_digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    assert wheel_url == (
        f"https://test-files.pythonhosted.org/packages/{wheel.name}#sha256={wheel_digest}"
    )
    assert sorted(path.name for path in (tmp_path / "upload").iterdir()) == [sdist.name]


def test_prepare_upload_rejects_existing_filename_with_different_hash(tmp_path: Path) -> None:
    dist, wheel, _ = _dist(tmp_path)
    wheel.write_bytes(b"local-wheel")

    with pytest.raises(RuntimeError, match="artifact hash mismatch"):
        prepare_upload(
            dist,
            tmp_path / "upload",
            {wheel.name: _published(wheel, sha256="0" * 64)},
            package=PACKAGE,
            version=VERSION,
        )


def test_prepare_upload_rejects_unexpected_remote_artifact(tmp_path: Path) -> None:
    dist, wheel, _ = _dist(tmp_path)
    unexpected = tmp_path / "netbox_sdk-0.0.11rc1-cp313-cp313-manylinux.whl"
    unexpected.write_bytes(b"unexpected-wheel")

    with pytest.raises(RuntimeError, match="unexpected artifact"):
        prepare_upload(
            dist,
            tmp_path / "upload",
            {
                wheel.name: _published(wheel),
                unexpected.name: _published(unexpected),
            },
            package=PACKAGE,
            version=VERSION,
        )


def test_prepare_upload_requires_registry_wheel_after_publish(tmp_path: Path) -> None:
    dist, _, _ = _dist(tmp_path)

    with pytest.raises(RuntimeError, match="missing uploaded artifact"):
        prepare_upload(
            dist,
            tmp_path / "upload",
            {},
            package=PACKAGE,
            version=VERSION,
            require_published=True,
        )


def test_local_artifacts_require_exact_wheel_and_sdist_identity(tmp_path: Path) -> None:
    dist, wheel, sdist = _dist(tmp_path)

    assert validate_local_artifacts(dist, package=PACKAGE, version=VERSION) == (wheel, sdist)


@pytest.mark.parametrize(
    "unexpected_name",
    [
        "checksums.txt",
        "netbox_sdk-0.0.11rc1-py3-none-any.whl.sig",
    ],
)
def test_local_artifacts_reject_unexpected_entries(
    tmp_path: Path,
    unexpected_name: str,
) -> None:
    dist, _, _ = _dist(tmp_path)
    (dist / unexpected_name).write_bytes(b"unexpected")

    with pytest.raises(RuntimeError, match="unexpected entries"):
        validate_local_artifacts(dist, package=PACKAGE, version=VERSION)


def test_local_artifacts_reject_multiple_wheels(tmp_path: Path) -> None:
    dist, _, _ = _dist(tmp_path)
    (dist / "netbox_sdk-0.0.11rc1-1-py3-none-any.whl").write_bytes(b"extra")

    with pytest.raises(RuntimeError, match="exactly one wheel and one source distribution"):
        validate_local_artifacts(dist, package=PACKAGE, version=VERSION)


@pytest.mark.parametrize(
    ("artifact", "replacement"),
    [
        ("wheel", "other_sdk-0.0.11rc1-py3-none-any.whl"),
        ("sdist", "netbox_sdk-0.0.12.tar.gz"),
    ],
)
def test_local_artifacts_reject_wrong_package_or_version(
    tmp_path: Path,
    artifact: str,
    replacement: str,
) -> None:
    dist, wheel, sdist = _dist(tmp_path)
    target = wheel if artifact == "wheel" else sdist
    target.rename(dist / replacement)

    with pytest.raises(RuntimeError, match="identity mismatch"):
        validate_local_artifacts(dist, package=PACKAGE, version=VERSION)


def test_published_validation_creates_no_upload_candidates(tmp_path: Path) -> None:
    dist, wheel, sdist = _dist(tmp_path)
    published = {wheel.name: _published(wheel), sdist.name: _published(sdist)}
    upload = tmp_path / "unexpected-missing"

    missing, wheel_url = prepare_upload(
        dist,
        upload,
        published,
        package=PACKAGE,
        version=VERSION,
        require_published=True,
    )

    assert missing == []
    assert wheel_url is not None and wheel_url.endswith(
        f"/{wheel.name}#sha256={hashlib.sha256(wheel.read_bytes()).hexdigest()}"
    )
    assert list(upload.iterdir()) == []


def test_partial_pypi_upload_stages_only_verified_missing_artifact(tmp_path: Path) -> None:
    dist, wheel, sdist = _dist(tmp_path)
    upload = tmp_path / "pypi-upload"

    missing, wheel_url = prepare_upload(
        dist,
        upload,
        {wheel.name: _published(wheel, file_host=PYPI_FILE_HOST)},
        package=PACKAGE,
        version=VERSION,
        registry_name="PyPI",
        file_host=PYPI_FILE_HOST,
    )

    assert missing == [sdist]
    assert wheel_url is not None and wheel_url.startswith(
        f"https://{PYPI_FILE_HOST}/packages/{wheel.name}#sha256="
    )
    assert [path.name for path in upload.iterdir()] == [sdist.name]


def test_complete_pypi_upload_stages_nothing(tmp_path: Path) -> None:
    dist, wheel, sdist = _dist(tmp_path)
    published = {
        wheel.name: _published(wheel, file_host=PYPI_FILE_HOST),
        sdist.name: _published(sdist, file_host=PYPI_FILE_HOST),
    }
    upload = tmp_path / "pypi-upload"

    missing, _ = prepare_upload(
        dist,
        upload,
        published,
        package=PACKAGE,
        version=VERSION,
        registry_name="PyPI",
        file_host=PYPI_FILE_HOST,
    )

    assert missing == []
    assert list(upload.iterdir()) == []


def test_approved_upload_revalidation_rejects_changed_copy(tmp_path: Path) -> None:
    dist, wheel, _ = _dist(tmp_path)
    upload = tmp_path / "pypi-upload"
    prepare_upload(
        dist,
        upload,
        {wheel.name: _published(wheel, file_host=PYPI_FILE_HOST)},
        package=PACKAGE,
        version=VERSION,
        registry_name="PyPI",
        file_host=PYPI_FILE_HOST,
    )
    staged = next(upload.iterdir())
    staged.write_bytes(b"substituted")

    with pytest.raises(RuntimeError, match="artifact hash mismatch"):
        validate_approved_upload(
            dist,
            upload,
            package=PACKAGE,
            version=VERSION,
        )


def test_approved_upload_revalidation_rejects_unexpected_file(tmp_path: Path) -> None:
    dist, _, _ = _dist(tmp_path)
    upload = tmp_path / "pypi-upload"
    prepare_upload(
        dist,
        upload,
        {},
        package=PACKAGE,
        version=VERSION,
        registry_name="PyPI",
        file_host=PYPI_FILE_HOST,
    )
    (upload / "unexpected.txt").write_text("unexpected", encoding="utf-8")

    with pytest.raises(RuntimeError, match="does not match its manifest"):
        validate_approved_upload(
            dist,
            upload,
            package=PACKAGE,
            version=VERSION,
        )


def test_testpypi_metadata_rejects_production_file_host() -> None:
    with pytest.raises(RuntimeError, match="unexpected artifact URL"):
        published_artifacts(
            {
                "urls": [
                    {
                        "filename": "netbox_sdk-0.0.11rc1-py3-none-any.whl",
                        "digests": {"sha256": "0" * 64},
                        "url": "https://files.pythonhosted.org/packages/netbox_sdk.whl",
                    }
                ]
            }
        )
