"""Capture engine — parallel CLI invocation with config management.

Single Responsibility: orchestrates CLI captures (serial or parallel).
Dependency Inversion: depends on model protocols, not concrete Pydantic classes.

Parallelism strategy:
    Uses ``ProcessPoolExecutor`` for true process isolation.  Each worker
    process gets its own Python interpreter and ``sys.stdout``/``sys.stderr``
    so that ``CliRunner``'s stream manipulation does not cause cross-thread
    interference.

    Concurrency is bounded by ``max_concurrency`` (default 4) to avoid
    overwhelming the NetBox demo instance.

Config lifecycle:
    1. Main process injects config into ``_RUNTIME_CONFIGS`` and saves to disk.
    2. Each worker process loads config from disk (not from shared memory).
    3. Main process cleans up after the pool shuts down.
"""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from inspect import signature
from pathlib import Path
from typing import TextIO

from .models import (
    DEFAULT_MAX_CONCURRENCY,
    CaptureArtifact,
    CaptureResult,
    CaptureSpec,
    build_slug,
    truncate,
)

# ── Top-level worker function (required for ProcessPoolExecutor) ─────────


def _worker_capture(
    spec_dict: dict,
    *,
    profile: str,
    max_lines: int,
    max_chars: int,
    markdown_output: bool,
) -> dict:
    """Execute a single capture in a child process.

    Returns a plain dict (not ``CaptureResult``) so that results are
    picklable across process boundaries.
    """
    # Lazy imports — each process loads its own modules.
    from typer.testing import CliRunner

    from netbox_cli import cli as cli_mod
    from netbox_cli.cli import runtime as _rt
    from netbox_cli.config import (
        DEMO_BASE_URL,
        Config,
        is_runtime_config_complete,
        load_profile_config,
        normalize_base_url,
    )
    from netbox_cli.docgen.format import convert_json_to_variants
    from netbox_cli.docgen.models import (
        inject_format_flag,
        supports_format_variants,
    )

    # ── Ensure config is available in this process ────────────────────────
    existing = load_profile_config(profile)
    if is_runtime_config_complete(existing):
        cli_mod._RUNTIME_CONFIGS[profile] = existing
    else:
        if profile == "demo":
            base_url = DEMO_BASE_URL
        else:
            raw = os.environ.get("NETBOX_URL", "https://netbox.example.com").strip()
            base_url = normalize_base_url(raw)
        token_key = os.environ.get("NETBOX_TOKEN_KEY", "docgen-placeholder").strip()
        token_secret = os.environ.get("NETBOX_TOKEN_SECRET", "placeholder").strip()
        timeout = float(os.environ.get("NBX_DOC_CAPTURE_TIMEOUT", "30"))
        cli_mod._RUNTIME_CONFIGS[profile] = Config(
            base_url=base_url,
            token_key=token_key,
            token_secret=token_secret,
            timeout=timeout,
        )

    # Pre-load schema index so lazy init doesn't race.
    _rt._get_index()

    # ── Build spec from dict ──────────────────────────────────────────────
    argv: list[str] = spec_dict["argv"]
    safe: bool = spec_dict["safe"]

    # ── Apply --markdown flag ─────────────────────────────────────────────
    if markdown_output:
        _MARKDOWN_ACTIONS = frozenset({"list", "get", "create", "update", "patch", "delete"})
        _FORMAT_FLAGS = frozenset({"--json", "--yaml", "--markdown"})

        if "--help" not in argv and not any(f in argv for f in _FORMAT_FLAGS):
            opt_idx = next((i for i, t in enumerate(argv) if t.startswith("-")), len(argv))
            pos = argv[:opt_idx]
            if pos:
                if pos[0] == "call" and len(pos) >= 3:
                    argv = [*argv, "--markdown"]
                else:
                    body = pos[1:] if pos[0] == "demo" else pos
                    if len(body) >= 3 and body[-1] in _MARKDOWN_ACTIONS:
                        argv = [*argv, "--markdown"]

    # ── Run CLI ───────────────────────────────────────────────────────────
    def _invoke(args: list[str], catch: bool) -> tuple[int, str, float]:
        if "mix_stderr" in signature(CliRunner).parameters:
            runner = CliRunner(mix_stderr=False)
        else:
            runner = CliRunner()
        started = time.perf_counter()
        result = runner.invoke(cli_mod.app, args, catch_exceptions=catch, color=False)
        elapsed = time.perf_counter() - started
        out = result.stdout or ""
        err = getattr(result, "stderr", "") or ""
        if err.strip():
            out = f"{out}\n--- stderr ---\n{err}" if out.strip() else f"--- stderr ---\n{err}"
        if result.exception is not None and not isinstance(result.exception, SystemExit):
            import traceback

            tb = "".join(
                traceback.format_exception(
                    type(result.exception),
                    result.exception,
                    result.exception.__traceback__,
                )
            )
            out = f"{out}\n--- exception ---\n{tb}" if out.strip() else f"--- exception ---\n{tb}"
        return result.exit_code or 0, out, elapsed

    code, stdout, elapsed = _invoke(argv, catch=not safe)

    # Truncate.
    if len(stdout) > max_chars:
        stdout_trunc = stdout[:max_chars] + "\n\n\u2026 (truncated by character limit)\n"
        did_truncate = True
    else:
        lines = stdout.splitlines()
        if len(lines) > max_lines:
            stdout_trunc = (
                "\n".join(lines[:max_lines])
                + f"\n\n\u2026 ({len(lines) - max_lines} more lines truncated)\n"
            )
            did_truncate = True
        else:
            stdout_trunc = stdout
            did_truncate = False

    # ── Format variants ───────────────────────────────────────────────────
    stdout_json = None
    stdout_yaml = None
    stdout_markdown = None

    if supports_format_variants(spec_dict["argv"]):
        json_argv = inject_format_flag(argv, "--json")
        _, json_stdout, _ = _invoke(json_argv, catch=True)
        variants = convert_json_to_variants(json_stdout)
        if variants is not None:
            stdout_json = variants.json_text
            stdout_yaml = variants.yaml_text
            stdout_markdown = variants.markdown_text

    return {
        "section": spec_dict["section"],
        "title": spec_dict["title"],
        "argv": argv,
        "exit_code": code,
        "elapsed_seconds": round(elapsed, 3),
        "stdout_full": stdout_trunc,
        "truncated": did_truncate,
        "stdout_json": stdout_json,
        "stdout_yaml": stdout_yaml,
        "stdout_markdown": stdout_markdown,
    }


# ── Engine class ─────────────────────────────────────────────────────────────


class CaptureEngine:
    """Executes CLI captures in parallel (process isolation) or serial.

    Usage::

        engine = CaptureEngine(max_concurrency=4)
        results = engine.capture_all(specs, profile="demo")
        engine.write_artifacts(results, raw_dir)
    """

    def __init__(
        self,
        *,
        max_concurrency: int = DEFAULT_MAX_CONCURRENCY,
        max_lines: int = 200,
        max_chars: int = 120_000,
        markdown_output: bool = True,
        log: TextIO | None = None,
    ) -> None:
        self._concurrency = max(1, max_concurrency)
        self._max_lines = max_lines
        self._max_chars = max_chars
        self._markdown_output = markdown_output
        self._log = log or sys.stderr

    # ── Public API ────────────────────────────────────────────────────────

    def capture_all(
        self,
        specs: list[CaptureSpec],
        *,
        profile: str,
    ) -> list[CaptureResult]:
        """Capture every spec, returning results in spec order.

        When *max_concurrency* > 1, specs are dispatched to a process pool
        for true parallelism.  Each worker is an isolated Python process
        with its own ``sys.stdout`` and ``CliRunner``.
        """
        if self._concurrency <= 1 or len(specs) <= 1:
            return self._capture_serial(specs, profile=profile)
        return self._capture_parallel(specs, profile=profile)

    def write_artifacts(
        self,
        results: list[CaptureResult],
        raw_dir: Path,
    ) -> list[CaptureArtifact]:
        """Write one JSON artifact per result.  Returns the artifact list."""
        raw_dir.mkdir(parents=True, exist_ok=True)
        artifacts: list[CaptureArtifact] = []
        for result in results:
            slug = build_slug(result.section, result.title)
            filename = f"{len(artifacts) + 1:03d}-{slug}.json"
            artifact = CaptureArtifact(result=result, filename=filename)
            (raw_dir / filename).write_text(
                json.dumps(result.to_dict(), indent=2),
                encoding="utf-8",
            )
            artifacts.append(artifact)
        return artifacts

    # ── Serial execution ──────────────────────────────────────────────────

    def _capture_serial(
        self,
        specs: list[CaptureSpec],
        *,
        profile: str,
    ) -> list[CaptureResult]:
        from netbox_cli import cli as cli_mod  # noqa: PLC0415
        from netbox_cli.cli import runtime as _rt  # noqa: PLC0415
        from netbox_cli.config import (  # noqa: PLC0415
            DEMO_BASE_URL,
            Config,
            is_runtime_config_complete,
            load_profile_config,
            normalize_base_url,
        )

        # Pre-load schema.
        _rt._get_index()

        # Inject config once.
        existing = load_profile_config(profile)
        if is_runtime_config_complete(existing):
            cli_mod._RUNTIME_CONFIGS[profile] = existing
            stub = False
        else:
            stub = True
            if profile == "demo":
                base_url = DEMO_BASE_URL
            else:
                raw = os.environ.get("NETBOX_URL", "https://netbox.example.com").strip()
                base_url = normalize_base_url(raw)
            cli_mod._RUNTIME_CONFIGS[profile] = Config(
                base_url=base_url,
                token_key=os.environ.get("NETBOX_TOKEN_KEY", "docgen-placeholder").strip(),
                token_secret=os.environ.get("NETBOX_TOKEN_SECRET", "placeholder").strip(),
                timeout=float(os.environ.get("NBX_DOC_CAPTURE_TIMEOUT", "30")),
            )

        try:
            return [self._run_one_serial(spec, profile=profile) for spec in specs]
        finally:
            if stub:
                cli_mod._RUNTIME_CONFIGS.pop(profile, None)

    def _run_one_serial(
        self,
        spec: CaptureSpec,
        *,
        profile: str,
    ) -> CaptureResult:
        from ..docgen_capture import argv_with_markdown_output  # noqa: PLC0415
        from .format import convert_json_to_variants  # noqa: PLC0415
        from .models import inject_format_flag, supports_format_variants  # noqa: PLC0415

        argv = argv_with_markdown_output(spec.argv, enabled=self._markdown_output)
        code, stdout, elapsed = self._invoke_cli(argv, safe=spec.safe)
        stdout_trunc, did_truncate = truncate(stdout, self._max_lines, self._max_chars)

        result = CaptureResult(
            section=spec.section,
            title=spec.title,
            argv=argv,
            exit_code=code,
            elapsed_seconds=elapsed,
            stdout_full=stdout_trunc,
            truncated=did_truncate,
        )

        if supports_format_variants(spec.argv):
            json_argv = inject_format_flag(argv, "--json")
            _, json_stdout, _ = self._invoke_cli(json_argv, safe=True)
            variants = convert_json_to_variants(json_stdout)
            if variants is not None:
                result.stdout_json = variants.json_text
                result.stdout_yaml = variants.yaml_text
                result.stdout_markdown = variants.markdown_text

        return result

    def _invoke_cli(self, argv: list[str], *, safe: bool) -> tuple[int, str, float]:
        from typer.testing import CliRunner  # noqa: PLC0415

        if "mix_stderr" in signature(CliRunner).parameters:
            runner = CliRunner(mix_stderr=False)
        else:
            runner = CliRunner()
        from netbox_cli.cli import app as cli_app  # noqa: PLC0415

        started = time.perf_counter()
        result = runner.invoke(cli_app, argv, catch_exceptions=not safe, color=False)
        elapsed = time.perf_counter() - started
        out = result.stdout or ""
        err = getattr(result, "stderr", "") or ""
        if err.strip():
            out = f"{out}\n--- stderr ---\n{err}" if out.strip() else f"--- stderr ---\n{err}"
        if result.exception is not None and not isinstance(result.exception, SystemExit):
            import traceback

            tb = "".join(
                traceback.format_exception(
                    type(result.exception),
                    result.exception,
                    result.exception.__traceback__,
                )
            )
            out = f"{out}\n--- exception ---\n{tb}" if out.strip() else f"--- exception ---\n{tb}"
        return result.exit_code or 0, out, elapsed

    # ── Parallel execution (ProcessPoolExecutor) ──────────────────────────

    def _capture_parallel(
        self,
        specs: list[CaptureSpec],
        *,
        profile: str,
    ) -> list[CaptureResult]:
        """Run captures across isolated worker processes."""
        # Ensure config is saved to disk so workers can load it.
        self._ensure_config_on_disk(profile)

        spec_dicts = [
            {"section": s.section, "title": s.title, "argv": list(s.argv), "safe": s.safe}
            for s in specs
        ]
        results_raw: dict[int, dict] = {}

        with ProcessPoolExecutor(max_workers=self._concurrency) as pool:
            futures = {
                pool.submit(
                    _worker_capture,
                    spec_dict,
                    profile=profile,
                    max_lines=self._max_lines,
                    max_chars=self._max_chars,
                    markdown_output=self._markdown_output,
                ): idx
                for idx, spec_dict in enumerate(spec_dicts)
            }
            for future in as_completed(futures):
                idx = futures[future]
                results_raw[idx] = future.result()

        return [
            CaptureResult(
                section=d["section"],
                title=d["title"],
                argv=d["argv"],
                exit_code=d["exit_code"],
                elapsed_seconds=d["elapsed_seconds"],
                stdout_full=d["stdout_full"],
                truncated=d["truncated"],
                stdout_json=d.get("stdout_json"),
                stdout_yaml=d.get("stdout_yaml"),
                stdout_markdown=d.get("stdout_markdown"),
            )
            for d in (results_raw[i] for i in range(len(specs)))
        ]

    @staticmethod
    def _ensure_config_on_disk(profile: str) -> None:
        """Ensure the profile config exists on disk so child processes can load it."""
        from netbox_cli.config import (  # noqa: PLC0415
            DEMO_BASE_URL,
            Config,
            is_runtime_config_complete,
            load_profile_config,
            normalize_base_url,
            save_profile_config,
        )

        existing = load_profile_config(profile)
        if is_runtime_config_complete(existing):
            return

        if profile == "demo":
            base_url = DEMO_BASE_URL
        else:
            raw = os.environ.get("NETBOX_URL", "https://netbox.example.com").strip()
            base_url = normalize_base_url(raw)

        stub_cfg = Config(
            base_url=base_url,
            token_key=os.environ.get("NETBOX_TOKEN_KEY", "docgen-placeholder").strip(),
            token_secret=os.environ.get("NETBOX_TOKEN_SECRET", "placeholder").strip(),
            timeout=float(os.environ.get("NBX_DOC_CAPTURE_TIMEOUT", "30")),
        )
        save_profile_config(profile, stub_cfg)
