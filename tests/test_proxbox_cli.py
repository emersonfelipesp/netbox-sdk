"""Tests for the ``nbx proxbox`` Typer command group."""

from __future__ import annotations

import json
from typing import Any

import pytest
from conftest import cli_json
from typer.testing import CliRunner

from netbox_cli import app as nbx_app
from netbox_cli import proxbox as proxbox_mod
from netbox_sdk.proxbox_sync import ProxboxSyncError, ScheduleResult, SseFrame

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
    job: dict[str, Any] | list[dict[str, Any]],
    schedule: ScheduleResult | None = None,
    stream_error: Exception | None = None,
) -> _RawClient:
    raw = _RawClient()
    jobs = list(job) if isinstance(job, list) else [job]

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
            if len(jobs) > 1:
                return jobs.pop(0)
            return jobs[0]

        async def resolve_endpoint(self, name_or_id: str | int) -> int:
            raise AssertionError(f"unexpected endpoint lookup: {name_or_id!r}")

    monkeypatch.setattr(proxbox_mod, "_get_client", _get_client)
    monkeypatch.setattr(proxbox_mod, "ProxboxSyncClient", _FakeProxbox)
    return raw


def test_proxbox_resources_command_lists_catalog_json() -> None:
    result = runner.invoke(nbx_app, ["proxbox", "resources", "--json"])

    assert result.exit_code == 0
    payload = cli_json(result.stdout)
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
    payload = cli_json(result.stdout)
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


def test_proxbox_tui_requires_confirmation_before_building_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NETBOX_SDK_CONFIRM_WRITE", raising=False)
    monkeypatch.setattr(
        proxbox_mod,
        "load_tui_callables",
        lambda *args: (
            lambda: ("netbox-dark",),
            lambda theme: theme,
            lambda **kwargs: pytest.fail("an unconfirmed TUI must not launch"),
        ),
    )

    def _fail_client() -> Any:
        pytest.fail("an unconfirmed TUI must not construct an API client")

    monkeypatch.setattr(proxbox_mod, "_get_client", _fail_client)

    result = runner.invoke(nbx_app, ["proxbox", "tui"])

    assert result.exit_code != 0
    assert "Live NetBox writes require explicit confirmation" in result.output


def test_proxbox_tui_launches_when_confirmed(monkeypatch: pytest.MonkeyPatch) -> None:
    client = object()
    launches: list[dict[str, Any]] = []
    monkeypatch.setattr(
        proxbox_mod,
        "load_tui_callables",
        lambda *args: (
            lambda: ("netbox-dark",),
            lambda theme: theme,
            lambda **kwargs: launches.append(kwargs),
        ),
    )
    monkeypatch.setattr(proxbox_mod, "_get_client", lambda: client)

    result = runner.invoke(nbx_app, ["proxbox", "tui", "--confirm"])

    assert result.exit_code == 0
    assert launches == [{"client": client, "theme_name": None}]


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


def test_proxbox_sync_stream_failure_with_terminal_success_is_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = _install_fake_proxbox(
        monkeypatch,
        frames=[],
        stream_error=RuntimeError("SSE protocol disconnect"),
        job={"status": "completed", "error": "", "data": {}, "log_entries": []},
    )

    result = runner.invoke(
        nbx_app,
        ["proxbox", "sync", "--json", "--confirm"],
    )

    assert result.exit_code == 0
    payload = cli_json(result.stdout)
    assert payload["job_id"] == 101
    assert payload["status"] == "completed"
    assert payload["ok"] is True
    assert payload["errors"] == []
    assert "SSE protocol disconnect" in payload["warnings"][0]["detail"]
    assert raw.fetched_job_ids == [101]
    assert raw.closed is True


def test_proxbox_sync_stream_eof_without_complete_uses_authoritative_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = _install_fake_proxbox(
        monkeypatch,
        frames=[],
        job={"status": "completed", "error": "", "data": {}, "log_entries": []},
    )

    result = runner.invoke(nbx_app, ["proxbox", "sync", "--json", "--confirm"])

    assert result.exit_code == 0
    payload = cli_json(result.stdout)
    assert payload["ok"] is True
    assert payload["errors"] == []
    assert "before the terminal complete frame" in payload["warnings"][0]["message"]
    assert raw.fetched_job_ids == [101]
    assert raw.closed is True


def test_proxbox_sync_stream_failure_polls_nonterminal_job_to_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(proxbox_mod, "_JOB_POLL_INTERVAL", 0.0)
    raw = _install_fake_proxbox(
        monkeypatch,
        frames=[],
        stream_error=TimeoutError("SSE stream timed out"),
        job=[
            {"status": "running", "error": "", "data": {}, "log_entries": []},
            {"status": "completed", "error": "", "data": {}, "log_entries": []},
        ],
    )

    result = runner.invoke(nbx_app, ["proxbox", "sync", "--json", "--confirm"])

    assert result.exit_code == 0
    payload = cli_json(result.stdout)
    assert payload["status"] == "completed"
    assert payload["ok"] is True
    assert payload["errors"] == []
    assert "SSE stream timed out" in payload["warnings"][0]["detail"]
    assert raw.fetched_job_ids == [101, 101]
    assert raw.closed is True


def test_proxbox_sync_stream_failure_with_authoritative_job_error_still_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = _install_fake_proxbox(
        monkeypatch,
        frames=[],
        stream_error=RuntimeError("SSE protocol disconnect"),
        job={"status": "errored", "error": "job failed", "data": {}, "log_entries": []},
    )

    result = runner.invoke(nbx_app, ["proxbox", "sync", "--json", "--confirm"])

    assert result.exit_code == 1
    payload = cli_json(result.stdout)
    assert payload["status"] == "errored"
    assert payload["ok"] is False
    assert any("job failed" in entry["detail"] for entry in payload["errors"])
    assert "SSE protocol disconnect" in payload["warnings"][0]["detail"]
    assert raw.fetched_job_ids == [101]
    assert raw.closed is True


@pytest.mark.parametrize("stream_fails", [False, True])
async def test_proxbox_sync_authoritative_fetch_failure_preserves_job_id(
    stream_fails: bool,
    capsys: pytest.CaptureFixture[str],
) -> None:
    raw = _RawClient()

    class _FetchFailingProxbox:
        async def schedule(
            self,
            sync_types: list[str],
            *,
            proxmox_endpoint_ids: list[int] | None = None,
            job_name: str | None = None,
        ) -> ScheduleResult:
            del sync_types, proxmox_endpoint_ids, job_name
            return ScheduleResult(ok=True, job_id=101, message="queued")

        async def stream_job(self, job_id: int, *, timeout: float | None = None):
            del job_id, timeout
            if stream_fails:
                raise RuntimeError("SSE protocol disconnect")
            yield SseFrame(
                event="complete",
                data={"ok": True, "message": "done", "status": "completed"},
            )

        async def fetch_job(self, job_id: int) -> dict[str, Any]:
            raise ConnectionError(f"job {job_id} fetch unavailable")

    with pytest.raises(ProxboxSyncError) as excinfo:
        await proxbox_mod._run_sync(
            raw_client=raw,
            proxbox=_FetchFailingProxbox(),  # type: ignore[arg-type]
            endpoint=None,
            sync_types=["all"],
            job_name=None,
            timeout=5.0,
            json_output=True,
        )

    assert excinfo.value.job_id == 101
    assert "inspect this existing job" in str(excinfo.value)
    assert raw.closed is True

    proxbox_mod._render_cli_exception(excinfo.value, json_output=True)
    payload = json.loads(capsys.readouterr().out)
    assert payload["job_id"] == 101
    assert payload["ok"] is False


def test_frame_to_line_styles_error_frames() -> None:
    line = proxbox_mod.frame_to_line(
        SseFrame(
            event="error_detail",
            data={"phase": "devices", "message": "device failed", "detail": "bad role"},
        )
    )

    assert "device failed" in line.plain
    assert "red" in str(line.style)
