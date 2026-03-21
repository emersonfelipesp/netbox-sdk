from __future__ import annotations

import json

from netbox_cli.config import (
    DEFAULT_PROFILE,
    DEMO_BASE_URL,
    DEMO_PROFILE,
    Config,
    clear_profile_config,
    config_path,
    load_profile_config,
    save_profile_config,
)


def test_load_profile_config_reads_legacy_default(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    path = config_path()
    path.write_text(
        json.dumps(
            {
                "base_url": "https://netbox.example.com",
                "token_key": "abc",
                "token_secret": "def",
                "timeout": 12.0,
            }
        ),
        encoding="utf-8",
    )

    cfg = load_profile_config(DEFAULT_PROFILE)

    assert cfg.base_url == "https://netbox.example.com"
    assert cfg.token_version == "v2"
    assert cfg.token_key == "abc"
    assert cfg.token_secret == "def"
    assert cfg.timeout == 12.0


def test_demo_profile_ignores_env_url(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("NETBOX_URL", "https://wrong.example.com")

    cfg = load_profile_config(DEMO_PROFILE)

    assert cfg.base_url == DEMO_BASE_URL


def test_save_profile_config_persists_profiles(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    save_profile_config(
        DEFAULT_PROFILE,
        Config(
            base_url="https://netbox.example.com",
            token_key="root",
            token_secret="secret",
            timeout=30.0,
        ),
    )
    save_profile_config(
        DEMO_PROFILE,
        Config(
            base_url="https://ignored.example.com",
            token_version="v1",
            token_key="demo",
            token_secret="demo-secret",
            timeout=45.0,
        ),
    )

    stored = json.loads(config_path().read_text(encoding="utf-8"))

    assert stored["profiles"]["default"]["base_url"] == "https://netbox.example.com"
    assert stored["profiles"]["demo"]["base_url"] == DEMO_BASE_URL
    assert stored["profiles"]["demo"]["token_version"] == "v1"
    assert stored["profiles"]["demo"]["token_key"] == "demo"


def test_save_demo_profile_migrates_legacy_default(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    path = config_path()
    path.write_text(
        json.dumps(
            {
                "base_url": "https://netbox.example.com",
                "token_key": "abc",
                "token_secret": "def",
                "timeout": 12.0,
            }
        ),
        encoding="utf-8",
    )

    save_profile_config(
        DEMO_PROFILE,
        Config(
            base_url=DEMO_BASE_URL,
            token_key="demo",
            token_secret="secret",
            timeout=10.0,
        ),
    )

    stored = json.loads(path.read_text(encoding="utf-8"))
    assert stored["profiles"]["default"]["base_url"] == "https://netbox.example.com"
    assert stored["profiles"]["demo"]["base_url"] == DEMO_BASE_URL


def test_clear_profile_config_removes_only_selected_profile(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    save_profile_config(
        DEFAULT_PROFILE,
        Config(
            base_url="https://netbox.example.com",
            token_key="root",
            token_secret="secret",
            timeout=30.0,
        ),
    )
    save_profile_config(
        DEMO_PROFILE,
        Config(
            base_url=DEMO_BASE_URL,
            token_key="demo",
            token_secret="demo-secret",
            timeout=45.0,
        ),
    )

    clear_profile_config(DEMO_PROFILE)

    stored = json.loads(config_path().read_text(encoding="utf-8"))
    assert "default" in stored["profiles"]
    assert "demo" not in stored["profiles"]
