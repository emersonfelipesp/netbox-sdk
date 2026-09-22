# OpenBao SDK

`netbox_sdk.openbao` is the maintained SDK contract for `netbox-openbao`. It
contains a fixed inventory of the plugin's ten REST collections and every
custom action exposed by the canonical plugin API. Runtime discovery remains
available for unknown plugins, but it is not the authority for this
security-sensitive surface.

```python
from netbox_sdk.openbao import OpenBaoClient

openbao = OpenBaoClient(client)
await openbao.request_resource("credentials", "create", payload={
    "name": "router-admin",
    "policy": 4,
    "credential_type": "ssh-key",
    "generate_ssh_key": True,
    "ssh_key_type": "ed25519",
})
await openbao.request_action(
    "credential.rotate",
    path_parameters={"id": 12},
    payload={"secret_data": {"password": replacement}},
)
```

Server-side SSH key generation is part of standard credential creation. The
private key remains write-only and is never represented as a separate action.
The `credential.quick-add-ssh` route coordinates the atomic quick-add operation.

All action and resource requests bypass the SDK response cache. Material
responses must be consumed once and must not be logged, persisted, or included
in exception messages. The SDK does not retry these operations automatically:
after a transport failure, inspect server state before deciding whether to
repeat a mutation.

Raft snapshots use `download_snapshot()` and `upload_snapshot()`. Both enforce
explicit byte bounds. Upload opens a regular file without following symlinks and
requires `reason`, the exact `confirmation`, `openbao_cluster_id`, and
`configuration_index`; these become the four required restore headers. Download
returns bytes without text decoding, caching, redirects, or retry fallback.

Nested administration routes use named path parameters. Values are restricted
to a single safe URL segment, and the complete required set must be supplied.
Server permissions, capability digests, confirmation strings, impact digests,
reasons, and state checks remain authoritative.
