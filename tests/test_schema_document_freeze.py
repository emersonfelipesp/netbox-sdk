"""The process-cached OpenAPI document must not be corruptible by one consumer.

``bundled_index()`` caches one parsed document per release line and hands every
caller a ``clone()`` over that *same* document. Copying it per call was never an
option — the bundled documents are 7.7-9.6 MB — so the document is frozen
instead, and a mutation fails at the line that attempted it rather than
silently degrading every later SDK, CLI, TUI and MCP consumer in the process.
"""

from __future__ import annotations

import time

import pytest

from netbox_sdk.schema import (
    FrozenDict,
    FrozenList,
    SchemaDocumentFrozenError,
    freeze_document,
)
from netbox_sdk.schema_resolution import _clear_bundled_index_cache, bundled_index

pytestmark = pytest.mark.suite_sdk


@pytest.fixture(autouse=True)
def _isolated_cache():
    """Never inherit or leak a cached index between tests in this module."""
    _clear_bundled_index_cache()
    yield
    _clear_bundled_index_cache()


def test_frozen_containers_still_satisfy_isinstance_checks() -> None:
    """The parser guards with ``isinstance(value, dict)``.

    A ``MappingProxyType`` fails that check, which would silently disable schema
    parsing rather than protect it — so the frozen types must subclass the real
    builtins.
    """
    frozen = freeze_document({"paths": {"/api/x/": {"get": {}}}, "servers": [{"url": "/"}]})

    assert isinstance(frozen, dict)
    assert isinstance(frozen["paths"], dict)
    assert isinstance(frozen["servers"], list)
    assert isinstance(frozen["servers"][0], dict)


def test_freeze_is_idempotent_and_does_not_rebuild() -> None:
    """Re-freezing an already frozen document must be free, not another deep pass."""
    once = freeze_document({"paths": {"/api/x/": {}}})
    twice = freeze_document(once)

    assert twice is once
    assert isinstance(once, FrozenDict)
    assert isinstance(freeze_document([1, 2]), FrozenList)


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda doc: doc.__setitem__("paths", {}), id="setitem"),
        pytest.param(lambda doc: doc.pop("paths"), id="pop"),
        pytest.param(lambda doc: doc.clear(), id="clear"),
        pytest.param(lambda doc: doc.update({"paths": {}}), id="update"),
        pytest.param(lambda doc: doc.setdefault("other", 1), id="setdefault"),
        pytest.param(lambda doc: doc.popitem(), id="popitem"),
        pytest.param(lambda doc: doc.__delitem__("paths"), id="delitem"),
    ],
)
def test_every_dict_mutation_route_is_blocked(mutate) -> None:
    """A guard that blocks only ``__setitem__`` is trivially routed around."""
    doc = freeze_document({"paths": {"/api/x/": {}}})

    with pytest.raises(SchemaDocumentFrozenError):
        mutate(doc)


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda seq: seq.append(1), id="append"),
        pytest.param(lambda seq: seq.pop(), id="pop"),
        pytest.param(lambda seq: seq.clear(), id="clear"),
        pytest.param(lambda seq: seq.extend([1]), id="extend"),
        pytest.param(lambda seq: seq.insert(0, 1), id="insert"),
        pytest.param(lambda seq: seq.remove("a"), id="remove"),
        pytest.param(lambda seq: seq.sort(), id="sort"),
        pytest.param(lambda seq: seq.reverse(), id="reverse"),
        pytest.param(lambda seq: seq.__setitem__(0, 1), id="setitem"),
    ],
)
def test_every_list_mutation_route_is_blocked(mutate) -> None:
    doc = freeze_document({"required": ["a", "b"]})

    with pytest.raises(SchemaDocumentFrozenError):
        mutate(doc["required"])


def test_one_caller_cannot_corrupt_a_later_bundled_index_caller() -> None:
    """The defect this exists to prevent, stated as the acceptance criterion.

    Popping a key from ``paths`` on one caller's index used to reach every later
    caller *and* leave already-created clones referencing paths the document no
    longer contained.
    """
    first = bundled_index("4.6")
    victim_path = next(iter(first.schema["paths"]))

    with pytest.raises(SchemaDocumentFrozenError):
        first.schema["paths"].pop(victim_path)

    second = bundled_index("4.6")

    assert victim_path in second.schema["paths"]
    # ...and the index is still internally consistent: every operation the
    # derived map advertises is still described by the document behind it.
    assert all(operation.path in second.schema["paths"] for operation in second.operations)


def test_nested_mutation_deep_inside_the_document_is_blocked() -> None:
    """Shallow freezing would leave the interesting corruption paths wide open."""
    index = bundled_index("4.6")
    path_item = index.schema["paths"][next(iter(index.schema["paths"]))]

    with pytest.raises(SchemaDocumentFrozenError):
        path_item["get"] = {"tampered": True}


def test_derived_maps_stay_mutable_per_clone() -> None:
    """Freezing the document must not freeze the parts clones are meant to edit."""
    first = bundled_index("4.6")
    second = bundled_index("4.6")

    assert first.add_discovered_resource(
        group="plugins",
        resource="demo/widgets",
        list_path="/api/plugins/demo/widgets/",
    )

    assert first.resource_paths(group="plugins", resource="demo/widgets") is not None
    assert second.resource_paths(group="plugins", resource="demo/widgets") is None


def test_repeated_bundled_index_calls_do_not_pay_the_freeze_cost() -> None:
    """The freeze is one pass per release line, not per call.

    Guards the acceptance criterion directly: the first call absorbs parse and
    freeze, every later call is a derived-map copy. Asserted as an order of
    magnitude rather than a fixed millisecond budget so it is not flaky on a
    loaded CI runner.
    """
    start = time.perf_counter()
    bundled_index("4.6")
    cold = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(5):
        bundled_index("4.6")
    warm = (time.perf_counter() - start) / 5

    assert warm < cold / 10, f"cached call {warm * 1000:.1f}ms vs cold {cold * 1000:.1f}ms"
