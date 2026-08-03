"""Tests for the ``nbx proxbox`` Typer command group."""

from __future__ import annotations

import json
from typing import Any

import pytest
from typer.testing import CliRunner

from netbox_cli import app as nbx_app
from netbox_cli import proxbox as proxbox_mod
from netbox_sdk.proxbox_sync import ScheduleResult, SseFrame

pytestmark = pytest.mark.suite_cli

runner = CliRunner()


class _RawClient:
    def __init__(self) -> None:
        self.closed = False
        self.fetched_job_ids: list[int] = []

    async def close(self) -> None:
        self.closed = True


def _install_fake_proxbox(
    monkeypatch: pytest.MonkeyPatch,
    *,
    frames: list[SseFrame],
    job: dict[str, Any],
    schedule: ScheduleResult | None = None,
    stream_error: Exception | None = None,
) -> _RawClient:
    raw = _RawClient()

    def _get_client() -> _RawClient:
        return raw

    class _FakeProxbox:
        @classmethod
        def from_client(cls, raw_client: Any) -> _FakeProxbox:
            assert raw_client is raw
            return cls()

        async def schedule(
            self,
            sync_types: list[str],
            *,
            proxmox_endpoint_ids: list[int] | None = None,
            job_name: str | None = None,
        ) -> ScheduleResult:
            assert proxmox_endpoint_ids is None
            assert job_name is None
            assert sync_types
            return schedule or ScheduleResult(ok=True, job_id=101, message="queued")

        async def stream_job(self, job_id: int, *, timeout: float | None = None):
            assert job_id == 101
            assert timeout is not None
            for frame in frames:
                yield frame
            if stream_error is not None:
                raise stream_error

        async def fetch_job(self, job_id: int) -> dict[str, Any]:
            assert job_id == 101
            raw.fetched_job_ids.append(job_id)
            return job

        async def resolve_endpoint(self, name_or_id: str | int) -> int:
            raise AssertionError(f"unexpected endpoint lookup: {name_or_id!r}")

    monkeypatch.setattr(proxbox_mod, "_get_client", _get_client)
    monkeypatch.setattr(proxbox_mod, "ProxboxSyncClient", _FakeProxbox)
    return raw


def test_proxbox_resources_command_lists_catalog_json() -> None:
    result = runner.invoke(nbx_app, ["proxbox", "resources", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    commands = {item["command"] for item in payload}
    assert "nbx proxbox endpoints/proxmox" in commands
    assert "nbx proxbox operations/deletion-requests" in commands
    deletion_request = next(
        item for item in payload if item["command"] == "nbx proxbox operations/deletion-requests"
    )
    assert deletion_request["actions"] == ["list", "get"]
    assert deletion_request["read_only"] is True


def test_proxbox_ops_command_shows_read_only_operations() -> None:
    result = runner.invoke(nbx_app, ["proxbox", "ops", "operations/deletion-requests", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert [item["action"] for item in payload] == ["list", "get"]
    assert {item["method"] for item in payload} == {"GET"}


def test_proxbox_generated_create_dry_run_resolves_endpoint_path() -> None:
    result = runner.invoke(
        nbx_app,
        [
            "proxbox",
            "endpoints",
            "proxmox",
            "create",
            "--dry-run",
            "--body-json",
            '{"name":"pve-prod"}',
        ],
    )

    assert result.exit_code == 0
    assert "POST" in result.stdout
    assert "/api/plugins/proxbox/endpoints/proxmox/" in result.stdout


def test_proxbox_generated_patch_dry_run_resolves_nested_path() -> None:
    result = runner.invoke(
        nbx_app,
        [
            "proxbox",
            "firewall",
            "rules",
            "patch",
            "--id",
            "7",
            "--dry-run",
            "--body-json",
            '{"enabled":false}',
        ],
    )

    assert result.exit_code == 0
    assert "PATCH" in result.stdout
    assert "/api/plugins/proxbox/firewall/rules/7/" in result.stdout


def test_proxbox_read_only_resources_do_not_register_write_commands() -> None:
    result = runner.invoke(
        nbx_app,
        [
            "proxbox",
            "operations",
            "deletion-requests",
            "patch",
            "--id",
            "1",
            "--body-json",
            '{"approved":true}',
        ],
    )

    assert result.exit_code != 0
    assert "No such command" in result.output


def test_proxbox_sync_requires_confirmation_before_building_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NETBOX_SDK_CONFIRM_WRITE", raising=False)

    def _fail_client() -> Any:
        pytest.fail("an unconfirmed sync must not construct an API client")

    monkeypatch.setattr(proxbox_mod, "_get_client", _fail_client)

    result = runner.invoke(nbx_app, ["proxbox", "sync"])

    assert result.exit_code != 0
    assert "Live NetBox writes require explicit confirmation" in result.output


def test_proxbox_sync_success_renders_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = _install_fake_proxbox(
        monkeypatch,
        frames=[
            SseFrame(event="step", data={"step": "schedule", "status": "started"}),
            SseFrame(
                event="item_progress",
                data={
                    "phase": "virtual-machines",
                    "message": "imported vm-1",
                    "item": {"name": "vm-1"},
                    "progress": {"current": 1, "total": 2, "percent": 50},
                },
            ),
            SseFrame(
                event="phase_summary",
                data={"phase": "virtual-machines", "result": {"created": 1, "failed": 0}},
            ),
            SseFrame(
                event="complete",
                data={"ok": True, "message": "done", "status": "completed"},
            ),
        ],
        job={"status": "completed", "error": "", "data": {}, "log_entries": []},
    )

    result = runner.invoke(nbx_app, ["proxbox", "sync", "-t", "virtual-machines", "--confirm"])

    assert result.exit_code == 0
    assert "Proxbox sync completed successfully" in result.stdout
    assert "virtual-machines" in result.stdout
    assert "created=1" in result.stdout
    assert raw.closed is True


def test_proxbox_sync_failure_merges_stream_and_job_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = _install_fake_proxbox(
        monkeypatch,
        frames=[
            SseFrame(
                event="error_detail",
                data={
                    "phase": "storage",
                    "item": {"name": "vm-1"},
                    "category": "validation",
                    "message": "vm-1 failed",
                    "detail": "bad disk",
                },
            ),
            SseFrame(
                event="complete",
                data={"ok": False, "message": "sync failed", "status": "errored"},
            ),
        ],
        job={
            "status": "errored",
            "error": "job failed",
            "data": {},
            "log_entries": [
                {
                    "level": "error",
                    "message": "throttled dropped error",
                    "data": {"phase": "storage", "detail": "authoritative log"},
                }
            ],
        },
    )

    result = runner.invoke(nbx_app, ["proxbox", "sync", "-t", "storage", "--confirm"])

    assert result.exit_code == 1
    assert "Proxbox Sync Errors" in result.stdout
    assert "vm-1 failed" in result.stdout
    assert "throttled dropped error" in result.stdout
    assert "job failed" in result.stdout
    assert raw.closed is True


def test_proxbox_sync_json_mode_outputs_final_object(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_proxbox(
        monkeypatch,
        frames=[
            SseFrame(event="complete", data={"ok": True, "message": "done", "status": "completed"})
        ],
        job={"status": "completed", "error": "", "data": {}, "log_entries": []},
    )

    result = runner.invoke(nbx_app, ["proxbox", "sync", "--json", "--confirm"])

    assert result.exit_code == 0
    assert '"job_id": 101' in result.stdout
    assert '"ok": true' in result.stdout
    assert "Recent Events" not in result.stdout


@pytest.mark.parametrize(
    ("stream_error", "job_status", "error_text"),
    [
        (TimeoutError("SSE stream timed out"), "running", "SSE stream timed out"),
        (RuntimeError("SSE protocol disconnect"), "errored", "SSE protocol disconnect"),
    ],
)
def test_proxbox_sync_stream_failure_fetches_and_reports_authoritative_job(
    monkeypatch: pytest.MonkeyPatch,
    stream_error: Exception,
    job_status: str,
    error_text: str,
) -> None:
    raw = _install_fake_proxbox(
        monkeypatch,
        frames=[],
        stream_error=stream_error,
        job={"status": job_status, "error": "", "data": {}, "log_entries": []},
    )

    result = runner.invoke(
        nbx_app,
        ["proxbox", "sync", "--json", "--confirm"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["job_id"] == 101
    assert payload["status"] == job_status
    assert error_text in payload["errors"][0]["detail"]
    assert raw.fetched_job_ids == [101]
    assert raw.closed is True


def test_frame_to_line_styles_error_frames() -> None:
    line = proxbox_mod.frame_to_line(
        SseFrame(
            event="error_detail",
            data={"phase": "devices", "message": "device failed", "detail": "bad role"},
        )
    )

    assert "device failed" in line.plain
    assert "red" in str(line.style)
