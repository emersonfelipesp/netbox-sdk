from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path

DEFAULT_TIMEOUT = 30.0
DEFAULT_CONFIG_DIRNAME = "netbox-cli"
DEFAULT_CONFIG_FILENAME = "config.json"
TOKEN_KEY_ENV_VAR = "NETBOX_TOKEN_KEY"
TOKEN_SECRET_ENV_VAR = "NETBOX_TOKEN_SECRET"
BASE_URL_ENV_VAR = "NETBOX_URL"


@dataclass(slots=True)
class Config:
    base_url: str | None = None
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



def load_config() -> Config:
    path = config_path()
    stored: dict[str, object] = {}
    if path.exists():
        stored = json.loads(path.read_text(encoding="utf-8"))

    raw_url_obj = stored.get("base_url") or os.environ.get(BASE_URL_ENV_VAR)
    raw_url = str(raw_url_obj).strip() if raw_url_obj else ""
    raw_token_key = stored.get("token_key") or os.environ.get(TOKEN_KEY_ENV_VAR)
    raw_token_secret = stored.get("token_secret") or os.environ.get(TOKEN_SECRET_ENV_VAR)
    timeout = float(stored.get("timeout") or DEFAULT_TIMEOUT)
    return Config(
        base_url=normalize_base_url(raw_url) if raw_url else None,
        token_key=str(raw_token_key) if raw_token_key else None,
        token_secret=str(raw_token_secret) if raw_token_secret else None,
        timeout=timeout,
    )



def save_config(cfg: Config) -> None:
    path = config_path()
    path.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")


def resolved_token(cfg: Config) -> str | None:
    if cfg.token_key and cfg.token_secret:
        key = cfg.token_key
        if not key.startswith("nbt_"):
            key = f"nbt_{key}"
        return f"{key}.{cfg.token_secret}"
    return None


def is_runtime_config_complete(cfg: Config) -> bool:
    return bool(cfg.base_url and cfg.token_key and cfg.token_secret)
