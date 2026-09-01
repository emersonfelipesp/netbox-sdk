"""Contract for the live NetBox ``/api/status/`` matrix allow-list."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.check_live_netbox_status import (
    PREVIEW_LIVE_IMAGE,
    allowed_live_status_versions,
    live_status_matches,
    main,
)

pytestmark = pytest.mark.suite_sdk


def test_stable_pins_require_an_exact_status_match() -> None:
    assert allowed_live_status_versions("v4.6.6") == frozenset({"4.6.6"})
    assert live_status_matches("v4.6.6", "4.6.6")
    assert not live_status_matches("v4.6.6", "4.6.3")


def test_preview_pin_requires_the_pinned_image_and_observed_status() -> None:
    assert allowed_live_status_versions("v4.7.0-beta2", PREVIEW_LIVE_IMAGE) == frozenset({"4.7.0"})
    assert live_status_matches("v4.7.0-beta2", "4.7.0", PREVIEW_LIVE_IMAGE)
    assert not live_status_matches("v4.7.0-beta2", "4.7.0")
    assert not live_status_matches(
        "v4.7.0-beta2", "4.7.0", "ghcr.io/netbox-community/netbox:v4.7.0-beta2"
    )
    assert not live_status_matches("v4.7.0-beta2", "4.7.0-beta2", PREVIEW_LIVE_IMAGE)


def test_preview_image_constant_is_the_workflow_runtime_image() -> None:
    workflow = Path(__file__).resolve().parents[1] / ".github/workflows/test.yml"
    text = workflow.read_text(encoding="utf-8")
    assert f'image="{PREVIEW_LIVE_IMAGE}"' in text or PREVIEW_LIVE_IMAGE in text
    assert 'echo "NETBOX_CI_IMAGE=$image"' in text
    assert '--image "${NETBOX_CI_IMAGE:-}"' in text


def test_cli_accepts_the_preview_status_only_for_the_pinned_image(
    tmp_path,
) -> None:
    status = tmp_path / "status.json"
    status.write_text(json.dumps({"netbox-version": "4.7.0"}), encoding="utf-8")
    assert (
        main(
            [
                "--expected",
                "v4.7.0-beta2",
                "--status-file",
                str(status),
                "--image",
                PREVIEW_LIVE_IMAGE,
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "--expected",
                "v4.7.0-beta2",
                "--status-file",
                str(status),
                "--image",
                "ghcr.io/netbox-community/netbox:v4.7.0-beta2",
            ]
        )
        == 1
    )
