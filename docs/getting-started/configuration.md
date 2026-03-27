# Configuration

`netbox-sdk` stores connection settings in a JSON config file and supports two named profiles: `default` and `demo`.

---

## Interactive setup

Run `nbx init` to be prompted for your NetBox connection details:

```bash
nbx init
```

You will be prompted for:

- **NetBox base URL** — e.g. `https://netbox.example.com`
- **Token key** — the key portion of a v2 API token
- **Token secret** — the secret portion of a v2 API token
- **Timeout** — HTTP timeout in seconds (default: 30)

Any command that requires a connection will also prompt automatically if the config is missing.

---

## Config file location

| Condition | Path |
|-----------|------|
| `XDG_CONFIG_HOME` is set | `$XDG_CONFIG_HOME/netbox-cli/config.json` |
| Default | `~/.config/netbox-cli/config.json` |

The file uses a `profiles` structure:

```json
{
  "profiles": {
    "default": {
      "base_url": "https://netbox.example.com",
      "token_version": "v2",
      "token_key": "abc123",
      "token_secret": "xyz789",
      "timeout": 30.0
    },
    "demo": {
      "base_url": "https://demo.netbox.dev",
      "token_version": "v1",
      "token_key": null,
      "token_secret": "40-char-token-string",
      "timeout": 30.0
    }
  }
}
```

---

## Environment variable overrides

The following variables override the **default profile** only:

| Variable | Config field |
|----------|-------------|
| `NETBOX_URL` | `base_url` |
| `NETBOX_TOKEN_KEY` | `token_key` |
| `NETBOX_TOKEN_SECRET` | `token_secret` |

Environment variables take precedence over stored config values but are not saved to disk.

---

## Token formats

NetBox supports two token formats:

=== "v2 tokens (default)"

    v2 tokens have a separate key and secret, combined into a `Bearer` header:

    ```
    Authorization: Bearer nbt_<KEY>.<SECRET>
    ```

    When configuring: `token_key` = the key part, `token_secret` = the secret part.

=== "v1 tokens (legacy)"

    v1 tokens are a single opaque string, sent as:

    ```
    Authorization: Token <TOKEN>
    ```

    When configuring: leave `token_key` empty, set `token_secret` to the full token string.
    Set `token_version` to `"v1"` in the config file.

`netbox-sdk` automatically retries a failed v2 request with a v1 format when it receives a 401 or 403 response, so misconfigured token versions are usually corrected transparently.

---

## Viewing current config

```bash
nbx config              # shows base_url, timeout, token status
nbx config --show-token # also shows token key and secret in plaintext
```

Example output:

```json
{
  "base_url": "https://netbox.example.com",
  "timeout": 30.0,
  "token_version": "v2",
  "token": "set",
  "token_key": "set",
  "token_secret": "set"
}
```

---

## Multiple profiles

The `demo` profile is separate from the `default` profile and always targets `https://demo.netbox.dev`. It is managed through the `nbx demo` subcommand tree. See [Demo Profile](../cli/demo-profile.md) for details.
