# Command Examples

!!! info "Machine-generated"
    This page is automatically generated from CLI captures.
    Last updated: `2026-03-20T23:01:55.623452+00:00`

??? note "Generation metadata"
    | Key | Value |
    |-----|-------|
    | Profile | `demo` |
    | NetBox URL | `https://demo.netbox.dev` |
    | Token configured | `False` |
    | Commands captured | `25` |

---

## Top-level

### `nbx --help`

=== ":material-console: Command"

    ```bash
    nbx --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root [OPTIONS] COMMAND [ARGS]...                                        
                                                                                    
     NetBox API-first CLI/TUI. Dynamic command form: nbx <group> <resource>         
     <action>                                                                       
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --help          Show this message and exit.                                  │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ╭─ Commands ───────────────────────────────────────────────────────────────────╮
    │ init                                                                         │
    │ config                                                                       │
    │ groups                                                                       │
    │ resources                                                                    │
    │ ops                                                                          │
    │ call                                                                         │
    │ tui                                                                          │
    │ docs            Generate reference documentation (captured CLI               │
    │                 input/output).                                               │
    │ demo            NetBox demo.netbox.dev profile and command tree.             │
    │ circuits        OpenAPI app group: circuits                                  │
    │ core            OpenAPI app group: core                                      │
    │ dcim            OpenAPI app group: dcim                                      │
    │ extras          OpenAPI app group: extras                                    │
    │ ipam            OpenAPI app group: ipam                                      │
    │ plugins         OpenAPI app group: plugins                                   │
    │ tenancy         OpenAPI app group: tenancy                                   │
    │ users           OpenAPI app group: users                                     │
    │ virtualization  OpenAPI app group: virtualization                            │
    │ vpn             OpenAPI app group: vpn                                       │
    │ wireless        OpenAPI app group: wireless                                  │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.579s</span>

---

### `nbx init --help`

=== ":material-console: Command"

    ```bash
    nbx init --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root init [OPTIONS]                                                     
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ *  --base-url            TEXT   NetBox base URL, e.g.                        │
    │                                 https://netbox.example.com                   │
    │                                 [required]                                   │
    │ *  --token-key           TEXT   NetBox API token key [required]              │
    │ *  --token-secret        TEXT   NetBox API token secret [required]           │
    │    --timeout             FLOAT  HTTP timeout in seconds [default: 30.0]      │
    │    --help                       Show this message and exit.                  │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.349s</span>

---

### `nbx config --help`

=== ":material-console: Command"

    ```bash
    nbx config --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root config [OPTIONS]                                                   
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --show-token          Include API token in output                            │
    │ --help                Show this message and exit.                            │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.467s</span>

---

### `nbx groups --help`

=== ":material-console: Command"

    ```bash
    nbx groups --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root groups [OPTIONS]                                                   
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --help          Show this message and exit.                                  │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.713s</span>

---

### `nbx resources --help`

=== ":material-console: Command"

    ```bash
    nbx resources --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root resources [OPTIONS] GROUP                                          
                                                                                    
    ╭─ Arguments ──────────────────────────────────────────────────────────────────╮
    │ *    group      TEXT  OpenAPI app group, e.g. dcim [required]                │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --help          Show this message and exit.                                  │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.467s</span>

---

### `nbx ops --help`

=== ":material-console: Command"

    ```bash
    nbx ops --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root ops [OPTIONS] GROUP RESOURCE                                       
                                                                                    
    ╭─ Arguments ──────────────────────────────────────────────────────────────────╮
    │ *    group         TEXT  [required]                                          │
    │ *    resource      TEXT  [required]                                          │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --help          Show this message and exit.                                  │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.512s</span>

---

### `nbx call --help`

=== ":material-console: Command"

    ```bash
    nbx call --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root call [OPTIONS] METHOD PATH                                         
                                                                                    
    ╭─ Arguments ──────────────────────────────────────────────────────────────────╮
    │ *    method      TEXT  [required]                                            │
    │ *    path        TEXT  [required]                                            │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --query      -q      TEXT  Query parameter key=value                         │
    │ --body-json          TEXT  Inline JSON request body                          │
    │ --body-file          TEXT  Path to JSON request body file                    │
    │ --json                     Output raw JSON                                   │
    │ --yaml                     Output YAML                                       │
    │ --help                     Show this message and exit.                       │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.291s</span>

---

### `nbx tui --help`

=== ":material-console: Command"

    ```bash
    nbx tui --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root tui [OPTIONS]                                                      
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --theme          Theme selector. Use '--theme' to list available themes or   │
    │                  '--theme <name>' to launch with one.                        │
    │ --help           Show this message and exit.                                 │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.444s</span>

---

### `nbx tui --theme`

=== ":material-console: Command"

    ```bash
    nbx tui --theme
    ```

=== ":material-text-box-outline: Output"

    ```text
    Available themes:
    - default
    - dracula
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.280s</span>

---

### `nbx docs --help`

=== ":material-console: Command"

    ```bash
    nbx docs --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root docs [OPTIONS] COMMAND [ARGS]...                                   
                                                                                    
     Generate reference documentation (captured CLI input/output).                  
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --help          Show this message and exit.                                  │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ╭─ Commands ───────────────────────────────────────────────────────────────────╮
    │ generate-capture  Capture every nbx command (input + output) and write       │
    │                   docs/generated/nbx-command-capture.md.                     │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.715s</span>

---

### `nbx docs generate-capture --help`

=== ":material-console: Command"

    ```bash
    nbx docs generate-capture --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root docs generate-capture [OPTIONS]                                    
                                                                                    
     Capture every nbx command (input + output) and write                           
     docs/generated/nbx-command-capture.md.                                         
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --output     -o      PATH     Markdown destination. Default:                 │
    │                               <repo>/docs/generated/nbx-command-capture.md   │
    │ --raw-dir            PATH     Raw JSON artifacts directory. Default:         │
    │                               <repo>/docs/generated/raw/                     │
    │ --max-lines          INTEGER  Max lines per command output in the Markdown.  │
    │                               [default: 200]                                 │
    │ --max-chars          INTEGER  Max chars per command output in the Markdown.  │
    │                               [default: 120000]                              │
    │ --help                        Show this message and exit.                    │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.678s</span>

---


## Demo profile

### `nbx demo --help`

=== ":material-console: Command"

    ```bash
    nbx demo --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root demo [OPTIONS] COMMAND [ARGS]...                                   
                                                                                    
     NetBox demo.netbox.dev profile and command tree.                               
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --token-key           TEXT  Set the demo profile directly without            │
    │                             Playwright.                                      │
    │ --token-secret        TEXT  Set the demo profile directly without            │
    │                             Playwright.                                      │
    │ --help                      Show this message and exit.                      │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ╭─ Commands ───────────────────────────────────────────────────────────────────╮
    │ init            Authenticate with demo.netbox.dev via Playwright and save    │
    │                 the demo profile.                                            │
    │ config                                                                       │
    │ reset                                                                        │
    │ tui                                                                          │
    │ circuits        OpenAPI app group: circuits                                  │
    │ core            OpenAPI app group: core                                      │
    │ dcim            OpenAPI app group: dcim                                      │
    │ extras          OpenAPI app group: extras                                    │
    │ ipam            OpenAPI app group: ipam                                      │
    │ plugins         OpenAPI app group: plugins                                   │
    │ tenancy         OpenAPI app group: tenancy                                   │
    │ users           OpenAPI app group: users                                     │
    │ virtualization  OpenAPI app group: virtualization                            │
    │ vpn             OpenAPI app group: vpn                                       │
    │ wireless        OpenAPI app group: wireless                                  │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.346s</span>

---

### `nbx demo init --help`

=== ":material-console: Command"

    ```bash
    nbx demo init --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root demo init [OPTIONS]                                                
                                                                                    
     Authenticate with demo.netbox.dev via Playwright and save the demo profile.    
                                                                                    
     Pass ``--username`` and ``--password`` for non-interactive / CI use.           
     Alternatively, supply an existing token directly with ``--token-key`` and      
     ``--token-secret`` to skip Playwright entirely.                                
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --headless          --headed          Run Playwright headless (default). Use │
    │                                       --headed only when a desktop/X server  │
    │                                       is available.                          │
    │                                       [default: headless]                    │
    │ --username      -u              TEXT  demo.netbox.dev username. Prompted     │
    │                                       interactively when omitted.            │
    │ --password      -p              TEXT  demo.netbox.dev password. Prompted     │
    │                                       interactively when omitted.            │
    │ --token-key                     TEXT  Set the demo profile directly without  │
    │                                       Playwright (requires --token-secret).  │
    │ --token-secret                  TEXT  Set the demo profile directly without  │
    │                                       Playwright (requires --token-key).     │
    │ --help                                Show this message and exit.            │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.305s</span>

---

### `nbx demo config --help`

=== ":material-console: Command"

    ```bash
    nbx demo config --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root demo config [OPTIONS]                                              
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --show-token          Include API token in output                            │
    │ --help                Show this message and exit.                            │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.433s</span>

---


## Schema Discovery

### `nbx groups`

=== ":material-console: Command"

    ```bash
    nbx groups
    ```

=== ":material-text-box-outline: Output"

    ```text
    circuits
    core
    dcim
    extras
    ipam
    plugins
    tenancy
    users
    virtualization
    vpn
    wireless
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.359s</span>

---

### `nbx resources dcim`

=== ":material-console: Command"

    ```bash
    nbx resources dcim
    ```

=== ":material-text-box-outline: Output"

    ```text
    cable-terminations
    cables
    connected-device
    console-port-templates
    console-ports
    console-server-port-templates
    console-server-ports
    device-bay-templates
    device-bays
    device-roles
    device-types
    devices
    front-port-templates
    front-ports
    interface-templates
    interfaces
    inventory-item-roles
    inventory-item-templates
    inventory-items
    locations
    mac-addresses
    manufacturers
    module-bay-templates
    module-bays
    module-type-profiles
    module-types
    modules
    platforms
    power-feeds
    power-outlet-templates
    power-outlets
    power-panels
    power-port-templates
    power-ports
    rack-reservations
    rack-roles
    rack-types
    racks
    rear-port-templates
    rear-ports
    regions
    site-groups
    sites
    virtual-chassis
    virtual-device-contexts
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.224s</span>

---

### `nbx ops dcim devices`

=== ":material-console: Command"

    ```bash
    nbx ops dcim devices
    ```

=== ":material-text-box-outline: Output"

    ```text
                                      dcim/devices                                  
    ┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Method ┃ Path                             ┃ Operation ID                     ┃
    ┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │ DELETE │ /api/dcim/devices/               │ dcim_devices_bulk_destroy        │
    │ GET    │ /api/dcim/devices/               │ dcim_devices_list                │
    │ PATCH  │ /api/dcim/devices/               │ dcim_devices_bulk_partial_update │
    │ POST   │ /api/dcim/devices/               │ dcim_devices_create              │
    │ PUT    │ /api/dcim/devices/               │ dcim_devices_bulk_update         │
    │ DELETE │ /api/dcim/devices/{id}/          │ dcim_devices_destroy             │
    │ GET    │ /api/dcim/devices/{id}/          │ dcim_devices_retrieve            │
    │ PATCH  │ /api/dcim/devices/{id}/          │ dcim_devices_partial_update      │
    │ PUT    │ /api/dcim/devices/{id}/          │ dcim_devices_update              │
    │ POST   │ /api/dcim/devices/{id}/render-c… │ dcim_devices_render_config_crea… │
    └────────┴──────────────────────────────────┴──────────────────────────────────┘
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.241s</span>

---

### `nbx resources ipam`

=== ":material-console: Command"

    ```bash
    nbx resources ipam
    ```

=== ":material-text-box-outline: Output"

    ```text
    aggregates
    asn-ranges
    asns
    fhrp-group-assignments
    fhrp-groups
    ip-addresses
    ip-ranges
    prefixes
    rirs
    roles
    route-targets
    service-templates
    services
    vlan-groups
    vlan-translation-policies
    vlan-translation-rules
    vlans
    vrfs
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.374s</span>

---


## Dynamic Commands

### `nbx dcim --help`

=== ":material-console: Command"

    ```bash
    nbx dcim --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root dcim [OPTIONS] COMMAND [ARGS]...                                   
                                                                                    
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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.264s</span>

---

### `nbx dcim devices --help`

=== ":material-console: Command"

    ```bash
    nbx dcim devices --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root dcim devices [OPTIONS] COMMAND [ARGS]...                           
                                                                                    
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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.230s</span>

---

### `nbx dcim devices list --help`

=== ":material-console: Command"

    ```bash
    nbx dcim devices list --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root dcim devices list [OPTIONS]                                        
                                                                                    
     list dcim/devices                                                              
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --id                 INTEGER  Object ID for detail operations                │
    │ --query      -q      TEXT     Query parameter key=value                      │
    │ --body-json          TEXT     Inline JSON request body                       │
    │ --body-file          TEXT     Path to JSON request body file                 │
    │ --json                        Output raw JSON                                │
    │ --yaml                        Output YAML                                    │
    │ --help                        Show this message and exit.                    │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.392s</span>

---

### `nbx ipam prefixes --help`

=== ":material-console: Command"

    ```bash
    nbx ipam prefixes --help
    ```

=== ":material-text-box-outline: Output"

    ```text
                                                                                    
     Usage: root ipam prefixes [OPTIONS] COMMAND [ARGS]...                          
                                                                                    
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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.214s</span>

---


## Live API — demo.netbox.dev

### `nbx demo dcim devices list`

=== ":material-console: Command"

    ```bash
    nbx demo dcim devices list
    ```

=== ":material-text-box-outline: Output"

    ```text
    Status: 200
                                      79 result(s)                                  
    ┏━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┓
    ┃ ID  ┃ Name     ┃ Display  ┃ Status ┃ Role     ┃ Site    ┃ Location ┃ Tenant  ┃
    ┡━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━┩
    │ 27  │ dmi01-ak │ dmi01-ak │ Active │ PDU (ID  │ DM-Akro │ —        │ Dunder- │
    │     │ ron-pdu0 │ ron-pdu0 │        │ 5)       │ n (ID   │          │ Mifflin │
    │     │ 1        │ 1        │        │          │ 2)      │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 1   │ dmi01-ak │ dmi01-ak │ Active │ Router   │ DM-Akro │ —        │ Dunder- │
    │     │ ron-rtr0 │ ron-rtr0 │        │ (ID 1)   │ n (ID   │          │ Mifflin │
    │     │ 1        │ 1        │        │          │ 2)      │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 14  │ dmi01-ak │ dmi01-ak │ Active │ Access   │ DM-Akro │ —        │ Dunder- │
    │     │ ron-sw01 │ ron-sw01 │        │ Switch   │ n (ID   │          │ Mifflin │
    │     │          │          │        │ (ID 4)   │ 2)      │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 34  │ dmi01-al │ dmi01-al │ Active │ PDU (ID  │ DM-Alba │ —        │ Dunder- │
    │     │ bany-pdu │ bany-pdu │        │ 5)       │ ny (ID  │          │ Mifflin │
    │     │ 01       │ 01       │        │          │ 3)      │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 2   │ dmi01-al │ dmi01-al │ Active │ Router   │ DM-Alba │ —        │ Dunder- │
    │     │ bany-rtr │ bany-rtr │        │ (ID 1)   │ ny (ID  │          │ Mifflin │
    │     │ 01       │ 01       │        │          │ 3)      │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 15  │ dmi01-al │ dmi01-al │ Active │ Access   │ DM-Alba │ —        │ Dunder- │
    │     │ bany-sw0 │ bany-sw0 │        │ Switch   │ ny (ID  │          │ Mifflin │
    │     │ 1        │ 1        │        │ (ID 4)   │ 3)      │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 35  │ dmi01-bi │ dmi01-bi │ Active │ PDU (ID  │ DM-Bing │ —        │ Dunder- │
    │     │ nghamton │ nghamton │        │ 5)       │ hamton  │          │ Mifflin │
    │     │ -pdu01   │ -pdu01   │        │          │ (ID 4)  │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 3   │ dmi01-bi │ dmi01-bi │ Active │ Router   │ DM-Bing │ —        │ Dunder- │
    │     │ nghamton │ nghamton │        │ (ID 1)   │ hamton  │          │ Mifflin │
    │     │ -rtr01   │ -rtr01   │        │          │ (ID 4)  │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 16  │ dmi01-bi │ dmi01-bi │ Active │ Access   │ DM-Bing │ —        │ Dunder- │
    │     │ nghamton │ nghamton │        │ Switch   │ hamton  │          │ Mifflin │
    │     │ -sw01    │ -sw01    │        │ (ID 4)   │ (ID 4)  │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 36  │ dmi01-bu │ dmi01-bu │ Active │ PDU (ID  │ DM-Buff │ —        │ Dunder- │
    │     │ ffalo-pd │ ffalo-pd │        │ 5)       │ alo (ID │          │ Mifflin │
    │     │ u01      │ u01      │        │          │ 5)      │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 4   │ dmi01-bu │ dmi01-bu │ Active │ Router   │ DM-Buff │ —        │ Dunder- │
    │     │ ffalo-rt │ ffalo-rt │        │ (ID 1)   │ alo (ID │          │ Mifflin │
    │     │ r01      │ r01      │        │          │ 5)      │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 17  │ dmi01-bu │ dmi01-bu │ Active │ Access   │ DM-Buff │ —        │ Dunder- │
    │     │ ffalo-sw │ ffalo-sw │        │ Switch   │ alo (ID │          │ Mifflin │
    │     │ 01       │ 01       │        │ (ID 4)   │ 5)      │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 37  │ dmi01-ca │ dmi01-ca │ Active │ PDU (ID  │ DM-Camd │ —        │ Dunder- │
    │     │ mden-pdu │ mden-pdu │        │ 5)       │ en (ID  │          │ Mifflin │
    │     │ 01       │ 01       │        │          │ 6)      │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 5   │ dmi01-ca │ dmi01-ca │ Active │ Router   │ DM-Camd │ —        │ Dunder- │
    │     │ mden-rtr │ mden-rtr │        │ (ID 1)   │ en (ID  │          │ Mifflin │
    │     │ 01       │ 01       │        │          │ 6)      │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 18  │ dmi01-ca │ dmi01-ca │ Active │ Access   │ DM-Camd │ —        │ Dunder- │
    │     │ mden-sw0 │ mden-sw0 │        │ Switch   │ en (ID  │          │ Mifflin │
    │     │ 1        │ 1        │        │ (ID 4)   │ 6)      │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 38  │ dmi01-na │ dmi01-na │ Active │ PDU (ID  │ DM-Nash │ —        │ Dunder- │
    │     │ shua-pdu │ shua-pdu │        │ 5)       │ ua (ID  │          │ Mifflin │
    │     │ 01       │ 01       │        │          │ 7)      │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 6   │ dmi01-na │ dmi01-na │ Active │ Router   │ DM-Nash │ —        │ Dunder- │
    │     │ shua-rtr │ shua-rtr │        │ (ID 1)   │ ua (ID  │          │ Mifflin │
    │     │ 01       │ 01       │        │          │ 7)      │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 19  │ dmi01-na │ dmi01-na │ Active │ Access   │ DM-Nash │ —        │ Dunder- │
    │     │ shua-sw0 │ shua-sw0 │        │ Switch   │ ua (ID  │          │ Mifflin │
    │     │ 1        │ 1        │        │ (ID 4)   │ 7)      │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 39  │ dmi01-pi │ dmi01-pi │ Active │ PDU (ID  │ DM-Pitt │ —        │ Dunder- │
    │     │ ttsfield │ ttsfield │        │ 5)       │ sfield  │          │ Mifflin │
    │     │ -pdu01   │ -pdu01   │        │          │ (ID 8)  │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 7   │ dmi01-pi │ dmi01-pi │ Active │ Router   │ DM-Pitt │ —        │ Dunder- │
    │     │ ttsfield │ ttsfield │        │ (ID 1)   │ sfield  │          │ Mifflin │
    │     │ -rtr01   │ -rtr01   │        │          │ (ID 8)  │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 20  │ dmi01-pi │ dmi01-pi │ Active │ Access   │ DM-Pitt │ —        │ Dunder- │
    │     │ ttsfield │ ttsfield │        │ Switch   │ sfield  │          │ Mifflin │
    │     │ -sw01    │ -sw01    │        │ (ID 4)   │ (ID 8)  │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 40  │ dmi01-ro │ dmi01-ro │ Active │ PDU (ID  │ DM-Roch │ —        │ Dunder- │
    │     │ chester- │ chester- │        │ 5)       │ ester   │          │ Mifflin │
    │     │ pdu01    │ pdu01    │        │          │ (ID 9)  │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 8   │ dmi01-ro │ dmi01-ro │ Active │ Router   │ DM-Roch │ —        │ Dunder- │
    │     │ chester- │ chester- │        │ (ID 1)   │ ester   │          │ Mifflin │
    │     │ rtr01    │ rtr01    │        │          │ (ID 9)  │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 21  │ dmi01-ro │ dmi01-ro │ Active │ Access   │ DM-Roch │ —        │ Dunder- │
    │     │ chster-s │ chster-s │        │ Switch   │ ester   │          │ Mifflin │
    │     │ w01      │ w01      │        │ (ID 4)   │ (ID 9)  │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 41  │ dmi01-sc │ dmi01-sc │ Active │ PDU (ID  │ DM-Scra │ —        │ Dunder- │
    │     │ ranton-p │ ranton-p │        │ 5)       │ nton    │          │ Mifflin │
    │     │ du01     │ du01     │        │          │ (ID 10) │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 9   │ dmi01-sc │ dmi01-sc │ Active │ Router   │ DM-Scra │ —        │ Dunder- │
    │     │ ranton-r │ ranton-r │        │ (ID 1)   │ nton    │          │ Mifflin │
    │     │ tr01     │ tr01     │        │          │ (ID 10) │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 22  │ dmi01-sc │ dmi01-sc │ Active │ Access   │ DM-Scra │ —        │ Dunder- │
    │     │ ranton-s │ ranton-s │        │ Switch   │ nton    │          │ Mifflin │
    │     │ w01      │ w01      │        │ (ID 4)   │ (ID 10) │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 42  │ dmi01-st │ dmi01-st │ Active │ PDU (ID  │ DM-Stam │ —        │ Dunder- │
    │     │ amford-p │ amford-p │        │ 5)       │ ford    │          │ Mifflin │
    │     │ du01     │ du01     │        │          │ (ID 11) │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 10  │ dmi01-st │ dmi01-st │ Active │ Router   │ DM-Stam │ —        │ Dunder- │
    │     │ amford-r │ amford-r │        │ (ID 1)   │ ford    │          │ Mifflin │
    │     │ tr01     │ tr01     │        │          │ (ID 11) │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 23  │ dmi01-st │ dmi01-st │ Active │ Access   │ DM-Stam │ —        │ Dunder- │
    │     │ amford-s │ amford-s │        │ Switch   │ ford    │          │ Mifflin │
    │     │ w01      │ w01      │        │ (ID 4)   │ (ID 11) │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 43  │ dmi01-sy │ dmi01-sy │ Active │ PDU (ID  │ DM-Syra │ —        │ Dunder- │
    │     │ racuse-p │ racuse-p │        │ 5)       │ cuse    │          │ Mifflin │
    │     │ du01     │ du01     │        │          │ (ID 12) │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 11  │ dmi01-sy │ dmi01-sy │ Active │ Router   │ DM-Syra │ —        │ Dunder- │
    │     │ racuse-r │ racuse-r │        │ (ID 1)   │ cuse    │          │ Mifflin │
    │     │ tr01     │ tr01     │        │          │ (ID 12) │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 24  │ dmi01-sy │ dmi01-sy │ Active │ Access   │ DM-Syra │ —        │ Dunder- │
    │     │ racuse-s │ racuse-s │        │ Switch   │ cuse    │          │ Mifflin │
    │     │ w01      │ w01      │        │ (ID 4)   │ (ID 12) │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 44  │ dmi01-ut │ dmi01-ut │ Active │ PDU (ID  │ DM-Utic │ —        │ Dunder- │
    │     │ ica-pdu0 │ ica-pdu0 │        │ 5)       │ a (ID   │          │ Mifflin │
    │     │ 1        │ 1        │        │          │ 13)     │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 12  │ dmi01-ut │ dmi01-ut │ Active │ Router   │ DM-Utic │ —        │ Dunder- │
    │     │ ica-rtr0 │ ica-rtr0 │        │ (ID 1)   │ a (ID   │          │ Mifflin │
    │     │ 1        │ 1        │        │          │ 13)     │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 25  │ dmi01-ut │ dmi01-ut │ Active │ Access   │ DM-Utic │ —        │ Dunder- │
    │     │ ica-sw01 │ ica-sw01 │        │ Switch   │ a (ID   │          │ Mifflin │
    │     │          │          │        │ (ID 4)   │ 13)     │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 45  │ dmi01-yo │ dmi01-yo │ Active │ PDU (ID  │ DM-Yonk │ —        │ Dunder- │
    │     │ nkers-pd │ nkers-pd │        │ 5)       │ ers (ID │          │ Mifflin │
    │     │ u01      │ u01      │        │          │ 14)     │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 13  │ dmi01-yo │ dmi01-yo │ Active │ Router   │ DM-Yonk │ —        │ Dunder- │
    │     │ nkers-rt │ nkers-rt │        │ (ID 1)   │ ers (ID │          │ Mifflin │
    │     │ r01      │ r01      │        │          │ 14)     │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 26  │ dmi01-yo │ dmi01-yo │ Active │ Access   │ DM-Yonk │ —        │ Dunder- │
    │     │ nkers-sw │ nkers-sw │        │ Switch   │ ers (ID │          │ Mifflin │
    │     │ 01       │ 01       │        │ (ID 4)   │ 14)     │          │ , Inc.  │
    │     │          │          │        │          │         │          │ (ID 5)  │
    │ 107 │ kphb     │ kphb     │ Active │ Core     │ Butler  │ —        │ —       │
    │     │          │          │        │ Switch   │ Communi │          │         │
    │     │          │          │        │ (ID 2)   │ cations │          │         │
    │     │          │          │        │          │  (ID    │          │         │
    │     │          │          │        │          │ 24)     │          │         │
    │ 96  │ ncsu-cor │ ncsu-cor │ Active │ Core     │ MDF (ID │ Row 1    │ NC      │
    │     │ eswitch1 │ eswitch1 │        │ Switch   │ 21)     │ (ID 1)   │ State   │
    │     │          │          │        │ (ID 2)   │         │          │ Univers │
    │     │          │          │        │          │         │          │ ity (ID │
    │     │          │          │        │          │         │          │ 13)     │
    │ 97  │ ncsu-cor │ ncsu-cor │ Active │ Core     │ MDF (ID │ Row 1    │ NC      │
    │     │ eswitch2 │ eswitch2 │        │ Switch   │ 21)     │ (ID 1)   │ State   │
    │     │          │          │        │ (ID 2)   │         │          │ Univers │
    │     │          │          │        │          │         │          │ ity (ID │
    │     │          │          │        │          │         │          │ 13)     │
    │ 94  │ ncsu117- │ ncsu117- │ Active │ Distribu │ D. S.   │ —        │ NC      │
    │     │ distswit │ distswit │        │ tion     │ Weaver  │          │ State   │
    │     │ ch1      │ ch1      │        │ Switch   │ Labs    │          │ Univers │
    │     │          │          │        │ (ID 3)   │ (ID 22) │          │ ity (ID │
    │     │          │          │        │          │         │          │ 13)     │
    │ 95  │ ncsu118- │ ncsu118- │ Active │ Distribu │ Grinnel │ —        │ NC      │
    │     │ distswit │ distswit │        │ tion     │ ls Lab  │          │ State   │
    │     │ ch1      │ ch1      │        │ Switch   │ (ID 23) │          │ Univers │
    │     │          │          │        │ (ID 3)   │         │          │ ity (ID │
    │     │          │          │        │          │         │          │ 13)     │
    │ 93  │ ncsu128- │ ncsu128- │ Active │ Distribu │ Butler  │ —        │ NC      │
    │     │ distswit │ distswit │        │ tion     │ Communi │          │ State   │
    │     │ ch1      │ ch1      │        │ Switch   │ cations │          │ Univers │
    │     │          │          │        │ (ID 3)   │  (ID    │          │ ity (ID │
    │     │          │          │        │          │ 24)     │          │ 13)     │
    │ 88  │ PP:B117  │ PP:B117  │ Active │ Patch    │ MDF (ID │ —        │ NC      │
    │     │          │          │        │ Panel    │ 21)     │          │ State   │
    │     │          │          │        │ (ID 6)   │         │          │ Univers │
    │     │          │          │        │          │         │          │ ity (ID │
    │     │          │          │        │          │         │          │ 13)     │
    │ 89  │ PP:B118  │ PP:B118  │ Active │ Patch    │ MDF (ID │ —        │ NC      │
    │     │          │          │        │ Panel    │ 21)     │          │ State   │
    │     │          │          │        │ (ID 6)   │         │          │ Univers │
    │     │          │          │        │          │         │          │ ity (ID │
    │     │          │          │        │          │         │          │ 13)     │
    │ 87  │ PP:B128  │ PP:B128  │ Active │ Patch    │ MDF (ID │ —        │ NC      │
    │     │          │          │        │ Panel    │ 21)     │          │ State   │
    │     │          │          │        │ (ID 6)   │         │          │ Univers │
    │     │          │          │        │          │         │          │ ity (ID │
    │     │          │          │        │          │         │          │ 13)     │
    │ 90  │ PP:MDF   │ PP:MDF   │ Active │ Patch    │ Butler  │ —        │ NC      │
    │     │          │          │        │ Panel    │ Communi │          │ State   │
    │     │          │          │        │ (ID 6)   │ cations │          │ Univers │
    │     │          │          │        │          │  (ID    │          │ ity (ID │
    │     │          │          │        │          │ 24)     │          │ 13)     │
    │ 91  │ PP:MDF   │ PP:MDF   │ Active │ Patch    │ D. S.   │ —        │ NC      │
    │     │          │          │        │ Panel    │ Weaver  │          │ State   │
    │     │          │          │        │ (ID 6)   │ Labs    │          │ Univers │
    │     │          │          │        │          │ (ID 22) │          │ ity (ID │
    │     │          │          │        │          │         │          │ 13)     │
    └─────┴──────────┴──────────┴────────┴──────────┴─────────┴──────────┴─────────┘
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">2.372s</span>

!!! warning "Truncated"
    Output was truncated. Full text is in `docs/generated/raw/`.

---

### `nbx demo ipam prefixes list`

=== ":material-console: Command"

    ```bash
    nbx demo ipam prefixes list
    ```

=== ":material-text-box-outline: Output"

    ```text
    Status: 200
                                      96 result(s)                                  
    ┏━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┓
    ┃ ID ┃ Display   ┃ Status    ┃ Role      ┃ Prefix     ┃ VLAN      ┃ Tenant     ┃
    ┡━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━┩
    │ 1  │ 10.112.0. │ Container │ —         │ 10.112.0.0 │ —         │ Dunder-Mif │
    │    │ 0/15      │           │           │ /15        │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 2  │ 10.112.0. │ Container │ —         │ 10.112.0.0 │ —         │ Dunder-Mif │
    │    │ 0/17      │           │           │ /17        │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 3  │ 10.112.12 │ Container │ —         │ 10.112.128 │ —         │ Dunder-Mif │
    │    │ 8.0/17    │           │           │ .0/17      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 60 │ 10.112.12 │ Container │ —         │ 10.112.128 │ —         │ Dunder-Mif │
    │    │ 8.0/22    │           │           │ .0/22      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 7  │ 10.112.12 │ Active    │ Managemen │ 10.112.128 │ —         │ Dunder-Mif │
    │    │ 8.0/28    │           │ t (ID 4)  │ .0/28      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 8  │ 10.112.12 │ Active    │ Access -  │ 10.112.129 │ Data      │ Dunder-Mif │
    │    │ 9.0/24    │           │ Data (ID  │ .0/24      │ (100) (ID │ flin, Inc. │
    │    │           │           │ 1)        │            │ 1)        │ (ID 5)     │
    │ 9  │ 10.112.13 │ Active    │ Access -  │ 10.112.130 │ Voice     │ Dunder-Mif │
    │    │ 0.0/24    │           │ Voice (ID │ .0/24      │ (200) (ID │ flin, Inc. │
    │    │           │           │ 2)        │            │ 2)        │ (ID 5)     │
    │ 10 │ 10.112.13 │ Active    │ Access -  │ 10.112.131 │ Wireless  │ Dunder-Mif │
    │    │ 1.0/24    │           │ Wireless  │ .0/24      │ (300) (ID │ flin, Inc. │
    │    │           │           │ (ID 3)    │            │ 27)       │ (ID 5)     │
    │ 61 │ 10.112.13 │ Container │ —         │ 10.112.132 │ —         │ Dunder-Mif │
    │    │ 2.0/22    │           │           │ .0/22      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 11 │ 10.112.13 │ Active    │ Managemen │ 10.112.132 │ —         │ Dunder-Mif │
    │    │ 2.0/28    │           │ t (ID 4)  │ .0/28      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 12 │ 10.112.13 │ Active    │ Access -  │ 10.112.133 │ Data      │ Dunder-Mif │
    │    │ 3.0/24    │           │ Data (ID  │ .0/24      │ (100) (ID │ flin, Inc. │
    │    │           │           │ 1)        │            │ 3)        │ (ID 5)     │
    │ 13 │ 10.112.13 │ Active    │ Access -  │ 10.112.134 │ Voice     │ Dunder-Mif │
    │    │ 4.0/24    │           │ Voice (ID │ .0/24      │ (200) (ID │ flin, Inc. │
    │    │           │           │ 2)        │            │ 4)        │ (ID 5)     │
    │ 14 │ 10.112.13 │ Active    │ Access -  │ 10.112.135 │ Wireless  │ Dunder-Mif │
    │    │ 5.0/24    │           │ Wireless  │ .0/24      │ (300) (ID │ flin, Inc. │
    │    │           │           │ (ID 3)    │            │ 28)       │ (ID 5)     │
    │ 62 │ 10.112.13 │ Container │ —         │ 10.112.136 │ —         │ Dunder-Mif │
    │    │ 6.0/22    │           │           │ .0/22      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 15 │ 10.112.13 │ Active    │ Managemen │ 10.112.136 │ —         │ Dunder-Mif │
    │    │ 6.0/28    │           │ t (ID 4)  │ .0/28      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 16 │ 10.112.13 │ Active    │ Access -  │ 10.112.137 │ Data      │ Dunder-Mif │
    │    │ 7.0/24    │           │ Data (ID  │ .0/24      │ (100) (ID │ flin, Inc. │
    │    │           │           │ 1)        │            │ 5)        │ (ID 5)     │
    │ 17 │ 10.112.13 │ Active    │ Access -  │ 10.112.138 │ Voice     │ Dunder-Mif │
    │    │ 8.0/24    │           │ Voice (ID │ .0/24      │ (200) (ID │ flin, Inc. │
    │    │           │           │ 2)        │            │ 6)        │ (ID 5)     │
    │ 18 │ 10.112.13 │ Active    │ Access -  │ 10.112.139 │ Wireless  │ Dunder-Mif │
    │    │ 9.0/24    │           │ Wireless  │ .0/24      │ (300) (ID │ flin, Inc. │
    │    │           │           │ (ID 3)    │            │ 29)       │ (ID 5)     │
    │ 63 │ 10.112.14 │ Container │ —         │ 10.112.140 │ —         │ Dunder-Mif │
    │    │ 0.0/22    │           │           │ .0/22      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 19 │ 10.112.14 │ Active    │ Managemen │ 10.112.140 │ —         │ Dunder-Mif │
    │    │ 0.0/28    │           │ t (ID 4)  │ .0/28      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 20 │ 10.112.14 │ Active    │ Access -  │ 10.112.141 │ Data      │ Dunder-Mif │
    │    │ 1.0/24    │           │ Data (ID  │ .0/24      │ (100) (ID │ flin, Inc. │
    │    │           │           │ 1)        │            │ 7)        │ (ID 5)     │
    │ 21 │ 10.112.14 │ Active    │ Access -  │ 10.112.142 │ Voice     │ Dunder-Mif │
    │    │ 2.0/24    │           │ Voice (ID │ .0/24      │ (200) (ID │ flin, Inc. │
    │    │           │           │ 2)        │            │ 8)        │ (ID 5)     │
    │ 22 │ 10.112.14 │ Active    │ Access -  │ 10.112.143 │ Wireless  │ Dunder-Mif │
    │    │ 3.0/24    │           │ Wireless  │ .0/24      │ (300) (ID │ flin, Inc. │
    │    │           │           │ (ID 3)    │            │ 30)       │ (ID 5)     │
    │ 64 │ 10.112.14 │ Container │ —         │ 10.112.144 │ —         │ Dunder-Mif │
    │    │ 4.0/22    │           │           │ .0/22      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 23 │ 10.112.14 │ Active    │ Managemen │ 10.112.144 │ —         │ Dunder-Mif │
    │    │ 4.0/28    │           │ t (ID 4)  │ .0/28      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 24 │ 10.112.14 │ Active    │ Access -  │ 10.112.145 │ Data      │ Dunder-Mif │
    │    │ 5.0/24    │           │ Data (ID  │ .0/24      │ (100) (ID │ flin, Inc. │
    │    │           │           │ 1)        │            │ 9)        │ (ID 5)     │
    │ 25 │ 10.112.14 │ Active    │ Access -  │ 10.112.146 │ Voice     │ Dunder-Mif │
    │    │ 6.0/24    │           │ Voice (ID │ .0/24      │ (200) (ID │ flin, Inc. │
    │    │           │           │ 2)        │            │ 10)       │ (ID 5)     │
    │ 26 │ 10.112.14 │ Active    │ Access -  │ 10.112.147 │ Wireless  │ Dunder-Mif │
    │    │ 7.0/24    │           │ Wireless  │ .0/24      │ (300) (ID │ flin, Inc. │
    │    │           │           │ (ID 3)    │            │ 31)       │ (ID 5)     │
    │ 65 │ 10.112.14 │ Container │ —         │ 10.112.148 │ —         │ Dunder-Mif │
    │    │ 8.0/22    │           │           │ .0/22      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 27 │ 10.112.14 │ Active    │ Managemen │ 10.112.148 │ —         │ Dunder-Mif │
    │    │ 8.0/28    │           │ t (ID 4)  │ .0/28      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 28 │ 10.112.14 │ Active    │ Access -  │ 10.112.149 │ Data      │ Dunder-Mif │
    │    │ 9.0/24    │           │ Data (ID  │ .0/24      │ (100) (ID │ flin, Inc. │
    │    │           │           │ 1)        │            │ 11)       │ (ID 5)     │
    │ 29 │ 10.112.15 │ Active    │ Access -  │ 10.112.150 │ Voice     │ Dunder-Mif │
    │    │ 0.0/24    │           │ Voice (ID │ .0/24      │ (200) (ID │ flin, Inc. │
    │    │           │           │ 2)        │            │ 12)       │ (ID 5)     │
    │ 30 │ 10.112.15 │ Active    │ Access -  │ 10.112.151 │ Wireless  │ Dunder-Mif │
    │    │ 1.0/24    │           │ Wireless  │ .0/24      │ (300) (ID │ flin, Inc. │
    │    │           │           │ (ID 3)    │            │ 32)       │ (ID 5)     │
    │ 66 │ 10.112.15 │ Container │ —         │ 10.112.152 │ —         │ Dunder-Mif │
    │    │ 2.0/22    │           │           │ .0/22      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 31 │ 10.112.15 │ Active    │ Managemen │ 10.112.152 │ —         │ Dunder-Mif │
    │    │ 2.0/28    │           │ t (ID 4)  │ .0/28      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 32 │ 10.112.15 │ Active    │ Access -  │ 10.112.153 │ Data      │ Dunder-Mif │
    │    │ 3.0/24    │           │ Data (ID  │ .0/24      │ (100) (ID │ flin, Inc. │
    │    │           │           │ 1)        │            │ 13)       │ (ID 5)     │
    │ 33 │ 10.112.15 │ Active    │ Access -  │ 10.112.154 │ Voice     │ Dunder-Mif │
    │    │ 4.0/24    │           │ Voice (ID │ .0/24      │ (200) (ID │ flin, Inc. │
    │    │           │           │ 2)        │            │ 14)       │ (ID 5)     │
    │ 34 │ 10.112.15 │ Active    │ Access -  │ 10.112.155 │ Wireless  │ Dunder-Mif │
    │    │ 5.0/24    │           │ Wireless  │ .0/24      │ (300) (ID │ flin, Inc. │
    │    │           │           │ (ID 3)    │            │ 33)       │ (ID 5)     │
    │ 67 │ 10.112.15 │ Container │ —         │ 10.112.156 │ —         │ Dunder-Mif │
    │    │ 6.0/22    │           │           │ .0/22      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 35 │ 10.112.15 │ Active    │ Managemen │ 10.112.156 │ —         │ Dunder-Mif │
    │    │ 6.0/28    │           │ t (ID 4)  │ .0/28      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 36 │ 10.112.15 │ Active    │ Access -  │ 10.112.157 │ Data      │ Dunder-Mif │
    │    │ 7.0/24    │           │ Data (ID  │ .0/24      │ (100) (ID │ flin, Inc. │
    │    │           │           │ 1)        │            │ 15)       │ (ID 5)     │
    │ 37 │ 10.112.15 │ Active    │ Access -  │ 10.112.158 │ Voice     │ Dunder-Mif │
    │    │ 8.0/24    │           │ Voice (ID │ .0/24      │ (200) (ID │ flin, Inc. │
    │    │           │           │ 2)        │            │ 16)       │ (ID 5)     │
    │ 38 │ 10.112.15 │ Active    │ Access -  │ 10.112.159 │ Wireless  │ Dunder-Mif │
    │    │ 9.0/24    │           │ Wireless  │ .0/24      │ (300) (ID │ flin, Inc. │
    │    │           │           │ (ID 3)    │            │ 34)       │ (ID 5)     │
    │ 68 │ 10.112.16 │ Container │ —         │ 10.112.160 │ —         │ Dunder-Mif │
    │    │ 0.0/22    │           │           │ .0/22      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 39 │ 10.112.16 │ Active    │ Managemen │ 10.112.160 │ —         │ Dunder-Mif │
    │    │ 0.0/28    │           │ t (ID 4)  │ .0/28      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 40 │ 10.112.16 │ Active    │ Access -  │ 10.112.161 │ Data      │ Dunder-Mif │
    │    │ 1.0/24    │           │ Data (ID  │ .0/24      │ (100) (ID │ flin, Inc. │
    │    │           │           │ 1)        │            │ 17)       │ (ID 5)     │
    │ 41 │ 10.112.16 │ Active    │ Access -  │ 10.112.162 │ Voice     │ Dunder-Mif │
    │    │ 2.0/24    │           │ Voice (ID │ .0/24      │ (200) (ID │ flin, Inc. │
    │    │           │           │ 2)        │            │ 18)       │ (ID 5)     │
    │ 42 │ 10.112.16 │ Active    │ Access -  │ 10.112.163 │ Wireless  │ Dunder-Mif │
    │    │ 3.0/24    │           │ Wireless  │ .0/24      │ (300) (ID │ flin, Inc. │
    │    │           │           │ (ID 3)    │            │ 35)       │ (ID 5)     │
    │ 69 │ 10.112.16 │ Container │ —         │ 10.112.164 │ —         │ Dunder-Mif │
    │    │ 4.0/22    │           │           │ .0/22      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    │ 43 │ 10.112.16 │ Active    │ Managemen │ 10.112.164 │ —         │ Dunder-Mif │
    │    │ 4.0/28    │           │ t (ID 4)  │ .0/28      │           │ flin, Inc. │
    │    │           │           │           │            │           │ (ID 5)     │
    └────┴───────────┴───────────┴───────────┴────────────┴───────────┴────────────┘
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">2.188s</span>

---

### `nbx demo dcim sites list`

=== ":material-console: Command"

    ```bash
    nbx demo dcim sites list
    ```

=== ":material-text-box-outline: Output"

    ```text
    Status: 200
                                      28 result(s)                                  
    ┏━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓
    ┃ ID ┃ Name               ┃ Display             ┃ Status  ┃ Tenant             ┃
    ┡━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━┩
    │ 24 │ Butler             │ Butler              │ Active  │ NC State           │
    │    │ Communications     │ Communications      │         │ University (ID 13) │
    │ 22 │ D. S. Weaver Labs  │ D. S. Weaver Labs   │ Active  │ NC State           │
    │    │                    │                     │         │ University (ID 13) │
    │ 2  │ DM-Akron           │ DM-Akron            │ Active  │ Dunder-Mifflin,    │
    │    │                    │                     │         │ Inc. (ID 5)        │
    │ 3  │ DM-Albany          │ DM-Albany           │ Active  │ Dunder-Mifflin,    │
    │    │                    │                     │         │ Inc. (ID 5)        │
    │ 4  │ DM-Binghamton      │ DM-Binghamton       │ Active  │ Dunder-Mifflin,    │
    │    │                    │                     │         │ Inc. (ID 5)        │
    │ 5  │ DM-Buffalo         │ DM-Buffalo          │ Active  │ Dunder-Mifflin,    │
    │    │                    │                     │         │ Inc. (ID 5)        │
    │ 6  │ DM-Camden          │ DM-Camden           │ Active  │ Dunder-Mifflin,    │
    │    │                    │                     │         │ Inc. (ID 5)        │
    │ 7  │ DM-Nashua          │ DM-Nashua           │ Active  │ Dunder-Mifflin,    │
    │    │                    │                     │         │ Inc. (ID 5)        │
    │ 1  │ DM-NYC             │ DM-NYC              │ Retired │ Dunder-Mifflin,    │
    │    │                    │                     │         │ Inc. (ID 5)        │
    │ 8  │ DM-Pittsfield      │ DM-Pittsfield       │ Active  │ Dunder-Mifflin,    │
    │    │                    │                     │         │ Inc. (ID 5)        │
    │ 9  │ DM-Rochester       │ DM-Rochester        │ Active  │ Dunder-Mifflin,    │
    │    │                    │                     │         │ Inc. (ID 5)        │
    │ 10 │ DM-Scranton        │ DM-Scranton         │ Active  │ Dunder-Mifflin,    │
    │    │                    │                     │         │ Inc. (ID 5)        │
    │ 11 │ DM-Stamford        │ DM-Stamford         │ Active  │ Dunder-Mifflin,    │
    │    │                    │                     │         │ Inc. (ID 5)        │
    │ 12 │ DM-Syracuse        │ DM-Syracuse         │ Active  │ Dunder-Mifflin,    │
    │    │                    │                     │         │ Inc. (ID 5)        │
    │ 13 │ DM-Utica           │ DM-Utica            │ Active  │ Dunder-Mifflin,    │
    │    │                    │                     │         │ Inc. (ID 5)        │
    │ 14 │ DM-Yonkers         │ DM-Yonkers          │ Active  │ Dunder-Mifflin,    │
    │    │                    │                     │         │ Inc. (ID 5)        │
    │ 23 │ Grinnells Lab      │ Grinnells Lab       │ Active  │ NC State           │
    │    │                    │                     │         │ University (ID 13) │
    │ 15 │ JBB Branch 104     │ JBB Branch 104      │ Active  │ Jimbob's Banking & │
    │    │                    │                     │         │ Trust (ID 10)      │
    │ 16 │ JBB Branch 109     │ JBB Branch 109      │ Active  │ Jimbob's Banking & │
    │    │                    │                     │         │ Trust (ID 10)      │
    │ 17 │ JBB Branch 115     │ JBB Branch 115      │ Active  │ Jimbob's Banking & │
    │    │                    │                     │         │ Trust (ID 10)      │
    │ 18 │ JBB Branch 120     │ JBB Branch 120      │ Active  │ Jimbob's Banking & │
    │    │                    │                     │         │ Trust (ID 10)      │
    │ 19 │ JBB Branch 127     │ JBB Branch 127      │ Active  │ Jimbob's Banking & │
    │    │                    │                     │         │ Trust (ID 10)      │
    │ 20 │ JBB Branch 133     │ JBB Branch 133      │ Active  │ Jimbob's Banking & │
    │    │                    │                     │         │ Trust (ID 10)      │
    │ 21 │ MDF                │ MDF                 │ Active  │ NC State           │
    │    │                    │                     │         │ University (ID 13) │
    │ 28 │ Outta Site         │ Outta Site          │ Active  │ —                  │
    │ 25 │ Servidor de        │ Servidor de Ignacio │ Active  │ —                  │
    │    │ Ignacio            │                     │         │                    │
    │ 26 │ ZIDRENN-SITE-A     │ ZIDRENN-SITE-A      │ Active  │ —                  │
    │ 27 │ ZIDRENN-SITE-B     │ ZIDRENN-SITE-B      │ Active  │ —                  │
    └────┴────────────────────┴─────────────────────┴─────────┴────────────────────┘
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.946s</span>

---
