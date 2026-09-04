from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import get_args

import pytest
from pydantic import ValidationError

from netbox_sdk.versioning import (
    DEFAULT_NETBOX_VERSION,
    SUPPORTED_NETBOX_VERSIONS,
    ReleaseLine,
    SupportedNetBoxVersion,
    UnsupportedNetBoxVersionError,
    bundled_openapi_path,
    describe_supported_versions,
    latest_stable_line,
    normalize_netbox_version,
    release_line,
    release_lines,
    version_module_suffix,
)
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
VERSION = "0.0.11"
EXPECTED_NETBOX_RELEASE_LINES = ("4.7", "4.6", "4.5", "4.4", "4.3")
EXPECTED_RELEASE_RECORDS = {
    "4.7": {
        "line": "4.7",
        "status": "stable",
        "openapi_asset": "netbox-openapi-4.7.json",
        "models_module": "netbox_sdk.models.v4_7",
        "typed_module": "netbox_sdk.typed_versions.v4_7",
        "background_bulk_overlay": True,
        "ga_response_shapes": True,
    },
    "4.6": {
        "line": "4.6",
        "status": "stable",
        "openapi_asset": "netbox-openapi-4.6.json",
        "models_module": "netbox_sdk.models.v4_6",
        "typed_module": "netbox_sdk.typed_versions.v4_6",
        "background_bulk_overlay": False,
        "ga_response_shapes": False,
    },
    "4.5": {
        "line": "4.5",
        "status": "stable",
        "openapi_asset": "netbox-openapi-4.5.json",
        "models_module": "netbox_sdk.models.v4_5",
        "typed_module": "netbox_sdk.typed_versions.v4_5",
        "background_bulk_overlay": False,
        "ga_response_shapes": False,
    },
    "4.4": {
        "line": "4.4",
        "status": "stable",
        "openapi_asset": "netbox-openapi-4.4.json",
        "models_module": "netbox_sdk.models.v4_4",
        "typed_module": "netbox_sdk.typed_versions.v4_4",
        "background_bulk_overlay": False,
        "ga_response_shapes": False,
    },
    "4.3": {
        "line": "4.3",
        "status": "stable",
        "openapi_asset": "netbox-openapi-4.3.json",
        "models_module": "netbox_sdk.models.v4_3",
        "typed_module": "netbox_sdk.typed_versions.v4_3",
        "background_bulk_overlay": False,
        "ga_response_shapes": False,
    },
}


def test_netbox_release_registry_preserves_public_contract() -> None:
    records = release_lines()

    assert get_args(SupportedNetBoxVersion) == EXPECTED_NETBOX_RELEASE_LINES
    assert SUPPORTED_NETBOX_VERSIONS == EXPECTED_NETBOX_RELEASE_LINES
    assert tuple(record.line for record in records) == EXPECTED_NETBOX_RELEASE_LINES
    assert {record.line: record.model_dump() for record in records} == EXPECTED_RELEASE_RECORDS
    assert all(isinstance(record, ReleaseLine) for record in records)
    with pytest.raises(ValidationError):
        setattr(records[0], "line", "9.9")
    assert DEFAULT_NETBOX_VERSION == "4.7"
    assert latest_stable_line() == "4.7"
    assert describe_supported_versions() == "4.3, 4.4, 4.5, 4.6, 4.7"
    assert normalize_netbox_version(None) == "4.7"
    assert release_line("v4.5.10").line == "4.5"
    assert normalize_netbox_version("v4.5.10") == "4.5"
    with pytest.raises(UnsupportedNetBoxVersionError, match="Supported release lines"):
        normalize_netbox_version("3.9")

    for line in SUPPORTED_NETBOX_VERSIONS:
        expected = EXPECTED_RELEASE_RECORDS[line]
        assert bundled_openapi_path(line).name == expected["openapi_asset"]
        assert version_module_suffix(line) == expected["models_module"].rsplit(".v", 1)[1]


def test_typed_api_typing_surface_covers_every_registered_line() -> None:
    """Every registered line must be reachable, and correctly typed, statically.

    ``SupportedNetBoxVersion`` is a ``Literal`` and ``typed_api`` is a set of
    ``@overload`` stubs, so neither can be computed from the registry. A line can
    therefore be registered, work at runtime, and still be rejected or MIS-typed
    by the public typing surface.

    This guard asserts the exact literal-to-return-type mapping, the
    ``TYPE_CHECKING`` imports, and the ``TypedApiClient`` union membership by
    parsing the AST. A substring search is not enough: removing a class from the
    union leaves its name present in the import and the overload, and swapping an
    overload's return type leaves every literal and class name intact.
    """
    source = (Path(__file__).resolve().parents[1] / "netbox_sdk" / "typed_api.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)

    def _literal_value(node: ast.expr | None) -> str | None:
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
            if node.value.id != "Literal":
                return None
            inner = node.slice
            if isinstance(inner, ast.Constant) and isinstance(inner.value, str):
                return inner.value
        return None

    def _flatten_union(node: ast.expr) -> set[str]:
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return _flatten_union(node.left) | _flatten_union(node.right)
        if isinstance(node, ast.Name):
            return {node.id}
        return set()

    # literal -> declared return type, for each @overload of typed_api
    overload_map: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != "typed_api":
            continue
        if not any(isinstance(d, ast.Name) and d.id == "overload" for d in node.decorator_list):
            continue
        literal = _literal_value(
            next((a.annotation for a in node.args.kwonlyargs if a.arg == "netbox_version"), None)
        )
        returns = node.returns
        if literal is not None and isinstance(returns, ast.Name):
            overload_map[literal] = returns.id

    # TypedApiClient union members
    union_members: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "TypedApiClient" and node.value is not None:
                union_members = _flatten_union(node.value)

    # names imported under TYPE_CHECKING
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
            "netbox_sdk.typed_versions."
        ):
            imported.update(alias.name for alias in node.names)

    expected_map = {
        line: f"TypedApiV{line.replace('.', '_')}" for line in SUPPORTED_NETBOX_VERSIONS
    }
    assert overload_map == expected_map, (
        "typed_api overloads must map each registered line to its own typed class; "
        f"got {overload_map}, expected {expected_map}"
    )
    assert union_members == set(expected_map.values()), (
        f"TypedApiClient union is {sorted(union_members)}, expected {sorted(expected_map.values())}"
    )
    assert imported == set(expected_map.values()), (
        f"TYPE_CHECKING imports are {sorted(imported)}, expected {sorted(expected_map.values())}"
    )
    assert set(SUPPORTED_NETBOX_VERSIONS) == set(EXPECTED_NETBOX_RELEASE_LINES)


def test_netbox_release_registry_and_artifacts_are_bidirectionally_complete() -> None:
    package_root = Path(__file__).resolve().parents[1] / "netbox_sdk"
    openapi_root = package_root / "reference" / "openapi"
    models_root = package_root / "models"
    typed_root = package_root / "typed_versions"

    assert openapi_root.is_dir()
    assert models_root.is_dir()
    assert typed_root.is_dir()

    expected_lines = set(EXPECTED_NETBOX_RELEASE_LINES)
    records = {record.line: record for record in release_lines()}
    assert set(records) == expected_lines

    openapi_lines = {
        name.removeprefix("netbox-openapi-").removesuffix(".json")
        for path in openapi_root.glob("netbox-openapi-*.json")
        if (name := path.name).removeprefix("netbox-openapi-").removesuffix(".json").count(".") == 1
    }
    models_lines = {
        path.stem.removeprefix("v").replace("_", ".") for path in models_root.glob("v*_*.py")
    }
    typed_lines = {
        path.stem.removeprefix("v").replace("_", ".") for path in typed_root.glob("v*_*.py")
    }

    assert openapi_lines == expected_lines
    assert models_lines == expected_lines
    assert typed_lines == expected_lines

    for line, expected in EXPECTED_RELEASE_RECORDS.items():
        record = records[line]
        assert (openapi_root / expected["openapi_asset"]).is_file()
        assert (
            package_root
            / f"{expected['models_module'].removeprefix('netbox_sdk.').replace('.', '/')}.py"
        ).is_file()
        assert (
            package_root
            / f"{expected['typed_module'].removeprefix('netbox_sdk.').replace('.', '/')}.py"
        ).is_file()
        assert record.model_dump() == expected


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
    wheel = dist / "netbox_sdk-0.0.11-py3-none-any.whl"
    sdist = dist / "netbox_sdk-0.0.11.tar.gz"
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
    unexpected = tmp_path / "netbox_sdk-0.0.11-cp313-cp313-manylinux.whl"
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
        "netbox_sdk-0.0.11-py3-none-any.whl.sig",
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
    (dist / "netbox_sdk-0.0.11-1-py3-none-any.whl").write_bytes(b"extra")

    with pytest.raises(RuntimeError, match="exactly one wheel and one source distribution"):
        validate_local_artifacts(dist, package=PACKAGE, version=VERSION)


@pytest.mark.parametrize(
    ("artifact", "replacement"),
    [
        ("wheel", "other_sdk-0.0.11-py3-none-any.whl"),
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
                        "filename": "netbox_sdk-0.0.11-py3-none-any.whl",
                        "digests": {"sha256": "0" * 64},
                        "url": "https://files.pythonhosted.org/packages/netbox_sdk.whl",
                    }
                ]
            }
        )
