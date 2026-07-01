"""Tests for the ``nbx proxbox`` Typer command group."""

from __future__ import annotations

from typing import Any

import pytest
from typer.testing import CliRunner

from netbox_cli import app as nbx_app
from netbox_cli import proxbox as proxbox_mod
from netbox_sdk.proxbox_sync import ScheduleResult, SseFrame

pytestmark = pytest.mark.suite_cli

runner = CliRunner()


class _RawClient:
    closed = False

    async def close(self) -> None:
        self.closed = True


def _install_fake_proxbox(
    monkeypatch: pytest.MonkeyPatch,
    *,
    frames: list[SseFrame],
    job: dict[str, Any],
    schedule: ScheduleResult | None = None,
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

        async def fetch_job(self, job_id: int) -> dict[str, Any]:
            assert job_id == 101
            return job

        async def resolve_endpoint(self, name_or_id: str | int) -> int:
            raise AssertionError(f"unexpected endpoint lookup: {name_or_id!r}")

    monkeypatch.setattr(proxbox_mod, "_get_client", _get_client)
    monkeypatch.setattr(proxbox_mod, "ProxboxSyncClient", _FakeProxbox)
    return raw


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

    result = runner.invoke(nbx_app, ["proxbox", "sync", "-t", "virtual-machines"])

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

    result = runner.invoke(nbx_app, ["proxbox", "sync", "-t", "storage"])

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

    result = runner.invoke(nbx_app, ["proxbox", "sync", "--json"])

    assert result.exit_code == 0
    assert '"job_id": 101' in result.stdout
    assert '"ok": true' in result.stdout
    assert "Recent Events" not in result.stdout


def test_frame_to_line_styles_error_frames() -> None:
    line = proxbox_mod.frame_to_line(
        SseFrame(
            event="error_detail",
            data={"phase": "devices", "message": "device failed", "detail": "bad role"},
        )
    )

    assert "device failed" in line.plain
    assert "red" in str(line.style)
