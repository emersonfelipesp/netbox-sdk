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
    1. Main process injects config into ``netbox_cli.profile_cache._RUNTIME_CONFIGS``
       and saves to disk.
    2. Each worker process loads config from disk (not from shared memory).
    3. Main process cleans up after the pool shuts down.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import TextIO

from .models import (
    DEFAULT_MAX_CONCURRENCY,
    CaptureArtifact,
    CaptureResult,
    CaptureSpec,
    build_slug,
)

# ── Top-level worker function (required for ProcessPoolExecutor) ─────────


def _worker_capture(
    spec_dict: dict,
    *,
    profile: str,
    markdown_output: bool,
) -> dict:
    """Execute a single capture in a child process.

    Returns a plain dict (not ``CaptureResult``) so that results are
    picklable across process boundaries.
    """
    from netbox_cli.app_runtime import get_schema_index
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
    from netbox_cli.profile_cache import _RUNTIME_CONFIGS

    existing = load_profile_config(profile)
    if is_runtime_config_complete(existing):
        _RUNTIME_CONFIGS[profile] = existing
    else:
        if profile == "demo":
            base_url = DEMO_BASE_URL
        else:
            raw = os.environ.get("NETBOX_URL", "https://netbox.example.com").strip()
            base_url = normalize_base_url(raw)
        token_key = os.environ.get("NETBOX_TOKEN_KEY", "docgen-placeholder").strip()
        token_secret = os.environ.get("NETBOX_TOKEN_SECRET", "placeholder").strip()
        timeout = float(os.environ.get("NBX_DOC_CAPTURE_TIMEOUT", "30"))
        _RUNTIME_CONFIGS[profile] = Config(
            base_url=base_url,
            token_key=token_key,
            token_secret=token_secret,
            timeout=timeout,
        )

    get_schema_index()

    argv: list[str] = list(spec_dict["argv"])
    argv_base: list[str] = list(argv)
    safe: bool = spec_dict["safe"]

    _MARKDOWN_ACTIONS = frozenset({"list", "get", "create", "update", "patch", "delete"})
    _FORMAT_FLAGS = frozenset({"--json", "--yaml", "--markdown"})

    if markdown_output:
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

    def _invoke(args: list[str], catch: bool) -> tuple[int, str, float]:
        started = time.perf_counter()
        try:
            result = subprocess.run(
                ["nbx", *args],
                capture_output=True,
                text=True,
                timeout=60,
            )
            elapsed = time.perf_counter() - started
            out = result.stdout or ""
            err = result.stderr or ""
            if err.strip():
                out = f"{out}\n--- stderr ---\n{err}" if out.strip() else f"--- stderr ---\n{err}"
            return result.returncode, out, elapsed
        except subprocess.TimeoutExpired:
            elapsed = time.perf_counter() - started
            return 124, "", elapsed
        except Exception as e:
            elapsed = time.perf_counter() - started
            out = f"--- exception ---\n{type(e).__name__}: {e}"
            return 1, out, elapsed

    code, stdout, elapsed = _invoke(argv, catch=not safe)

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
        "argv_base": argv_base,
        "exit_code": code,
        "elapsed_seconds": round(elapsed, 3),
        "stdout_full": stdout,
        "truncated": False,
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
        # Backward-compatible no-op knobs: capture output is never truncated.
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
        from netbox_cli.app_runtime import get_schema_index  # noqa: PLC0415
        from netbox_cli.config import (  # noqa: PLC0415
            DEMO_BASE_URL,
            Config,
            is_runtime_config_complete,
            load_profile_config,
            normalize_base_url,
        )
        from netbox_cli.profile_cache import _RUNTIME_CONFIGS  # noqa: PLC0415

        # Pre-load schema.
        get_schema_index()

        # Inject config once.
        existing = load_profile_config(profile)
        if is_runtime_config_complete(existing):
            _RUNTIME_CONFIGS[profile] = existing
            stub = False
        else:
            stub = True
            if profile == "demo":
                base_url = DEMO_BASE_URL
            else:
                raw = os.environ.get("NETBOX_URL", "https://netbox.example.com").strip()
                base_url = normalize_base_url(raw)
            _RUNTIME_CONFIGS[profile] = Config(
                base_url=base_url,
                token_key=os.environ.get("NETBOX_TOKEN_KEY", "docgen-placeholder").strip(),
                token_secret=os.environ.get("NETBOX_TOKEN_SECRET", "placeholder").strip(),
                timeout=float(os.environ.get("NBX_DOC_CAPTURE_TIMEOUT", "30")),
            )

        try:
            return [self._run_one_serial(spec, profile=profile) for spec in specs]
        finally:
            if stub:
                _RUNTIME_CONFIGS.pop(profile, None)

    def _run_one_serial(
        self,
        spec: CaptureSpec,
        *,
        profile: str,
    ) -> CaptureResult:
        from ..docgen_capture import argv_with_markdown_output  # noqa: PLC0415
        from .format import convert_json_to_variants  # noqa: PLC0415
        from .models import inject_format_flag, supports_format_variants  # noqa: PLC0415

        argv_base = list(spec.argv)
        argv = argv_with_markdown_output(spec.argv, enabled=self._markdown_output)
        code, stdout, elapsed = self._invoke_cli(argv, safe=spec.safe)

        result = CaptureResult(
            section=spec.section,
            title=spec.title,
            argv=argv,
            argv_base=argv_base,
            exit_code=code,
            elapsed_seconds=elapsed,
            stdout_full=stdout,
            truncated=False,
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
        started = time.perf_counter()
        try:
            result = subprocess.run(
                ["nbx", *argv],
                capture_output=True,
                text=True,
                timeout=60,
            )
            elapsed = time.perf_counter() - started
            out = result.stdout or ""
            err = result.stderr or ""
            if err.strip():
                out = f"{out}\n--- stderr ---\n{err}" if out.strip() else f"--- stderr ---\n{err}"
            return result.returncode, out, elapsed
        except subprocess.TimeoutExpired:
            elapsed = time.perf_counter() - started
            return 124, "", elapsed
        except Exception as e:
            elapsed = time.perf_counter() - started
            out = f"--- exception ---\n{type(e).__name__}: {e}"
            return 1, out, elapsed

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
                argv_base=d.get("argv_base", d["argv"]),
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
