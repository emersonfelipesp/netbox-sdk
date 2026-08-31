from __future__ import annotations

import hashlib
import importlib.metadata
import json
import tomllib
from pathlib import Path

import pytest

from scripts.generate_typed_sdk import (
    DATAMODEL_CODE_GENERATOR_VERSION,
    RELEASE_PROVENANCE,
    RUFF_VERSION,
    _prepend_models_module_doc,
    apply_background_bulk_overlay,
    apply_write_compat_overlay,
    build_bindings,
    format_generated_artifacts,
    generate_models,
    validate_release_source,
    write_release_provenance,
)

pytestmark = pytest.mark.suite_sdk

ROOT = Path(__file__).resolve().parents[1]


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
        == "c1a3e2dee07a7a5bfedd9221c3495597cd2624baa32695800d1f75edbc5c044e"
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

    assert provenance["netbox_release"] == "v4.7.0-beta2"
    assert provenance["release_commit"] == "aa1d49d0f5021a28e6efc2d0364b84c5bcec7137"
    assert provenance["source_blob_sha"] == "1a3e6621a50520515652f969e9736da2545704c2"
    assert (
        provenance["source_sha256"]
        == "1408f6421f45720ecf25aa0edb777f185f74f9a87af887b5eeb73fee8012b880"
    )
    assert provenance["generator"] == {
        "name": "datamodel-code-generator",
        "version": DATAMODEL_CODE_GENERATOR_VERSION,
        "timestamp_disabled": True,
    }
    assert provenance["formatter"] == {"name": "ruff", "version": RUFF_VERSION}
    assert schema["info"]["version"] == "4.7.0-beta2"
    assert len(schema["paths"]) == 322
    assert len(schema["components"]["schemas"]) == 1099
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
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    overlaid = apply_write_compat_overlay("4.7", schema)
    overlay_path = tmp_path / "netbox-openapi-4.7.overlaid.json"
    overlay_path.write_text(json.dumps(overlaid, indent=2), encoding="utf-8")
    output_path = tmp_path / "v4_7.py"
    generate_models("4.7", overlay_path, output_path)
    _prepend_models_module_doc(output_path, "4.7")
    format_generated_artifacts([output_path])
    committed = ROOT / "netbox_sdk" / "models" / "v4_7.py"
    assert output_path.read_bytes() == committed.read_bytes()


def test_release_source_validation_rejects_unpinned_input(tmp_path) -> None:
    source = tmp_path / "source.json"
    source.write_text("not the official schema", encoding="utf-8")

    with pytest.raises(ValueError, match="source SHA-256 mismatch"):
        validate_release_source("4.6", source)


def test_provenance_writer_hashes_generated_artifacts(monkeypatch, tmp_path) -> None:
    source = tmp_path / "source.json"
    bundled = tmp_path / "netbox-openapi-4.6.json"
    model = tmp_path / "v4_6-model.py"
    typed = tmp_path / "v4_6-typed.py"
    for path, contents in (
        (source, "source"),
        (bundled, "schema"),
        (model, "model"),
        (typed, "typed"),
    ):
        path.write_text(contents, encoding="utf-8")

    release = RELEASE_PROVENANCE["4.6"]
    monkeypatch.setitem(release, "source_sha256", hashlib.sha256(b"source").hexdigest())

    output = write_release_provenance(
        "4.6",
        source_path=source,
        bundled_path=bundled,
        model_path=model,
        typed_path=typed,
    )

    assert output is not None
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["source_sha256"] == hashlib.sha256(b"source").hexdigest()
    assert payload["artifacts"][bundled.name] == hashlib.sha256(b"schema").hexdigest()
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
