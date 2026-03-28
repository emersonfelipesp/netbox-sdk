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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.999s</span>

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.589s</span>

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.870s</span>

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.904s</span>

---
