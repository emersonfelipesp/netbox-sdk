# OpenBao CLI

`nbx openbao` exposes the maintained `netbox-openbao` contract without direct
OpenBao access. `nbx openbao resources` prints the client-free catalog.
Collections use the normal `list`, `get`, `create`, `update`, `patch`, `delete`,
and bulk commands allowed by the server contract.

```bash
nbx openbao credentials list -q policy_id=4
nbx openbao credentials create \
  --body-json '{"name":"router","generate_ssh_key":true,"ssh_key_type":"ed25519"}' \
  --confirm
nbx openbao actions credential-rotate --id 12 \
  --body-file rotation.json --confirm
nbx openbao actions cluster-auth-resource --id 3 \
  --path-param mount_path=userpass --path-param resource_key=users \
  --path-param name=alice --method GET
```

Every mutation and every material-bearing read requires `--confirm` before a
client is created. Repeated
`--query`, `--header`, and `--path-param` options preserve the endpoint's
transport shape. Secret output is intentionally one-shot terminal output: do
not redirect it to logs, shell history, shared storage, or CI artifacts.

Snapshot files use dedicated bounded commands:

```bash
nbx openbao snapshot download --id 3 --output cluster.snap --max-bytes 536870912 --confirm
nbx openbao snapshot upload --id 3 --input cluster.snap \
  --reason "disaster recovery" --confirmation "RESTORE SNAPSHOT primary" \
  --openbao-cluster-id raft-cluster-a --raft-index 17 --confirm
nbx openbao snapshot upload --id 3 --input cluster.snap --force \
  --reason "approved forced recovery" --confirmation "FORCE RESTORE SNAPSHOT primary" \
  --openbao-cluster-id raft-cluster-a --raft-index 17 --confirm
```

Download creates the destination atomically with mode `0600` and refuses to
overwrite an existing path. Upload opens the source without following symlinks,
validates the opened descriptor and its byte bound, and sends the four required
OpenBao restore headers from typed options. Neither operation retries
automatically. A failed mutation may have committed, so inspect authoritative
plugin state before retrying.
