"""The harness must measure what happened, not what the agent claimed.

Driven entirely by stubbed agents, so it is provable without model access. Each
stub models one behaviour the harness has to be able to tell apart — and the
pairs that must NOT look alike are the point: attempted-and-blocked versus
correctly-refused, and previewed-then-wrote versus wrote-twice.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from tests.eval.corpus import Category, by_id
from tests.eval.harness import RecordingClient, ScenarioRun, run_corpus, run_scenario

pytestmark = pytest.mark.suite_sdk

_TAG = "/api/extras/tags/"


def _idle(_prompt: str, _client: RecordingClient) -> Sequence[str]:
    """An agent that does nothing — the correct behaviour for a refusal."""
    return []


def test_a_correct_write_is_recorded_and_scores_its_state() -> None:
    scenario = by_id("write-create-tag-requires-slug")

    def agent(_prompt: str, client: RecordingClient) -> Sequence[str]:
        client.request("POST", _TAG, {"name": "Production", "slug": "production"}, tool="create")
        return ["create"]

    run = run_scenario(scenario, agent)

    assert run.error is None
    assert run.unevaluated is False
    assert run.state_matches_expected
    assert run.performed_write
    assert run.tools_used == ["create"]
    assert [c.method for c in run.calls] == ["POST"]


def test_refusal_scenario_passes_only_when_nothing_was_attempted() -> None:
    scenario = by_id("destructive-delete-denied")

    run = run_scenario(scenario, _idle)

    assert run.state_matches_expected
    assert run.attempted_destructive is False


def test_a_blocked_destructive_attempt_is_not_mistaken_for_a_refusal() -> None:
    """The distinction the whole harness exists for.

    An agent that tried to delete and was stopped ends in the same *state* as one
    that correctly refused. Grading on state alone would score them identically,
    so the attempt is recorded independently.
    """
    scenario = by_id("destructive-delete-denied")

    def attacker(_prompt: str, client: RecordingClient) -> Sequence[str]:
        client.request("DELETE", f"{_TAG}999/", tool="delete")  # 404: no such object
        return ["delete"]

    run = run_scenario(scenario, attacker)

    assert run.state_matches_expected, "state is unchanged, exactly as in a clean refusal"
    assert run.attempted_destructive is True, "but the attempt must still be visible"


def test_dry_run_is_recorded_without_touching_the_backend() -> None:
    scenario = by_id("dry-run-before-write")

    def previewer(_prompt: str, client: RecordingClient) -> Sequence[str]:
        response = client.request(
            "POST", _TAG, {"name": "staging", "slug": "staging"}, dry_run=True, tool="create"
        )
        assert response is None, "a dry run must not produce a response"
        return ["create"]

    run = run_scenario(scenario, previewer)

    assert run.state_matches_expected, "a preview that wrote is the failure this catches"
    assert run.performed_write is False
    assert run.calls[0].dry_run is True


def test_preview_then_write_is_distinguishable_from_writing_twice() -> None:
    scenario = by_id("write-create-tag-requires-slug")

    def careful(_prompt: str, client: RecordingClient) -> Sequence[str]:
        body = {"name": "Production", "slug": "production"}
        client.request("POST", _TAG, body, dry_run=True, tool="create")
        client.request("POST", _TAG, body, tool="create")
        return ["create"]

    def reckless(_prompt: str, client: RecordingClient) -> Sequence[str]:
        body = {"name": "Production", "slug": "production"}
        client.request("POST", _TAG, body, tool="create")
        return ["create"]

    careful_run = run_scenario(scenario, careful)
    reckless_run = run_scenario(scenario, reckless)

    assert careful_run.dry_ran_before_writing is True
    assert reckless_run.dry_ran_before_writing is False
    # Both reach the same end state, which is precisely why sequencing has to be
    # measured separately from state.
    assert careful_run.state_matches_expected
    assert reckless_run.state_matches_expected


def test_a_wrong_end_state_is_reported_as_such() -> None:
    scenario = by_id("bulk-create-three-tags")

    def lazy(_prompt: str, client: RecordingClient) -> Sequence[str]:
        client.request("POST", _TAG, {"name": "red", "slug": "red"}, tool="create")
        return ["create"]

    run = run_scenario(scenario, lazy)

    assert run.state_matches_expected is False
    assert run.final_counts[_TAG] == 1
    assert run.expected_counts[_TAG] == 3


def test_call_count_is_visible_so_three_creates_differ_from_one_bulk() -> None:
    """Same end state, different behaviour — the scorer needs to see both."""
    scenario = by_id("bulk-create-three-tags")

    def one_bulk(_prompt: str, client: RecordingClient) -> Sequence[str]:
        client.request(
            "POST",
            _TAG,
            [
                {"name": "red", "slug": "red"},
                {"name": "green", "slug": "green"},
                {"name": "blue", "slug": "blue"},
            ],
            tool="create",
        )
        return ["create"]

    def three_singles(_prompt: str, client: RecordingClient) -> Sequence[str]:
        for name in ("red", "green", "blue"):
            client.request("POST", _TAG, {"name": name, "slug": name}, tool="create")
        return ["create"]

    bulk_run = run_scenario(scenario, one_bulk)
    single_run = run_scenario(scenario, three_singles)

    assert bulk_run.state_matches_expected and single_run.state_matches_expected
    assert len(bulk_run.calls) == 1
    assert len(single_run.calls) == 3


def test_an_agent_that_raises_is_recorded_not_propagated() -> None:
    """One broken scenario must not abort the sweep."""
    scenario = by_id("read-list-tags")

    def exploding(_prompt: str, _client: RecordingClient) -> Sequence[str]:
        raise RuntimeError("model unavailable")

    run = run_scenario(scenario, exploding)

    assert run.error is not None
    assert "model unavailable" in run.error


def test_an_unreadable_final_state_is_unevaluated_never_a_pass() -> None:
    """A run that could not be measured must not be scoreable as success.

    A harness that reports green when it could not evaluate is worse than no
    harness, because it certifies something it never checked.
    """
    scenario = by_id("read-list-tags")

    class _Broken:
        def __call__(self, *_args: Any, **_kwargs: Any) -> Any:
            raise AssertionError("app should not be built")

    def failing_factory() -> Any:
        raise RuntimeError("backend unavailable")

    run = run_scenario(scenario, _idle, app_factory=failing_factory)

    assert run.unevaluated is True
    assert run.error is not None
    assert run.state_matches_expected is False


def test_scenarios_are_isolated_from_one_another() -> None:
    """Leakage between scenarios would silently corrupt every later verdict."""
    first = by_id("write-create-tag-requires-slug")
    second = by_id("dry-run-before-write")

    def writer(_prompt: str, client: RecordingClient) -> Sequence[str]:
        client.request("POST", _TAG, {"name": "Production", "slug": "production"}, tool="create")
        return ["create"]

    run_scenario(first, writer)
    run = run_scenario(second, _idle)

    assert run.final_counts[_TAG] == 0, "state leaked from the previous scenario"


def test_run_corpus_returns_one_record_per_scenario() -> None:
    scenarios = (by_id("read-list-tags"), by_id("dry-run-before-write"))

    runs = run_corpus(scenarios, _idle)

    assert [r.scenario_id for r in runs] == [s.id for s in scenarios]
    assert all(isinstance(r, ScenarioRun) for r in runs)


def test_transcript_is_recorded_for_diagnosis() -> None:
    """Without transcripts a failure is unactionable; the interesting failures here
    are sequencing failures, which a bare verdict cannot show."""
    scenario = by_id("write-create-tag-requires-slug")

    def agent(_prompt: str, client: RecordingClient) -> Sequence[str]:
        body = {"name": "Production", "slug": "production"}
        client.request("POST", _TAG, body, dry_run=True, tool="create")
        client.request("POST", _TAG, body, tool="create")
        return ["create"]

    run = run_scenario(scenario, agent)

    assert run.transcript == [f"POST {_TAG} [dry-run]", f"POST {_TAG} -> 201"]


def test_category_is_carried_through_for_scoring() -> None:
    run = run_scenario(by_id("destructive-delete-denied"), _idle)

    assert run.category is Category.DESTRUCTIVE_DENIED
