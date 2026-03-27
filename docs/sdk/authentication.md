# Authentication

NetBox supports two token formats. The SDK handles both transparently.

---

## Token versions

=== "v2 (default)"

    NetBox 4.x issues v2 tokens in two parts: a **key** prefix and a **secret** suffix, combined as `nbt_<key>.<secret>`.

    ```python
    from netbox_sdk import Config

    cfg = Config(
        base_url="https://netbox.example.com",
        token_version="v2",
        token_key="abc123",         # the part after "nbt_"
        token_secret="def456xyz",   # the secret suffix
    )
    ```

    The `Authorization` header sent to NetBox will be:
    ```
    Bearer nbt_abc123.def456xyz
    ```

=== "v1 (legacy)"

    Older NetBox instances use a single opaque token:

    ```python
    cfg = Config(
        base_url="https://netbox.example.com",
        token_version="v1",
        token_secret="abcdef1234567890abcdef1234567890abcdef12",
    )
    ```

    The `Authorization` header will be:
    ```
    Token abcdef1234567890abcdef1234567890abcdef12
    ```

---

## Automatic v2 → v1 fallback

If your configuration specifies v2 but the NetBox instance rejects the Bearer token with `"Invalid v2 token"`, the client automatically retries with the v1 `Token <secret>` header. This handles instances that have v1 tokens stored but are accessed with v2 config.

---

## Auth header helpers

```python
from netbox_sdk.config import authorization_header_value, resolved_token

cfg = Config(base_url="...", token_version="v2", token_key="k", token_secret="s")

resolved_token(cfg)              # "nbt_k.s"
authorization_header_value(cfg)  # "Bearer nbt_k.s"
```

---

## Profile storage

The SDK stores named connection profiles at `~/.config/netbox-cli/config.json` (or `$XDG_CONFIG_HOME/netbox-cli/config.json`).

```python
from netbox_sdk.config import (
    load_profile_config,
    save_profile_config,
    clear_profile_config,
    DEFAULT_PROFILE,
)

# Load the "default" profile (applies env var overrides automatically)
cfg = load_profile_config()
cfg = load_profile_config(DEFAULT_PROFILE)   # same thing

# Save a custom profile
save_profile_config("production", cfg)
save_profile_config("staging", staging_cfg)

# Load a named profile (no env var overrides applied)
staging = load_profile_config("staging")

# Remove a profile
clear_profile_config("staging")
```

### File security

The config directory is created with mode `0o700` and the config file with `0o600` to prevent other users on the same system from reading your credentials.

---

## Environment variable overrides

For the **default profile only**, these environment variables override values from disk:

| Variable | Config field |
|----------|-------------|
| `NETBOX_URL` | `base_url` |
| `NETBOX_TOKEN_KEY` | `token_key` |
| `NETBOX_TOKEN_SECRET` | `token_secret` |

Environment variables take precedence over stored values. Useful for CI/CD:

```bash
NETBOX_URL=https://netbox.example.com \
NETBOX_TOKEN_KEY=mykey \
NETBOX_TOKEN_SECRET=mysecret \
python your_script.py
```

```python
from netbox_sdk.config import load_config

cfg = load_config()   # picks up the environment variables
```

---

## Validating configuration

```python
from netbox_sdk.config import is_runtime_config_complete

if not is_runtime_config_complete(cfg):
    print("Missing base_url or token credentials")
```

This checks that `base_url`, `token_secret`, and (for v2) `token_key` are all present.

---

## URL normalization

The `base_url` field is normalized on assignment:

- Adds `https://` if no scheme is given
- Strips trailing slashes
- Rejects embedded credentials (`user:pass@host`)
- Rejects non-HTTP schemes (`ftp://`, `file://`)
- Rejects query strings and fragments

```python
from netbox_sdk.config import normalize_base_url

normalize_base_url("netbox.example.com")         # "https://netbox.example.com"
normalize_base_url("http://netbox.example.com/") # "http://netbox.example.com"
normalize_base_url("ftp://netbox.example.com")   # raises ValueError
```
