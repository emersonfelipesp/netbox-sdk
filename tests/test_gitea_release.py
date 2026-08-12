from __future__ import annotations

import base64
import csv
import hashlib
import io
import json
import stat
import subprocess
import tarfile
import zipfile
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.gitea_release import (
    MANIFEST_NAME,
    ArtifactRecord,
    BoundedHttpClient,
    GiteaRegistry,
    ReleaseError,
    RemoteState,
    TransferManifest,
    _main_validate_tag,
    _manifest_payload,
    _validate_wheel_record,
    classify_remote_state,
    prepare_transfer,
    reconcile_publication,
    validate_archive_source_binding,
    validate_transfer,
    validate_trusted_source_checkout,
)
from scripts.release_policy import (
    validate_exact_canonical_source,
    validate_gitea_candidate_tag,
)

pytestmark = pytest.mark.suite_sdk

PACKAGE = "netbox-sdk"
VERSION = "0.0.11rc2"
SOURCE_SHA = "a" * 40
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
license = "Apache-2.0"
license-files = ["LICENSE.txt"]
requires-python = ">=3.11,<3.14"
dependencies = ["demo-dependency>=1"]

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
        b"License-Expression: Apache-2.0\n"
        b"Requires-Python: <3.14,>=3.11\n"
        b"Requires-Dist: demo-dependency>=1\n"
        b'Requires-Dist: extra-dependency>=2; extra == "all"\n'
        b"Provides-Extra: all\n"
        b"Provides-Extra: empty\n"
        b"Dynamic: license-file\n\n"
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
    artifacts = tuple(
        ArtifactRecord(
            path.name, path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest()
        )
        for path in (transfer / WHEEL, transfer / SDIST)
    )
    manifest = TransferManifest(PACKAGE, VERSION, source_sha, artifacts)
    (transfer / MANIFEST_NAME).write_text(
        json.dumps(_manifest_payload(manifest), sort_keys=True), encoding="utf-8"
    )
    return transfer, manifest, repo


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
        )
    assert not transfer.exists()


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
    hostile = TransferManifest(PACKAGE, VERSION, manifest.source_sha, records)
    (transfer / MANIFEST_NAME).write_text(json.dumps(_manifest_payload(hostile)), encoding="utf-8")
    validate_transfer(
        transfer_dir=transfer,
        expected_package=PACKAGE,
        expected_version=VERSION,
        expected_source_sha=manifest.source_sha,
    )
    with pytest.raises(ReleaseError, match="trusted|differs"):
        validate_archive_source_binding(transfer_dir=transfer, manifest=hostile, source_root=repo)


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
    )


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
        revalidate_transfer=lambda: None,
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
            revalidate_transfer=lambda: None,
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
            revalidate_transfer=lambda: validations.append(True),
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
            revalidate_transfer=lambda: None,
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
    validate_gitea_candidate_tag(
        event_name="workflow_dispatch", ref_name=f"v{VERSION}", version=VERSION
    )
    for invalid in ("v0.0.11rc1", "0.0.11rc2", "v0.0.11"):
        with pytest.raises(RuntimeError):
            validate_gitea_candidate_tag(
                event_name="workflow_dispatch", ref_name=invalid, version=VERSION
            )
    output = tmp_path / "output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    assert _main_validate_tag(SimpleNamespace(event_name="push", tag=f"v{VERSION}")) == 0
    assert output.read_text() == f"tag=v{VERSION}\n"


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
        "workflow_dispatch:",
        '      - "v*rc*"',
        "runs-on: ci-untrusted-python312",
        "runs-on: mirror-host",
        "contents: read",
        "packages: write",
        "--no-isolation",
        "uv sync --locked --only-group publish --no-install-project",
        "uv 0.11.28",
        "3.12.13",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
        "actions/download-artifact@fa0a91b85d4f404e444e00e005971372dc801d16",
        "token: ''",
        "GITEA_TOKEN: ${{ github.token }}",
    )
    assert all(value in text for value in required)
    assert "GITHUB_ENV" not in text
    assert text.count("${{ github.token }}") == 1
    assert text.count("runs-on: ci-untrusted-python312") == 1
    assert text.count("uv 0.11.28") == 2
    assert text.count("contents: read") == 3
    assert text.count("packages: write") == 1
    assert "pull_request:" not in text and "release:" not in text
    publish_step = text.index("- name: Publish independently verified exact package")
    assert text.index("${{ github.token }}") > publish_step
    for line in text.splitlines():
        if "uses:" in line:
            assert "@" in line and len(line.split("@", 1)[1].split()[0]) == 40
    run_blocks = "\n".join(
        line for line in text.splitlines() if not line.lstrip().startswith(("env:", "RELEASE_TAG:"))
    )
    assert "${{ inputs." not in run_blocks


def test_private_registry_workflow_security_contract_and_mutations() -> None:
    workflow = Path(".gitea/workflows/publish-package.yml").read_text(encoding="utf-8")
    _assert_workflow_policy(workflow)
    mutations = (
        ("packages: write", "packages: read"),
        ("runs-on: mirror-host", "runs-on: ci-untrusted-python312"),
        ("token: ''", "token: ${{ github.token }}"),
        ("--no-isolation", "--isolation"),
        ("uv 0.11.28", "uv 0.11.29"),
        ("@ea165f8d65b6e75b540449e92b4886f43607fa02", "@v4"),
    )
    for old, new in mutations:
        mutated = workflow.replace(old, new, 1)
        with pytest.raises(AssertionError):
            _assert_workflow_policy(mutated)
