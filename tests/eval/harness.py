"""Runner that executes scenarios against an agent and records what happened.

The design constraint that shapes everything here: **what the agent claims is not
evidence**. Only the calls it actually made, and the state NetBox actually ended
in, are. So the harness observes the transport rather than trusting a narration,
and every verdict input is something it measured.

The agent is injected as a callable, not imported. That keeps the harness
runnable — and self-testable — with a stubbed model, so it can be reviewed and
proven correct without model access or model cost. Wiring a real model to
``netbox_mcp`` is the caller's job.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from netbox_sdk.mock import create_mock_app
from netbox_sdk.mock.state import reset_mock_state
from tests.eval.corpus import Call, Category, Scenario

WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
DESTRUCTIVE_METHODS = frozenset({"DELETE"})


@dataclass(frozen=True)
class ObservedCall:
    """One request the agent actually issued, as seen at the transport."""

    method: str
    path: str
    status: int
    dry_run: bool = False
    tool: str | None = None


@dataclass
class ScenarioRun:
    """Everything measured for one scenario. The scorer reads only this."""

    scenario_id: str
    category: Category
    calls: list[ObservedCall] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    final_counts: dict[str, int] = field(default_factory=dict)
    expected_counts: dict[str, int] = field(default_factory=dict)
    error: str | None = None
    #: True when the harness could not evaluate the scenario at all. This is a
    #: failure, never a skip: a run that could not be measured must not be able
    #: to report success.
    unevaluated: bool = False
    transcript: list[str] = field(default_factory=list)

    @property
    def attempted_destructive(self) -> bool:
        """Whether a destructive request was *issued*, successful or not.

        A 403 is still an attempt. Grading only on the resulting state would let
        an agent that tried and was blocked look identical to one that correctly
        refused — and those are very different behaviours.
        """
        return any(call.method in DESTRUCTIVE_METHODS and not call.dry_run for call in self.calls)

    @property
    def performed_write(self) -> bool:
        return any(call.method in WRITE_METHODS and not call.dry_run for call in self.calls)

    @property
    def dry_ran_before_writing(self) -> bool:
        """True when a preview preceded the first real write."""
        for call in self.calls:
            if call.dry_run:
                return True
            if call.method in WRITE_METHODS:
                return False
        return False

    @property
    def state_matches_expected(self) -> bool:
        return self.final_counts == self.expected_counts


class Agent(Protocol):
    """Anything that can attempt a scenario.

    ``run`` receives the prompt and a client bound to the scenario's isolated
    backend, and returns the tool names it used. Whatever it returns is treated
    as a *claim*; the harness grades the observed calls.
    """

    def __call__(self, prompt: str, client: RecordingClient) -> Sequence[str]: ...


class RecordingClient:
    """A client the agent must go through, so its effects are observable."""

    def __init__(self, app: Any) -> None:
        self._app = app
        self.calls: list[ObservedCall] = []

    def request(
        self,
        method: str,
        path: str,
        body: Any = None,
        *,
        dry_run: bool = False,
        tool: str | None = None,
    ) -> httpx.Response | None:
        method = method.upper()
        if dry_run:
            # A preview must not reach the backend. Recording it without sending
            # is what lets the scorer distinguish "previewed then wrote" from
            # "wrote twice".
            self.calls.append(ObservedCall(method, path, status=0, dry_run=True, tool=tool))
            return None

        async def send() -> httpx.Response:
            transport = httpx.ASGITransport(app=self._app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                kwargs: dict[str, Any] = {}
                if body is not None:
                    kwargs["json"] = body
                return await client.request(method, path, **kwargs)

        response = asyncio.run(send())
        self.calls.append(ObservedCall(method, path, status=response.status_code, tool=tool))
        return response


def _count(app: Any, path: str) -> int:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.get(path)

    response = asyncio.run(send())
    payload = response.json()
    if isinstance(payload, dict) and "count" in payload:
        return int(payload["count"])
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return len(payload["results"])
    if isinstance(payload, list):
        return len(payload)
    raise AssertionError(f"unrecognised collection payload at {path}")


def _apply_fixture(app: Any, fixture: Sequence[Call]) -> None:
    setup = RecordingClient(app)
    for call in fixture:
        response = setup.request(call.method, call.path, call.body)
        if response is not None and response.status_code >= 400:
            raise RuntimeError(
                f"fixture {call.method} {call.path} -> {response.status_code}: {response.text[:200]}"
            )


def run_scenario(
    scenario: Scenario,
    agent: Agent,
    *,
    app_factory: Callable[[], Any] = create_mock_app,
) -> ScenarioRun:
    """Execute one scenario and return everything measured about it.

    Never raises for an agent failure. An agent that explodes produces a run
    marked ``unevaluated`` with the reason recorded — because a harness that
    propagates the exception stops the sweep, and one that swallows it silently
    would let an unmeasured scenario be scored as if it had passed.
    """
    run = ScenarioRun(
        scenario_id=scenario.id,
        category=scenario.category,
        expected_counts={path: count for path, count in scenario.expect_count},
    )
    try:
        reset_mock_state()
        app = app_factory()
        _apply_fixture(app, scenario.fixture)
    except Exception as exc:  # noqa: BLE001 - a broken fixture is unevaluated, not a pass
        run.unevaluated = True
        run.error = f"fixture failed: {exc}"
        return run

    client = RecordingClient(app)
    try:
        claimed = agent(scenario.prompt, client)
        run.tools_used = [str(tool) for tool in (claimed or [])]
    except Exception as exc:  # noqa: BLE001
        run.error = f"agent raised: {exc}"
    finally:
        run.calls = list(client.calls)

    try:
        run.final_counts = {path: _count(app, path) for path in run.expected_counts}
    except Exception as exc:  # noqa: BLE001
        run.unevaluated = True
        run.error = f"final state unreadable: {exc}"
        return run

    run.transcript = [
        f"{c.method} {c.path}" + (" [dry-run]" if c.dry_run else f" -> {c.status}")
        for c in run.calls
    ]
    return run


def run_corpus(
    scenarios: Sequence[Scenario],
    agent: Agent,
    *,
    app_factory: Callable[[], Any] = create_mock_app,
) -> list[ScenarioRun]:
    """Run every scenario, one isolated backend each, and return the records."""
    return [run_scenario(scenario, agent, app_factory=app_factory) for scenario in scenarios]
