from __future__ import annotations

import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest

from scripts.generate_typed_sdk import (
    DATAMODEL_CODE_GENERATOR_VERSION,
    RELEASE_PROVENANCE,
    RUFF_VERSION,
    _prepend_models_module_doc,
    _release_source_blob,
    apply_background_bulk_overlay,
    build_bindings,
    format_generated_artifacts,
    generate_models,
    validate_release_artifact_hashes,
    validate_release_bundle,
    validate_release_source,
    write_release_provenance,
)

pytestmark = pytest.mark.suite_sdk

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_OBJECT_PACK = (
    ROOT
    / "tests"
    / "fixtures"
    / "netbox-release-source-objects-fb63775283eb495a0c8219b5ce6ff57416b423df.pack"
)
UPSTREAM_OBJECT_PACK_CHECKSUM = "fb63775283eb495a0c8219b5ce6ff57416b423df"
UPSTREAM_RELEASE_REFS = {
    "v4.6.6": "fb8c455ba61b57119a70670612dfdd05e8438b10",
    "v4.7.0": "5f06007e4c9bacc93ce17c1e645fc1143d60df3d",
}


def test_model_generator_version_is_pinned() -> None:
    assert DATAMODEL_CODE_GENERATOR_VERSION == "0.55.0"
    assert RUFF_VERSION == "0.15.9"


def test_datamodel_code_generator_is_locked_and_installed() -> None:
    pin = f"datamodel-code-generator=={DATAMODEL_CODE_GENERATOR_VERSION}"
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pin in data["project"]["optional-dependencies"]["dev"]
    assert pin in data["dependency-groups"]["dev"]
    lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
    assert 'name = "datamodel-code-generator"' in lock
    assert f'version = "{DATAMODEL_CODE_GENERATOR_VERSION}"' in lock
    assert (
        importlib.metadata.version("datamodel-code-generator") == DATAMODEL_CODE_GENERATOR_VERSION
    )


def test_model_generation_invokes_locked_datamodel_codegen(monkeypatch, tmp_path) -> None:
    calls: list[list[str]] = []
    locked = "/opt/venv/bin/datamodel-codegen"

    def fake_which(name: str) -> str | None:
        if name == "datamodel-codegen":
            return locked
        return None

    def fake_run(command, **kwargs):
        calls.append(command)

    monkeypatch.setattr("scripts.generate_typed_sdk.shutil.which", fake_which)
    monkeypatch.setattr("scripts.generate_typed_sdk.subprocess.run", fake_run)
    generate_models("4.6", tmp_path / "schema.json", tmp_path / "models.py")

    assert calls[0][0] == locked
    assert "uvx" not in calls[0]
    assert "--disable-timestamp" in calls[0]


def test_model_generation_fails_closed_without_locked_generator(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("scripts.generate_typed_sdk.shutil.which", lambda name: None)
    with pytest.raises(RuntimeError, match="datamodel-codegen is not on PATH"):
        generate_models("4.6", tmp_path / "schema.json", tmp_path / "models.py")


def test_v46_artifact_provenance_is_current() -> None:
    provenance_path = (
        ROOT / "netbox_sdk" / "reference" / "openapi" / "netbox-openapi-4.6.provenance.json"
    )
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    schema = json.loads(
        (ROOT / "netbox_sdk" / "reference" / "openapi" / "netbox-openapi-4.6.json").read_text(
            encoding="utf-8"
        )
    )

    assert provenance["netbox_release"] == "v4.6.6"
    assert provenance["release_commit"] == "fb8c455ba61b57119a70670612dfdd05e8438b10"
    assert provenance["source_blob_sha"] == "024d34500a04ec876fb3b32fa18c685e953a02f8"
    assert (
        provenance["source_sha256"]
        == "915a25d48e638ea49218f142af30271812f5f75f67ad619b05a9a9300c04f7d8"
    )
    assert provenance["generator"] == {
        "name": "datamodel-code-generator",
        "version": DATAMODEL_CODE_GENERATOR_VERSION,
        "timestamp_disabled": True,
    }
    assert provenance["formatter"] == {"name": "ruff", "version": RUFF_VERSION}
    assert schema["info"]["version"] == "4.6.6"
    assert len(schema["paths"]) == 308
    assert len(schema["components"]["schemas"]) == 1043
    assert "/api/extras/scripts/upload/{id}/" in schema["paths"]

    artifact_paths = {
        "netbox-openapi-4.6.json": ROOT
        / "netbox_sdk"
        / "reference"
        / "openapi"
        / "netbox-openapi-4.6.json",
        "models/v4_6.py": ROOT / "netbox_sdk" / "models" / "v4_6.py",
        "typed_versions/v4_6.py": ROOT / "netbox_sdk" / "typed_versions" / "v4_6.py",
    }
    for name, path in artifact_paths.items():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == provenance["artifacts"][name]


def _materialize_upstream_object_fixture(tmp_path: Path) -> Path:
    repository = tmp_path / "netbox-upstream.git"
    subprocess.run(["git", "init", "--bare", "-q", str(repository)], check=True)
    pack_path = repository / "objects" / "pack" / f"pack-{UPSTREAM_OBJECT_PACK_CHECKSUM}.pack"
    shutil.copyfile(UPSTREAM_OBJECT_PACK, pack_path)
    indexed = subprocess.run(
        ["git", "index-pack", str(pack_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert indexed.stdout.strip() == UPSTREAM_OBJECT_PACK_CHECKSUM
    for tag, commit in UPSTREAM_RELEASE_REFS.items():
        subprocess.run(
            ["git", "--git-dir", str(repository), "update-ref", f"refs/tags/{tag}", commit],
            check=True,
        )
    return repository


def test_every_recorded_source_digest_matches_its_upstream_blob(
    tmp_path: Path,
) -> None:
    repository = _materialize_upstream_object_fixture(tmp_path)
    assert {
        release["netbox_release"]: release["release_commit"]
        for release in RELEASE_PROVENANCE.values()
    } == UPSTREAM_RELEASE_REFS

    for version, release in RELEASE_PROVENANCE.items():
        blob_id = _release_source_blob(
            repository,
            release["release_commit"],
            release["source_path"],
        )
        assert blob_id == release["source_blob_sha"]
        blob = subprocess.run(
            ["git", "-C", str(repository), "cat-file", "blob", blob_id],
            check=True,
            capture_output=True,
        ).stdout
        blob_digest = hashlib.sha256(blob).hexdigest()
        assert blob_digest == release["source_sha256"]

        sidecar_path = (
            ROOT
            / "netbox_sdk"
            / "reference"
            / "openapi"
            / f"netbox-openapi-{version}.provenance.json"
        )
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
        assert sidecar["netbox_release"] == release["netbox_release"]
        assert sidecar["release_commit"] == release["release_commit"]
        assert sidecar["source_path"] == release["source_path"]
        assert sidecar["source_blob_sha"] == blob_id
        assert sidecar["source_sha256"] == blob_digest


def test_v46_typed_regeneration_matches_committed_artifact(tmp_path) -> None:
    schema_path = ROOT / "netbox_sdk" / "reference" / "openapi" / "netbox-openapi-4.6.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    output_path = tmp_path / "v4_6.py"
    output_path.write_text(build_bindings("4.6", schema), encoding="utf-8")

    format_generated_artifacts([output_path])

    committed = ROOT / "netbox_sdk" / "typed_versions" / "v4_6.py"
    assert output_path.read_bytes() == committed.read_bytes()


def test_v47_artifact_provenance_is_current() -> None:
    provenance_path = (
        ROOT / "netbox_sdk" / "reference" / "openapi" / "netbox-openapi-4.7.provenance.json"
    )
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    schema = json.loads(
        (ROOT / "netbox_sdk" / "reference" / "openapi" / "netbox-openapi-4.7.json").read_text(
            encoding="utf-8"
        )
    )

    assert provenance["netbox_release"] == "v4.7.0"
    assert provenance["release_commit"] == "5f06007e4c9bacc93ce17c1e645fc1143d60df3d"
    assert provenance["source_blob_sha"] == "ea7f7e9c38c37d2139c6600db584b249571524a6"
    assert (
        provenance["source_sha256"]
        == "be7f971179b1d6ba03b590c08ebe65966a32220ea8fdfd272f60dc5d66ea9008"
    )
    assert provenance["generator"] == {
        "name": "datamodel-code-generator",
        "version": DATAMODEL_CODE_GENERATOR_VERSION,
        "timestamp_disabled": True,
    }
    assert provenance["formatter"] == {"name": "ruff", "version": RUFF_VERSION}
    assert schema["info"]["version"] == "4.7.0"
    assert len(schema["paths"]) == 322
    assert len(schema["components"]["schemas"]) == 1109
    # 4.7 introduces cooling infrastructure and module bay types alongside the
    # 4.6 surface; assert one of each so a silently truncated bundle is caught.
    assert "/api/dcim/cooling-sources/" in schema["paths"]
    assert "/api/dcim/module-bay-types/" in schema["paths"]
    assert "/api/extras/scripts/upload/{id}/" in schema["paths"]

    artifact_paths = {
        "netbox-openapi-4.7.json": ROOT
        / "netbox_sdk"
        / "reference"
        / "openapi"
        / "netbox-openapi-4.7.json",
        "models/v4_7.py": ROOT / "netbox_sdk" / "models" / "v4_7.py",
        "typed_versions/v4_7.py": ROOT / "netbox_sdk" / "typed_versions" / "v4_7.py",
    }
    for name, path in artifact_paths.items():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == provenance["artifacts"][name]

    assert provenance["artifacts"]["netbox-openapi-4.7.json"] == provenance["source_sha256"]

    validate_release_artifact_hashes("4.7", artifact_paths["netbox-openapi-4.7.json"])


def test_release_verification_rejects_coupled_artifact_and_sidecar_drift(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A matching sidecar edit must not certify an altered generated artifact."""
    schema_root = tmp_path / "openapi"
    model_root = tmp_path / "models"
    typed_root = tmp_path / "typed_versions"
    for directory in (schema_root, model_root, typed_root):
        directory.mkdir()

    source_root = ROOT / "netbox_sdk"
    bundled = schema_root / "netbox-openapi-4.7.json"
    provenance = schema_root / "netbox-openapi-4.7.provenance.json"
    model = model_root / "v4_7.py"
    typed = typed_root / "v4_7.py"
    shutil.copyfile(source_root / "reference" / "openapi" / bundled.name, bundled)
    shutil.copyfile(source_root / "reference" / "openapi" / provenance.name, provenance)
    shutil.copyfile(source_root / "models" / model.name, model)
    shutil.copyfile(source_root / "typed_versions" / typed.name, typed)

    typed.write_text(typed.read_text(encoding="utf-8") + "\n# coupled drift\n", encoding="utf-8")
    payload = json.loads(provenance.read_text(encoding="utf-8"))
    payload["artifacts"]["typed_versions/v4_7.py"] = hashlib.sha256(typed.read_bytes()).hexdigest()
    provenance.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    monkeypatch.setattr("scripts.generate_typed_sdk.MODELS_ROOT", model_root)
    monkeypatch.setattr("scripts.generate_typed_sdk.TYPED_ROOT", typed_root)
    with pytest.raises(ValueError, match="deterministic regeneration mismatch.*typed_versions"):
        validate_release_artifact_hashes("4.7", bundled)


def test_release_verification_rejects_reformatted_bundle_and_sidecar_drift(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A matching sidecar edit must not certify reserialized upstream bytes."""
    schema_root = tmp_path / "openapi"
    model_root = tmp_path / "models"
    typed_root = tmp_path / "typed_versions"
    for directory in (schema_root, model_root, typed_root):
        directory.mkdir()

    source_root = ROOT / "netbox_sdk"
    bundled = schema_root / "netbox-openapi-4.7.json"
    provenance = schema_root / "netbox-openapi-4.7.provenance.json"
    model = model_root / "v4_7.py"
    typed = typed_root / "v4_7.py"
    shutil.copyfile(source_root / "reference" / "openapi" / bundled.name, bundled)
    shutil.copyfile(source_root / "reference" / "openapi" / provenance.name, provenance)
    shutil.copyfile(source_root / "models" / model.name, model)
    shutil.copyfile(source_root / "typed_versions" / typed.name, typed)

    document = json.loads(bundled.read_text(encoding="utf-8"))
    bundled.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    mutated_digest = hashlib.sha256(bundled.read_bytes()).hexdigest()
    assert mutated_digest != RELEASE_PROVENANCE["4.7"]["source_sha256"]
    payload = json.loads(provenance.read_text(encoding="utf-8"))
    payload["artifacts"][bundled.name] = mutated_digest
    provenance.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    monkeypatch.setattr("scripts.generate_typed_sdk.MODELS_ROOT", model_root)
    monkeypatch.setattr("scripts.generate_typed_sdk.TYPED_ROOT", typed_root)
    with pytest.raises(ValueError, match="reviewed upstream bytes"):
        validate_release_artifact_hashes("4.7", bundled)


def test_v47_typed_regeneration_matches_committed_artifact(tmp_path) -> None:
    schema_path = ROOT / "netbox_sdk" / "reference" / "openapi" / "netbox-openapi-4.7.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    output_path = tmp_path / "v4_7.py"
    # Mirror the generator exactly: bindings are built from the background-overlaid
    # schema. Regenerating without the overlay would compare the committed artifact
    # against a document the generator never uses, so this guard would fail for a
    # reason unrelated to drift.
    output_path.write_text(
        build_bindings("4.7", apply_background_bulk_overlay("4.7", schema)), encoding="utf-8"
    )

    format_generated_artifacts([output_path])

    committed = ROOT / "netbox_sdk" / "typed_versions" / "v4_7.py"
    assert output_path.read_bytes() == committed.read_bytes()


def test_v47_model_regeneration_matches_committed_artifact(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("UV_OFFLINE", "1")
    schema_path = ROOT / "netbox_sdk" / "reference" / "openapi" / "netbox-openapi-4.7.json"
    output_path = tmp_path / "v4_7.py"
    generate_models("4.7", schema_path, output_path)
    _prepend_models_module_doc(output_path, "4.7")
    format_generated_artifacts([output_path])
    committed = ROOT / "netbox_sdk" / "models" / "v4_7.py"
    assert output_path.read_bytes() == committed.read_bytes()


def test_release_source_validation_rejects_unpinned_input(tmp_path) -> None:
    source = tmp_path / "source.json"
    source.write_text("not the official schema", encoding="utf-8")

    with pytest.raises(ValueError, match="source SHA-256 mismatch"):
        validate_release_source("4.6", source)


def _pinned_test_release(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    repository = tmp_path / "upstream"
    repository.mkdir()
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    source = repository / "contrib" / "openapi.json"
    source.parent.mkdir()
    source.write_text('{"openapi":"3.0.0","paths":{}}\n', encoding="utf-8")
    other = repository / "other.txt"
    other.write_text("different blob\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repository), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "-c",
            "user.name=Provenance Test",
            "-c",
            "user.email=provenance@example.com",
            "commit",
            "-qm",
            "Release test",
        ],
        check=True,
    )
    subprocess.run(["git", "-C", str(repository), "tag", "v9.9.9"], check=True)
    commit = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    source_blob = _release_source_blob(repository, commit, "contrib/openapi.json")
    other_blob = _release_source_blob(repository, commit, "other.txt")
    monkeypatch.setitem(
        RELEASE_PROVENANCE,
        "test",
        {
            "netbox_release": "v9.9.9",
            "release_commit": commit,
            "source_path": "contrib/openapi.json",
            "source_blob_sha": source_blob,
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "source_url": "https://example.invalid/openapi.json",
            "other_blob_sha": other_blob,
        },
    )
    return repository, source


def test_release_source_binds_tag_commit_blob_and_bytes(monkeypatch, tmp_path) -> None:
    repository, source = _pinned_test_release(tmp_path, monkeypatch)

    validate_release_source("test", source, release_repository=repository)


def test_release_source_fails_closed_without_git_checkout(monkeypatch, tmp_path) -> None:
    _repository, source = _pinned_test_release(tmp_path, monkeypatch)

    with pytest.raises(ValueError, match="requires an upstream Git checkout"):
        validate_release_source("test", source)


def test_ci_verifies_upstream_release_bundle() -> None:
    workflow = (ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")

    assert "--release-repository /tmp/netbox-source" in workflow
    assert "--verify-only" in workflow
    assert "--source /tmp/netbox-source/contrib/openapi.json" in workflow


def test_release_source_rejects_wrong_commit(monkeypatch, tmp_path) -> None:
    repository, source = _pinned_test_release(tmp_path, monkeypatch)
    monkeypatch.setitem(RELEASE_PROVENANCE["test"], "release_commit", "0" * 40)

    with pytest.raises(ValueError, match="Cannot verify immutable"):
        validate_release_source("test", source, release_repository=repository)


def test_release_source_rejects_wrong_blob(monkeypatch, tmp_path) -> None:
    repository, source = _pinned_test_release(tmp_path, monkeypatch)
    release = RELEASE_PROVENANCE["test"]
    monkeypatch.setitem(release, "source_blob_sha", release["other_blob_sha"])

    with pytest.raises(ValueError, match="source blob mismatch"):
        validate_release_source("test", source, release_repository=repository)


def test_release_bundle_rejects_reformatted_document_drift(tmp_path) -> None:
    source = tmp_path / "source.json"
    bundle = tmp_path / "bundle.json"
    source.write_text('{"paths":{}}\n', encoding="utf-8")
    bundle.write_text('{\n  "paths": {}\n}\n', encoding="utf-8")

    with pytest.raises(ValueError, match="not byte-for-byte identical"):
        validate_release_bundle("4.7", source, bundle)


def test_provenance_writer_hashes_generated_artifacts(monkeypatch, tmp_path) -> None:
    source = tmp_path / "source.json"
    bundled = tmp_path / "netbox-openapi-4.6.json"
    model = tmp_path / "v4_6-model.py"
    typed = tmp_path / "v4_6-typed.py"
    for path, contents in (
        (source, '{"openapi":"3.0.0","paths":{}}'),
        (bundled, '{"paths":{},"openapi":"3.0.0"}'),
        (model, "model"),
        (typed, "typed"),
    ):
        path.write_text(contents, encoding="utf-8")

    release = RELEASE_PROVENANCE["4.6"]
    monkeypatch.setitem(release, "source_sha256", hashlib.sha256(source.read_bytes()).hexdigest())
    verified: list[tuple[str, Path, Path]] = []
    monkeypatch.setattr(
        "scripts.generate_typed_sdk._validate_release_git_objects",
        lambda version, path, repository: verified.append((version, path, repository)),
    )

    output = write_release_provenance(
        "4.6",
        source_path=source,
        release_repository=tmp_path,
        bundled_path=bundled,
        model_path=model,
        typed_path=typed,
    )

    assert output is not None
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert verified == [("4.6", source, tmp_path)]
    assert payload["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert payload["artifacts"][bundled.name] == hashlib.sha256(bundled.read_bytes()).hexdigest()
    assert payload["artifacts"][f"models/{model.name}"] == hashlib.sha256(b"model").hexdigest()
    assert (
        payload["artifacts"][f"typed_versions/{typed.name}"] == hashlib.sha256(b"typed").hexdigest()
    )


def test_generation_keeps_collection_and_detail_query_models_distinct() -> None:
    schema = {
        "paths": {
            "/api/dcim/devices/": {
                "get": {
                    "operationId": "dcim_devices_list",
                    "parameters": [
                        {
                            "in": "query",
                            "name": "tag__any",
                            "schema": {"type": "array", "items": {"type": "string"}},
                        },
                    ],
                }
            },
            "/api/dcim/devices/{id}/": {
                "get": {
                    "operationId": "dcim_devices_retrieve",
                    "parameters": [
                        {"in": "query", "name": "exclude", "schema": {"type": "string"}},
                    ],
                }
            },
        }
    }

    generated = build_bindings("4.6", schema)

    assert "class DcimDevicesRootGetQuery(BaseModel):" in generated
    assert "class DcimDevicesDetailGetQuery(BaseModel):" in generated
    assert "tag_any: list[str] | None = Field(None, alias='tag__any')" in generated
    assert "exclude: str | None = None" in generated


def test_generation_selects_multipart_for_binary_request_fields() -> None:
    schema = {
        "components": {
            "schemas": {
                "ScriptModuleRequest": {
                    "type": "object",
                    "properties": {
                        "file": {"type": "string", "format": "binary"},
                    },
                    "required": ["file"],
                }
            }
        },
        "paths": {
            "/api/extras/scripts/upload/": {
                "post": {
                    "operationId": "extras_scripts_upload_create",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ScriptModuleRequest"}
                            },
                            "multipart/form-data": {
                                "schema": {"$ref": "#/components/schemas/ScriptModuleRequest"}
                            },
                        }
                    },
                }
            }
        },
    }

    generated = build_bindings("4.6", schema)

    assert "body: ScriptModuleRequest | dict[str, Any]" in generated
    assert "return await self._typed_multipart_request(" in generated
    assert "binary_field_names=('file',)" in generated


def test_generation_preserves_raw_branching_for_core_only_schema() -> None:
    generated = build_bindings("4.6", {"paths": {}})

    assert "RawBranchingApp" in generated
    assert "class PluginsApp(TypedAppBase):" in generated
    assert "def branching(self) -> RawBranchingApp:" in generated
    assert "self.plugins = PluginsApp(self)" in generated
