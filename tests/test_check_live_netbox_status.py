"""Contract for the live NetBox ``/api/status/`` matrix allow-list."""

from __future__ import annotations

import json

import pytest

from scripts.check_live_netbox_provenance import (
    image_digest_matches,
    source_commit_matches,
)
from scripts.check_live_netbox_provenance import (
    main as provenance_main,
)
from scripts.check_live_netbox_status import (
    allowed_live_status_versions,
    live_status_matches,
    main,
)

pytestmark = pytest.mark.suite_sdk


def test_stable_pins_require_an_exact_status_match() -> None:
    assert allowed_live_status_versions("v4.6.6") == frozenset({"4.6.6"})
    assert live_status_matches("v4.6.6", "4.6.6")
    assert not live_status_matches("v4.6.6", "4.6.3")


def test_v47_ga_pin_requires_an_exact_status_match() -> None:
    assert allowed_live_status_versions("v4.7.0") == frozenset({"4.7.0"})
    assert live_status_matches("v4.7.0", "4.7.0")
    assert not live_status_matches("v4.7.0", "4.7.1")


def test_cli_accepts_only_the_exact_status(tmp_path) -> None:
    status = tmp_path / "status.json"
    status.write_text(json.dumps({"netbox-version": "4.7.0"}), encoding="utf-8")
    assert (
        main(
            [
                "--expected",
                "v4.7.0",
                "--status-file",
                str(status),
            ]
        )
        == 0
    )
    status.write_text(json.dumps({"netbox-version": "4.7.1"}), encoding="utf-8")
    assert main(["--expected", "v4.7.0", "--status-file", str(status)]) == 1


def test_live_source_commit_guard_fails_closed_on_mutation() -> None:
    reviewed = "5f06007e4c9bacc93ce17c1e645fc1143d60df3d"
    wrong = "0" * 40

    assert source_commit_matches(reviewed, reviewed)
    assert not source_commit_matches(reviewed, wrong)
    assert provenance_main(["--expected-commit", reviewed, "--actual-commit", wrong]) == 1


def test_live_image_digest_guard_fails_closed_on_mutation(tmp_path) -> None:
    reviewed = "sha256:a2cdf00fab61d2ae37e4f987adaa403fad5c4049a63bc960768b7bbf804e2cb6"
    wrong = "sha256:" + "0" * 64
    evidence = tmp_path / "repo-digests.json"
    evidence.write_text(
        json.dumps([f"ghcr.io/netbox-community/netbox@{wrong}"]),
        encoding="utf-8",
    )

    assert image_digest_matches(reviewed, [f"ghcr.io/netbox-community/netbox@{reviewed}"])
    assert not image_digest_matches(reviewed, [f"ghcr.io/netbox-community/netbox@{wrong}"])
    assert (
        provenance_main(
            [
                "--expected-image-digest",
                reviewed,
                "--repo-digests-file",
                str(evidence),
            ]
        )
        == 1
    )


def test_live_provenance_guard_rejects_missing_evidence() -> None:
    assert provenance_main([]) == 1
