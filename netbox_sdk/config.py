"""Configuration loading, profile persistence, and private config file handling."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, field_validator

DEFAULT_TIMEOUT = 30.0
DEFAULT_CONFIG_DIRNAME = "netbox-sdk"
LEGACY_CONFIG_DIRNAME = "netbox-cli"
DEFAULT_CONFIG_FILENAME = "config.json"
DEFAULT_HTTP_CACHE_DIRNAME = "http-cache"
TOKEN_KEY_ENV_VAR = "NETBOX_TOKEN_KEY"
TOKEN_SECRET_ENV_VAR = "NETBOX_TOKEN_SECRET"
BASE_URL_ENV_VAR = "NETBOX_URL"
DEMO_USERNAME_ENV_VAR = "DEMO_USERNAME"
DEMO_PASSWORD_ENV_VAR = "DEMO_PASSWORD"
DEFAULT_PROFILE = "default"
DEMO_PROFILE = "demo"
DEMO_BASE_URL = "https://demo.netbox.dev"


class Config(BaseModel):
    base_url: str | None = None
    token_version: str = "v2"
    token_key: str | None = None
    token_secret: str | None = None
    demo_username: str | None = None
    demo_password: str | None = None
    timeout: float = DEFAULT_TIMEOUT

    @field_validator("base_url", mode="before")
    @classmethod
    def _normalize_url(cls, v: object) -> str | None:
        if v is None:
            return None
        raw = str(v).strip()
        if not raw:
            return None
        return normalize_base_url(raw)

    @field_validator("token_version", mode="before")
    @classmethod
    def _normalize_token_version(cls, v: object) -> str:
        raw = str(v or "v2").strip().lower()
        return raw if raw in {"v1", "v2"} else "v2"

    @field_validator("token_key", "token_secret", mode="before")
    @classmethod
    def _coerce_optional_str(cls, v: object) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    @field_validator("timeout", mode="before")
    @classmethod
    def _coerce_timeout(cls, v: object) -> float:
        try:
            return float(v or DEFAULT_TIMEOUT)
        except (TypeError, ValueError):
            return DEFAULT_TIMEOUT


def normalize_base_url(value: str) -> str:
    url = value.strip()
    if not url:
        raise ValueError("base_url cannot be empty")
    if "://" not in url:
        url = f"https://{url}"
    parsed = urlsplit(url)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise ValueError("base_url must use http or https")
    if not parsed.netloc:
        raise ValueError("base_url must include a host")
    if parsed.username or parsed.password:
        raise ValueError("base_url must not include embedded credentials")
    if parsed.query or parsed.fragment:
        raise ValueError("base_url must not include query parameters or fragments")
    normalized_path = parsed.path.rstrip("/")
    return urlunsplit((scheme, parsed.netloc, normalized_path, "", ""))


def _set_private_permissions(path: Path, mode: int) -> None:
    try:
        if os.name != "nt":
            path.chmod(mode)
    except OSError:
        return


def _write_private_json(path: Path, payload: dict[str, object]) -> None:
    serialized = json.dumps(payload, indent=2)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(serialized)
    finally:
        _set_private_permissions(path, stat.S_IRUSR | stat.S_IWUSR)


def config_dir() -> Path:
    root = os.environ.get("XDG_CONFIG_HOME")
    if root:
        cfg_dir = Path(root) / DEFAULT_CONFIG_DIRNAME
    else:
        cfg_dir = Path.home() / ".config" / DEFAULT_CONFIG_DIRNAME
    cfg_dir.mkdir(parents=True, exist_ok=True)
    _set_private_permissions(cfg_dir, stat.S_IRWXU)
    return cfg_dir


def config_path() -> Path:
    return config_dir() / DEFAULT_CONFIG_FILENAME


def legacy_config_path() -> Path:
    root = os.environ.get("XDG_CONFIG_HOME")
    if root:
        return Path(root) / LEGACY_CONFIG_DIRNAME / DEFAULT_CONFIG_FILENAME
    return Path.home() / ".config" / LEGACY_CONFIG_DIRNAME / DEFAULT_CONFIG_FILENAME


def cache_dir() -> Path:
    return config_path().parent / DEFAULT_HTTP_CACHE_DIRNAME


def _load_raw_document() -> dict[str, object]:
    path = config_path()
    if not path.exists():
        legacy = legacy_config_path()
        if legacy.exists():
            path = legacy
        else:
            return {}
    loaded = json.loads(path.read_text(encoding="utf-8"))
    return loaded if isinstance(loaded, dict) else {}


def _coerce_config(payload: dict[str, object], *, apply_env: bool) -> Config:
    raw: dict[str, object] = dict(payload)
    if apply_env:
        raw["base_url"] = raw.get("base_url") or os.environ.get(BASE_URL_ENV_VAR)
        raw["token_key"] = raw.get("token_key") or os.environ.get(TOKEN_KEY_ENV_VAR)
        raw["token_secret"] = raw.get("token_secret") or os.environ.get(TOKEN_SECRET_ENV_VAR)
    raw["demo_username"] = raw.get("demo_username") or os.environ.get(DEMO_USERNAME_ENV_VAR)
    raw["demo_password"] = raw.get("demo_password") or os.environ.get(DEMO_PASSWORD_ENV_VAR)
    return Config.model_validate(raw)


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
    serialized = cfg.model_dump()
    if profile == DEMO_PROFILE:
        serialized["base_url"] = DEMO_BASE_URL
    profiles[profile] = serialized
    _write_private_json(path, {"profiles": profiles})


def save_config(cfg: Config) -> None:
    save_profile_config(DEFAULT_PROFILE, cfg)


def clear_profile_config(profile: str) -> None:
    path = config_path()
    stored = _load_raw_document()

    if "base_url" in stored or "token_key" in stored or "token_secret" in stored:
        if profile == DEFAULT_PROFILE:
            for candidate in (path, legacy_config_path()):
                if candidate.exists():
                    candidate.unlink()
        return

    profiles_obj = stored.get("profiles")
    profiles = profiles_obj if isinstance(profiles_obj, dict) else {}
    if profile in profiles:
        del profiles[profile]
    _write_private_json(path, {"profiles": profiles})


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
