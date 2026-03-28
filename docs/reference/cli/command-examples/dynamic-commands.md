# Dynamic Commands

## `nbx dcim --help`

=== ":material-console: Command"

    ```bash
    nbx dcim --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dcim --help
    ```

    ```text
                                                                                    
     Usage: nbx dcim [OPTIONS] COMMAND [ARGS]...                                    
                                                                                    
     OpenAPI app group: dcim                                                        
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --help          Show this message and exit.                                  │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ╭─ Commands ───────────────────────────────────────────────────────────────────╮
    │ cable-terminations             Resource: dcim/cable-terminations             │
    │ cables                         Resource: dcim/cables                         │
    │ connected-device               Resource: dcim/connected-device               │
    │ console-port-templates         Resource: dcim/console-port-templates         │
    │ console-ports                  Resource: dcim/console-ports                  │
    │ console-server-port-templates  Resource: dcim/console-server-port-templates  │
    │ console-server-ports           Resource: dcim/console-server-ports           │
    │ device-bay-templates           Resource: dcim/device-bay-templates           │
    │ device-bays                    Resource: dcim/device-bays                    │
    │ device-roles                   Resource: dcim/device-roles                   │
    │ device-types                   Resource: dcim/device-types                   │
    │ devices                        Resource: dcim/devices                        │
    │ front-port-templates           Resource: dcim/front-port-templates           │
    │ front-ports                    Resource: dcim/front-ports                    │
    │ interface-templates            Resource: dcim/interface-templates            │
    │ interfaces                     Resource: dcim/interfaces                     │
    │ inventory-item-roles           Resource: dcim/inventory-item-roles           │
    │ inventory-item-templates       Resource: dcim/inventory-item-templates       │
    │ inventory-items                Resource: dcim/inventory-items                │
    │ locations                      Resource: dcim/locations                      │
    │ mac-addresses                  Resource: dcim/mac-addresses                  │
    │ manufacturers                  Resource: dcim/manufacturers                  │
    │ module-bay-templates           Resource: dcim/module-bay-templates           │
    │ module-bays                    Resource: dcim/module-bays                    │
    │ module-type-profiles           Resource: dcim/module-type-profiles           │
    │ module-types                   Resource: dcim/module-types                   │
    │ modules                        Resource: dcim/modules                        │
    │ platforms                      Resource: dcim/platforms                      │
    │ power-feeds                    Resource: dcim/power-feeds                    │
    │ power-outlet-templates         Resource: dcim/power-outlet-templates         │
    │ power-outlets                  Resource: dcim/power-outlets                  │
    │ power-panels                   Resource: dcim/power-panels                   │
    │ power-port-templates           Resource: dcim/power-port-templates           │
    │ power-ports                    Resource: dcim/power-ports                    │
    │ rack-reservations              Resource: dcim/rack-reservations              │
    │ rack-roles                     Resource: dcim/rack-roles                     │
    │ rack-types                     Resource: dcim/rack-types                     │
    │ racks                          Resource: dcim/racks                          │
    │ rear-port-templates            Resource: dcim/rear-port-templates            │
    │ rear-ports                     Resource: dcim/rear-ports                     │
    │ regions                        Resource: dcim/regions                        │
    │ site-groups                    Resource: dcim/site-groups                    │
    │ sites                          Resource: dcim/sites                          │
    │ virtual-chassis                Resource: dcim/virtual-chassis                │
    │ virtual-device-contexts        Resource: dcim/virtual-device-contexts        │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.903s</span>

---

## `nbx dcim devices --help`

=== ":material-console: Command"

    ```bash
    nbx dcim devices --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dcim devices --help
    ```

    ```text
                                                                                    
     Usage: nbx dcim devices [OPTIONS] COMMAND [ARGS]...                            
                                                                                    
     Resource: dcim/devices                                                         
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --help          Show this message and exit.                                  │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ╭─ Commands ───────────────────────────────────────────────────────────────────╮
    │ list    list dcim/devices                                                    │
    │ get     get dcim/devices                                                     │
    │ create  create dcim/devices                                                  │
    │ update  update dcim/devices                                                  │
    │ patch   patch dcim/devices                                                   │
    │ delete  delete dcim/devices                                                  │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.875s</span>

---

## `nbx dcim devices list --help`

=== ":material-console: Command"

    ```bash
    nbx dcim devices list --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dcim devices list --help
    ```

    ```text
                                                                                    
     Usage: nbx dcim devices list [OPTIONS]                                         
                                                                                    
     list dcim/devices                                                              
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --id                   INTEGER  Object ID for detail operations              │
    │ --query        -q      TEXT     Query parameter key=value                    │
    │ --body-json            TEXT     Inline JSON request body                     │
    │ --body-file            TEXT     Path to JSON request body file               │
    │ --json                          Output raw JSON                              │
    │ --yaml                          Output YAML                                  │
    │ --markdown                      Output Markdown (mutually exclusive with     │
    │                                 --json/--yaml)                               │
    │ --trace                         Fetch and render the cable trace as ASCII    │
    │                                 when supported.                              │
    │ --trace-only                    Render only the cable trace ASCII output     │
    │                                 when supported.                              │
    │ --select               TEXT     JSON dot-path to extract specific field from │
    │                                 response                                     │
    │ --columns              TEXT     Comma-separated list of columns to display   │
    │ --max-columns          INTEGER  Maximum number of columns to display         │
    │                                 [default: 6]                                 │
    │ --dry-run                       Preview write operation without executing    │
    │                                 (create/update/patch/delete only)            │
    │ --help                          Show this message and exit.                  │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.832s</span>

---

## `nbx ipam prefixes --help`

=== ":material-console: Command"

    ```bash
    nbx ipam prefixes --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx ipam prefixes --help
    ```

    ```text
                                                                                    
     Usage: nbx ipam prefixes [OPTIONS] COMMAND [ARGS]...                           
                                                                                    
     Resource: ipam/prefixes                                                        
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --help          Show this message and exit.                                  │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ╭─ Commands ───────────────────────────────────────────────────────────────────╮
    │ list    list ipam/prefixes                                                   │
    │ get     get ipam/prefixes                                                    │
    │ create  create ipam/prefixes                                                 │
    │ update  update ipam/prefixes                                                 │
    │ patch   patch ipam/prefixes                                                  │
    │ delete  delete ipam/prefixes                                                 │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.507s</span>

---

## `nbx dcim interfaces get --help`

=== ":material-console: Command"

    ```bash
    nbx dcim interfaces get --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dcim interfaces get --help
    ```

    ```text
                                                                                    
     Usage: nbx dcim interfaces get [OPTIONS]                                       
                                                                                    
     get dcim/interfaces                                                            
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --id                   INTEGER  Object ID for detail operations              │
    │ --query        -q      TEXT     Query parameter key=value                    │
    │ --body-json            TEXT     Inline JSON request body                     │
    │ --body-file            TEXT     Path to JSON request body file               │
    │ --json                          Output raw JSON                              │
    │ --yaml                          Output YAML                                  │
    │ --markdown                      Output Markdown (mutually exclusive with     │
    │                                 --json/--yaml)                               │
    │ --trace                         Fetch and render the cable trace as ASCII    │
    │                                 when supported.                              │
    │ --trace-only                    Render only the cable trace ASCII output     │
    │                                 when supported.                              │
    │ --select               TEXT     JSON dot-path to extract specific field from │
    │                                 response                                     │
    │ --columns              TEXT     Comma-separated list of columns to display   │
    │ --max-columns          INTEGER  Maximum number of columns to display         │
    │                                 [default: 6]                                 │
    │ --dry-run                       Preview write operation without executing    │
    │                                 (create/update/patch/delete only)            │
    │ --help                          Show this message and exit.                  │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.699s</span>

---

## `nbx circuits circuit-terminations get --help`

=== ":material-console: Command"

    ```bash
    nbx circuits circuit-terminations get --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx circuits circuit-terminations get --help
    ```

    ```text
                                                                                    
     Usage: nbx circuits circuit-terminations get [OPTIONS]                         
                                                                                    
     get circuits/circuit-terminations                                              
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --id                   INTEGER  Object ID for detail operations              │
    │ --query        -q      TEXT     Query parameter key=value                    │
    │ --body-json            TEXT     Inline JSON request body                     │
    │ --body-file            TEXT     Path to JSON request body file               │
    │ --json                          Output raw JSON                              │
    │ --yaml                          Output YAML                                  │
    │ --markdown                      Output Markdown (mutually exclusive with     │
    │                                 --json/--yaml)                               │
    │ --trace                         Fetch and render the cable trace as ASCII    │
    │                                 when supported.                              │
    │ --trace-only                    Render only the cable trace ASCII output     │
    │                                 when supported.                              │
    │ --select               TEXT     JSON dot-path to extract specific field from │
    │                                 response                                     │
    │ --columns              TEXT     Comma-separated list of columns to display   │
    │ --max-columns          INTEGER  Maximum number of columns to display         │
    │                                 [default: 6]                                 │
    │ --dry-run                       Preview write operation without executing    │
    │                                 (create/update/patch/delete only)            │
    │ --help                          Show this message and exit.                  │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.624s</span>

---

## `nbx demo dcim devices list --select results.0.name`

=== ":material-console: Command"

    ```bash
    nbx demo dcim devices list --select results.0.name
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo dcim devices list --select results.0.name
    ```

    ```text
    (empty)
    ```

<span class="nbx-badge nbx-badge--err">exit&nbsp;124</span> <span class="nbx-badge nbx-badge--neutral">60.040s</span>

---

## `nbx demo dcim devices list --columns id,name,status`

=== ":material-console: Command"

    ```bash
    nbx demo dcim devices list --columns id,name,status
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo dcim devices list --columns id,name,status
    ```

    ```text
    (empty)
    ```

<span class="nbx-badge nbx-badge--err">exit&nbsp;124</span> <span class="nbx-badge nbx-badge--neutral">60.050s</span>

---

## `nbx demo dcim devices list --max-columns 3`

=== ":material-console: Command"

    ```bash
    nbx demo dcim devices list --max-columns 3
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo dcim devices list --max-columns 3
    ```

    ```text
    Error: Unexpected failure: TimeoutError. Please retry or check your configuration.
    
    --- stderr ---
    api request failed
    Traceback (most recent call last):
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/client.py", line 779, in _request
        resp = await handler(req)
               ^^^^^^^^^^^^^^^^^^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/client.py", line 734, in _connect_and_send_request
        conn = await self._connector.connect(
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            req, traces=traces, timeout=real_timeout
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        )
        ^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/connector.py", line 672, in connect
        proto = await self._create_connection(req, traces, timeout)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/connector.py", line 1239, in _create_connection
        _, proto = await self._create_direct_connection(req, traces, timeout)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/connector.py", line 1562, in _create_direct_connection
        hosts = await self._resolve_host(host, port, traces=traces)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/connector.py", line 1178, in _resolve_host
        return await asyncio.shield(resolved_host_task)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    asyncio.exceptions.CancelledError
    
    The above exception was the direct cause of the following exception:
    
    Traceback (most recent call last):
      File "/root/nms/netbox-sdk/netbox_sdk/client.py", line 160, in request
        response = await self._request_once(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^
        ...<8 lines>...
        )
        ^
      File "/root/nms/netbox-sdk/netbox_sdk/client.py", line 238, in _request_once
        async with session.request(
                   ~~~~~~~~~~~~~~~^
            method=method.upper(),
            ^^^^^^^^^^^^^^^^^^^^^^
        ...<4 lines>...
            headers=req_headers,
            ^^^^^^^^^^^^^^^^^^^^
        ) as response:
        ^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/client.py", line 1510, in __aenter__
        self._resp: _RetType = await self._coro
                               ^^^^^^^^^^^^^^^^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/client.py", line 624, in _request
        with timer:
             ^^^^^
      File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/helpers.py", line 713, in __exit__
        raise asyncio.TimeoutError from exc_val
    TimeoutError
    ```

<span class="nbx-badge nbx-badge--err">exit&nbsp;1</span> <span class="nbx-badge nbx-badge--neutral">34.968s</span>

---

## `nbx demo dcim devices create --dry-run --body-json {"name":"test"}`

=== ":material-console: Command"

    ```bash
    nbx demo dcim devices create --dry-run --body-json {"name":"test"}
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo dcim devices create --dry-run --body-json {"name":"test"}
    ```

    ```text
            Dry Run Preview        
    ┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
    ┃ Field  ┃ Value              ┃
    ┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
    │ Method │ POST               │
    │ Path   │ /api/dcim/devices/ │
    │ Body   │ {                  │
    │        │   "name": "test"   │
    │        │ }                  │
    └────────┴────────────────────┘
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.963s</span>

---
