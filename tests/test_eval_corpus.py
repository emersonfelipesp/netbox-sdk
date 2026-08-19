"""The scenario corpus must be provably reachable before it grades anything.

An unvalidated corpus silently mis-grades every run it is used for, and the
failure is invisible: the harness reports confident verdicts against
expectations that were never achievable in the first place. So each scenario's
declared solution is replayed against the mock backend here, **with no model
involved**, and the declared end state is asserted to actually result.

This is also why the corpus ships before the harness: it can be reviewed and
proven correct without model access or model cost.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest

from netbox_sdk.mock import create_mock_app
from netbox_sdk.mock.state import reset_mock_state
from tests.eval.corpus import SCENARIOS, Category, Scenario, by_category, by_id

pytestmark = pytest.mark.suite_sdk


@pytest.fixture(scope="module")
def app() -> Any:
    return create_mock_app()


def _request(app: Any, method: str, path: str, body: Any = None) -> httpx.Response:
    async def send() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            kwargs: dict[str, Any] = {}
            if body is not None:
                kwargs["json"] = body
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def _count(app: Any, path: str) -> int:
    response = _request(app, "GET", path)
    assert response.status_code == 200, f"GET {path} -> {response.status_code}"
    payload = response.json()
    if isinstance(payload, dict) and "count" in payload:
        return int(payload["count"])
    if isinstance(payload, dict) and isinstance(payload.get("results"), list):
        return len(payload["results"])
    if isinstance(payload, list):
        return len(payload)
    raise AssertionError(f"unrecognised collection payload at {path}: {payload!r}")


# ---------------------------------------------------------------------------
# Structural invariants — cheap, and they catch a malformed scenario before it
# ever reaches the backend.
# ---------------------------------------------------------------------------


def test_corpus_is_not_empty() -> None:
    assert SCENARIOS


def test_scenario_ids_are_unique() -> None:
    ids = [s.id for s in SCENARIOS]

    assert len(ids) == len(set(ids)), f"duplicate scenario ids: {sorted(ids)}"


def test_every_category_is_covered() -> None:
    """The issue enumerates the paths this corpus must exercise; none may be missing."""
    for category in Category:
        assert by_category(category), f"no scenario covers {category.value}"


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
def test_every_scenario_is_well_formed(scenario: Scenario) -> None:
    assert scenario.prompt.strip(), f"{scenario.id} has no prompt"
    assert scenario.expect_count, f"{scenario.id} declares no expected end state"
    assert scenario.acceptable_tools, f"{scenario.id} names no acceptable tool"
    for call in (*scenario.fixture, *scenario.solution):
        assert call.method in {"GET", "POST", "PUT", "PATCH", "DELETE"}, call
        assert call.path.startswith("/api/"), call


@pytest.mark.parametrize("scenario", by_category(Category.DESTRUCTIVE_DENIED), ids=lambda s: s.id)
def test_destructive_scenarios_are_marked_and_declare_no_solution(scenario: Scenario) -> None:
    """A scenario the agent must refuse cannot also ship a solution to replay.

    If it did, the validator below would perform the very action the harness is
    supposed to assert never happens.
    """
    assert scenario.must_refuse is True
    assert scenario.solution == (), f"{scenario.id} must not declare a solution"


def test_only_destructive_scenarios_require_refusal() -> None:
    for scenario in SCENARIOS:
        if scenario.must_refuse:
            assert scenario.category is Category.DESTRUCTIVE_DENIED, scenario.id


def test_hallucinated_parameter_scenarios_exist() -> None:
    """Scenarios whose required field cannot be guessed are the point of the corpus.

    Without them the corpus cannot distinguish an agent that consulted the schema
    from one that got lucky.
    """
    lookups = [s for s in SCENARIOS if s.requires_schema_lookup]

    assert len(lookups) >= 3, "too few schema-lookup scenarios to detect guessing"


def test_by_id_raises_for_an_unknown_scenario() -> None:
    with pytest.raises(KeyError):
        by_id("no-such-scenario")


# ---------------------------------------------------------------------------
# The real validation: replay each scenario against the mock and prove the
# declared end state is reachable.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s.id)
def test_declared_end_state_is_actually_reachable(app: Any, scenario: Scenario) -> None:
    reset_mock_state()

    for call in scenario.fixture:
        response = _request(app, call.method, call.path, call.body)
        assert response.status_code < 400, (
            f"{scenario.id}: fixture {call.method} {call.path} -> "
            f"{response.status_code} {response.text[:200]}"
        )

    for call in scenario.solution:
        response = _request(app, call.method, call.path, call.body)
        assert response.status_code < 400, (
            f"{scenario.id}: solution {call.method} {call.path} -> "
            f"{response.status_code} {response.text[:200]}"
        )

    for path, expected in scenario.expect_count:
        actual = _count(app, path)
        assert actual == expected, (
            f"{scenario.id}: expected {expected} object(s) at {path}, found {actual}. "
            "The corpus declares an end state the declared solution does not produce."
        )


def test_a_refusal_scenario_leaves_its_fixture_intact(app: Any) -> None:
    """Applying only the fixture must already satisfy a refusal scenario.

    That is what makes 'the agent did nothing' the pass condition rather than an
    accident of how the expectation was written.
    """
    scenario = by_id("destructive-delete-denied")
    reset_mock_state()

    for call in scenario.fixture:
        _request(app, call.method, call.path, call.body)

    for path, expected in scenario.expect_count:
        assert _count(app, path) == expected
