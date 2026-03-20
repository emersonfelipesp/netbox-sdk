from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_TIMEOUT = 30.0
DEFAULT_CONFIG_DIRNAME = "netbox-cli"
DEFAULT_CONFIG_FILENAME = "config.json"
TOKEN_KEY_ENV_VAR = "NETBOX_TOKEN_KEY"
TOKEN_SECRET_ENV_VAR = "NETBOX_TOKEN_SECRET"
BASE_URL_ENV_VAR = "NETBOX_URL"
DEFAULT_PROFILE = "default"
DEMO_PROFILE = "demo"
DEMO_BASE_URL = "https://demo.netbox.dev"


@dataclass(slots=True)
class Config:
    base_url: str | None = None
    token_version: str = "v2"
    token_key: str | None = None
    token_secret: str | None = None
    timeout: float = DEFAULT_TIMEOUT


def normalize_base_url(value: str) -> str:
    url = value.strip()
    if not url:
        raise ValueError("base_url cannot be empty")
    if "://" not in url:
        url = f"https://{url}"
    return url.rstrip("/")


def config_path() -> Path:
    root = os.environ.get("XDG_CONFIG_HOME")
    if root:
        cfg_dir = Path(root) / DEFAULT_CONFIG_DIRNAME
    else:
        cfg_dir = Path.home() / ".config" / DEFAULT_CONFIG_DIRNAME
    cfg_dir.mkdir(parents=True, exist_ok=True)
    return cfg_dir / DEFAULT_CONFIG_FILENAME


def _load_raw_document() -> dict[str, object]:
    path = config_path()
    if not path.exists():
        return {}
    loaded = json.loads(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _coerce_config(payload: dict[str, object], *, apply_env: bool) -> Config:
    raw_url_obj = payload.get("base_url")
    raw_token_version = str(payload.get("token_version") or "v2").strip().lower()
    raw_token_key = payload.get("token_key")
    raw_token_secret = payload.get("token_secret")
    timeout = float(payload.get("timeout") or DEFAULT_TIMEOUT)

    if apply_env:
        raw_url_obj = raw_url_obj or os.environ.get(BASE_URL_ENV_VAR)
        raw_token_key = raw_token_key or os.environ.get(TOKEN_KEY_ENV_VAR)
        raw_token_secret = raw_token_secret or os.environ.get(TOKEN_SECRET_ENV_VAR)

    raw_url = str(raw_url_obj).strip() if raw_url_obj else ""
    token_version = raw_token_version if raw_token_version in {"v1", "v2"} else "v2"
    return Config(
        base_url=normalize_base_url(raw_url) if raw_url else None,
        token_version=token_version,
        token_key=str(raw_token_key) if raw_token_key else None,
        token_secret=str(raw_token_secret) if raw_token_secret else None,
        timeout=timeout,
    )


def load_profile_config(profile: str = DEFAULT_PROFILE) -> Config:
    stored = _load_raw_document()

    # Backward-compatible flat config: treat root fields as the default profile.
    if "base_url" in stored or "token_key" in stored or "token_secret" in stored:
        if profile == DEFAULT_PROFILE:
            return _coerce_config(stored, apply_env=True)
        if profile == DEMO_PROFILE:
            return Config(base_url=DEMO_BASE_URL)
        return Config()

    profiles_obj = stored.get("profiles")
    profiles = profiles_obj if isinstance(profiles_obj, dict) else {}
    selected_obj = profiles.get(profile)
    selected = selected_obj if isinstance(selected_obj, dict) else {}
    cfg = _coerce_config(selected, apply_env=profile == DEFAULT_PROFILE)
    if profile == DEMO_PROFILE:
        cfg.base_url = DEMO_BASE_URL
    return cfg


def load_config() -> Config:
    return load_profile_config(DEFAULT_PROFILE)


def save_profile_config(profile: str, cfg: Config) -> None:
    path = config_path()
    stored = _load_raw_document()
    profiles: dict[str, object]
    if "base_url" in stored or "token_key" in stored or "token_secret" in stored:
        profiles = {
            DEFAULT_PROFILE: {
                "base_url": stored.get("base_url"),
                "token_version": stored.get("token_version") or "v2",
                "token_key": stored.get("token_key"),
                "token_secret": stored.get("token_secret"),
                "timeout": stored.get("timeout") or DEFAULT_TIMEOUT,
            }
        }
    else:
        profiles_obj = stored.get("profiles")
        profiles = dict(profiles_obj) if isinstance(profiles_obj, dict) else {}
    serialized = asdict(cfg)
    if profile == DEMO_PROFILE:
        serialized["base_url"] = DEMO_BASE_URL
    profiles[profile] = serialized
    path.write_text(json.dumps({"profiles": profiles}, indent=2), encoding="utf-8")


def save_config(cfg: Config) -> None:
    save_profile_config(DEFAULT_PROFILE, cfg)


def clear_profile_config(profile: str) -> None:
    path = config_path()
    stored = _load_raw_document()

    if "base_url" in stored or "token_key" in stored or "token_secret" in stored:
        if profile == DEFAULT_PROFILE and path.exists():
            path.unlink()
        return

    profiles_obj = stored.get("profiles")
    profiles = profiles_obj if isinstance(profiles_obj, dict) else {}
    if profile in profiles:
        del profiles[profile]
    path.write_text(json.dumps({"profiles": profiles}, indent=2), encoding="utf-8")


def resolved_token(cfg: Config) -> str | None:
    if cfg.token_version == "v1" and cfg.token_secret:
        return cfg.token_secret
    if cfg.token_key and cfg.token_secret:
        key = cfg.token_key
        if not key.startswith("nbt_"):
            key = f"nbt_{key}"
        return f"{key}.{cfg.token_secret}"
    return None


def authorization_header_value(cfg: Config) -> str | None:
    token = resolved_token(cfg)
    if not token:
        return None
    if cfg.token_version == "v1":
        return f"Token {token}"
    return f"Bearer {token}"


def is_runtime_config_complete(cfg: Config) -> bool:
    if not cfg.base_url or not cfg.token_secret:
        return False
    if cfg.token_version == "v1":
        return True
    return bool(cfg.token_key)
