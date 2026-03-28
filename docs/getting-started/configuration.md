# Configuration

`netbox-sdk` stores connection settings in a JSON config file and supports two
named profiles: `default` and `demo`.

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
- **TLS verification** — optional; see [HTTPS and TLS verification](#https-and-tls-verification)

Any command that requires a connection will also prompt automatically if the config is missing.

---

## HTTPS and TLS verification

For **HTTPS** base URLs, the SDK verifies the server TLS certificate using the system trust store (same default as Python `ssl`).

### When verification fails (self-signed or private CA)

If the server uses a self-signed certificate or a CA that is not in your system store, the first connection fails with a certificate verification error.

**Unset preference (`ssl_verify` omitted or `null`):** the CLI and TUIs can prompt once to either:

- **Disable verification** for this profile — stored as `"ssl_verify": false` (insecure; use only on trusted networks).
- **Keep verification enabled** — stored as `"ssl_verify": true`; you must fix the certificate chain or add the issuing CA to the system trust store.

After you choose, the preference is saved and you are not prompted again for that profile unless you edit the config.

**Explicit preference:** if `ssl_verify` is already `true` or `false` in config, the tools do not prompt; they honor the setting.

### `nbx init`

```bash
# Explicitly persist verification on or off (recommended for automation)
nbx init --base-url https://netbox.example.com --token-key KEY --token-secret SECRET --verify-ssl
nbx init ... --no-verify-ssl
```

Omit both flags to leave `ssl_verify` unset until the first connection (defaults to verifying at runtime, with optional prompt on failure).

### Environment variable

For the **default profile** only, `NETBOX_SSL_VERIFY` overrides the stored value when set:

| Value | Effect |
|-------|--------|
| `1`, `true`, `yes`, `on` | Verify certificates |
| `0`, `false`, `no`, `off` | Disable verification |

Unset the variable to use the value from `config.json`.

### `nbx test`

`nbx test` probes the API using the active profile. If verification fails and `ssl_verify` is unset, the same interactive choice as above is offered before the command exits.

### Textual TUIs

When a connection health check fails for a certificate reason and `ssl_verify` is unset, the main TUI, CLI builder, developer workbench, and Django model inspector can show a modal: **Keep verification** or **Disable verification** (saved to the profile).

### Config file field

Add optional `ssl_verify` to a profile (boolean or omit / `null`):

```json
"default": {
  "base_url": "https://netbox.example.com",
  "token_version": "v2",
  "token_key": "abc123",
  "token_secret": "xyz789",
  "timeout": 30.0,
  "ssl_verify": false
}
```

---

## Config file location

| Condition | Path |
|-----------|------|
| `XDG_CONFIG_HOME` is set | `$XDG_CONFIG_HOME/netbox-sdk/config.json` |
| Default | `~/.config/netbox-sdk/config.json` |

Older `netbox-cli` config files are still read automatically if the new
`netbox-sdk` path is not present yet.

The file uses a `profiles` structure:

```json
{
  "profiles": {
    "default": {
      "base_url": "https://netbox.example.com",
      "token_version": "v2",
      "token_key": "abc123",
      "token_secret": "xyz789",
      "timeout": 30.0,
      "ssl_verify": null
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
| `NETBOX_SSL_VERIFY` | `ssl_verify` (see [HTTPS and TLS verification](#https-and-tls-verification)) |

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
  "ssl_verify": null,
  "token": "set",
  "token_key": "set",
  "token_secret": "set"
}
```

`ssl_verify` is `true`, `false`, or `null` when no explicit value has been stored yet.

---

## Multiple profiles

The `demo` profile is separate from the `default` profile and always targets `https://demo.netbox.dev`. It is managed through the `nbx demo` subcommand tree. See [Demo Profile](../cli/demo-profile.md) for details.
