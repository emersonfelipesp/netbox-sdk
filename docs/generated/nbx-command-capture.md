# netbox-sdk — captured command input and output

This file is **machine-generated**. Regenerate with:

```bash
cd /path/to/netbox-sdk
uv sync --group docs --group dev   # once
uv run nbx docs generate-capture
# or: uv run python docs/generate_command_docs.py
```

Run the capture **in the background** (log + pid):

```bash
./docs/run_capture_in_background.sh
```

## Generation metadata

- **UTC time:** `2026-03-28T01:23:25.720866+00:00`
- **Profile used:** **demo profile** (`nbx demo ...` commands -> demo.netbox.dev)
- **Effective NetBox URL:** `https://demo.netbox.dev`
- **Effective timeout (s):** `2`
- **Token configured:** `False`

> Docgen is restricted to the demo profile only. Any live data shown here comes from demo.netbox.dev, never from a production NetBox instance.

> **Typer `CliRunner` quirk:** help banners may show `Usage: root` instead of `Usage: nbx`. The installed `nbx` script uses the correct name.

---

## CLI

### Core Commands

#### nbx --help

**Input:**

```bash
nbx --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.780`

**Output:**

```text
                                                                                
 Usage: nbx [OPTIONS] COMMAND [ARGS]...                                         
                                                                                
 NetBox SDK CLI. Dynamic command form: nbx <group> <resource> <action>          
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ init            Create or update the default NetBox SDK profile.             │
│ config          Show the current default profile configuration.              │
│ test            Test connectivity to your configured NetBox instance         │
│                 (default profile).                                           │
│ groups          List all available OpenAPI app groups.                       │
│ resources       List resources available within a group.                     │
│ ops             Show available HTTP operations for a resource.               │
│ graphql         Execute a GraphQL query against the NetBox API.              │
│ call            Call an arbitrary NetBox API path.                           │
│ tui             Launch the interactive NetBox terminal UI.                   │
│ logs            Show recent application logs from the shared on-disk log     │
│                 file.                                                        │
│ cli             CLI utilities: interactive command builder and helpers.      │
│ docs            Generate reference documentation (captured CLI               │
│                 input/output).                                               │
│ demo            NetBox demo.netbox.dev profile and command tree.             │
│ dev             Developer-focused tools and experimental interfaces.         │
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

---

#### nbx init --help

**Input:**

```bash
nbx init --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.430`

**Output:**

```text
                                                                                
 Usage: nbx init [OPTIONS]                                                      
                                                                                
 Create or update the default NetBox SDK profile.                               
                                                                                
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

---

#### nbx config --help

**Input:**

```bash
nbx config --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.442`

**Output:**

```text
                                                                                
 Usage: nbx config [OPTIONS]                                                    
                                                                                
 Show the current default profile configuration.                                
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --show-token          Include API token in output                            │
│ --help                Show this message and exit.                            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx logs --help

**Input:**

```bash
nbx logs --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.509`

**Output:**

```text
                                                                                
 Usage: nbx logs [OPTIONS]                                                      
                                                                                
 Show recent application logs from the shared on-disk log file.                 
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --limit   -n      INTEGER RANGE [x>=1]  Number of most recent log entries to │
│                                         display.                             │
│                                         [default: 200]                       │
│ --source                                Include module/function/line details │
│                                         in output.                           │
│ --help                                  Show this message and exit.          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx docs --help

**Input:**

```bash
nbx docs --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.746`

**Output:**

```text
                                                                                
 Usage: nbx docs [OPTIONS] COMMAND [ARGS]...                                    
                                                                                
 Generate reference documentation (captured CLI input/output).                  
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ generate-capture  Capture docs-safe ``nbx`` command output against the demo  │
│                   profile only.                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx docs generate-capture --help

**Input:**

```bash
nbx docs generate-capture --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.472`

**Output:**

```text
                                                                                
 Usage: nbx docs generate-capture [OPTIONS]                                     
                                                                                
 Capture docs-safe ``nbx`` command output against the demo profile only.        
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --output       -o                   PATH                Markdown             │
│                                                         destination.         │
│                                                         Default:             │
│                                                         <repo>/docs/generat… │
│ --raw-dir                           PATH                Raw JSON artifacts   │
│                                                         directory. Default:  │
│                                                         <repo>/docs/generat… │
│ --markdown         --no-markdown                        Append --markdown to │
│                                                         dynamic list/get/…   │
│                                                         and ``nbx call``     │
│                                                         captures so tables   │
│                                                         are plain Markdown   │
│                                                         (not Rich). Default: │
│                                                         on.                  │
│                                                         [default: markdown]  │
│ --concurrency  -j                   INTEGER RANGE       Max parallel CLI     │
│                                     [1<=x<=16]          captures. Higher     │
│                                                         values speed up      │
│                                                         generation but       │
│                                                         increase NetBox      │
│                                                         load.                │
│                                                         [default: 4]         │
│ --help                                                  Show this message    │
│                                                         and exit.            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

### Schema Discovery

#### nbx groups --help

**Input:**

```bash
nbx groups --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.824`

**Output:**

```text
                                                                                
 Usage: nbx groups [OPTIONS]                                                    
                                                                                
 List all available OpenAPI app groups.                                         
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx resources --help

**Input:**

```bash
nbx resources --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.502`

**Output:**

```text
                                                                                
 Usage: nbx resources [OPTIONS] GROUP                                           
                                                                                
 List resources available within a group.                                       
                                                                                
╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    group      TEXT  OpenAPI app group, e.g. dcim [required]                │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx ops --help

**Input:**

```bash
nbx ops --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.565`

**Output:**

```text
                                                                                
 Usage: nbx ops [OPTIONS] GROUP RESOURCE                                        
                                                                                
 Show available HTTP operations for a resource.                                 
                                                                                
╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    group         TEXT  [required]                                          │
│ *    resource      TEXT  [required]                                          │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx groups

**Input:**

```bash
nbx groups
```

**Exit code:** `0`  ·  **Wall time (s):** `3.592`

**Output:**

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

---

#### nbx resources dcim

**Input:**

```bash
nbx resources dcim
```

**Exit code:** `0`  ·  **Wall time (s):** `3.512`

**Output:**

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

---

#### nbx ops dcim devices

**Input:**

```bash
nbx ops dcim devices
```

**Exit code:** `0`  ·  **Wall time (s):** `3.549`

**Output:**

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

---

#### nbx resources ipam

**Input:**

```bash
nbx resources ipam
```

**Exit code:** `0`  ·  **Wall time (s):** `3.543`

**Output:**

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

---

### GraphQL and HTTP

#### nbx graphql --help

**Input:**

```bash
nbx graphql --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.451`

**Output:**

```text
                                                                                
 Usage: nbx graphql [OPTIONS] QUERY                                             
                                                                                
 Execute a GraphQL query against the NetBox API.                                
                                                                                
╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    query      TEXT  GraphQL query string [required]                        │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --variables  -v      TEXT  GraphQL variables: one JSON object, or repeat for │
│                            multiple key=value pairs                          │
│ --json                     Output raw JSON                                   │
│ --yaml                     Output YAML                                       │
│ --help                     Show this message and exit.                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx call --help

**Input:**

```bash
nbx call --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.973`

**Output:**

```text
                                                                                
 Usage: nbx call [OPTIONS] METHOD PATH                                          
                                                                                
 Call an arbitrary NetBox API path.                                             
                                                                                
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
│ --markdown                 Output Markdown (mutually exclusive with          │
│                            --json/--yaml)                                    │
│ --help                     Show this message and exit.                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

### Dynamic Commands

#### nbx dcim --help

**Input:**

```bash
nbx dcim --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.903`

**Output:**

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

---

#### nbx dcim devices --help

**Input:**

```bash
nbx dcim devices --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.875`

**Output:**

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

---

#### nbx dcim devices list --help

**Input:**

```bash
nbx dcim devices list --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.832`

**Output:**

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

---

#### nbx ipam prefixes --help

**Input:**

```bash
nbx ipam prefixes --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.507`

**Output:**

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

---

#### nbx dcim interfaces get --help

**Input:**

```bash
nbx dcim interfaces get --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.699`

**Output:**

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

---

#### nbx circuits circuit-terminations get --help

**Input:**

```bash
nbx circuits circuit-terminations get --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.624`

**Output:**

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

---

#### nbx demo dcim devices list --select results.0.name

**Input:**

```bash
nbx demo dcim devices list --select results.0.name --markdown
```

**Exit code:** `124`  ·  **Wall time (s):** `60.040`

**Output:**

```text
(empty)
```

---

#### nbx demo dcim devices list --columns id,name,status

**Input:**

```bash
nbx demo dcim devices list --columns id,name,status --markdown
```

**Exit code:** `124`  ·  **Wall time (s):** `60.050`

**Output:**

```text
(empty)
```

---

#### nbx demo dcim devices list --max-columns 3

**Input:**

```bash
nbx demo dcim devices list --max-columns 3 --markdown
```

**Exit code:** `1`  ·  **Wall time (s):** `34.968`

**Output:**

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

---

#### nbx demo dcim devices create --dry-run --body-json {"name":"test"}

**Input:**

```bash
nbx demo dcim devices create --dry-run --body-json {"name":"test"} --markdown
```

**Exit code:** `0`  ·  **Wall time (s):** `3.963`

**Output:**

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

---

### Developer Tools

#### nbx dev --help

**Input:**

```bash
nbx dev --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.593`

**Output:**

```text
                                                                                
 Usage: nbx dev [OPTIONS] COMMAND [ARGS]...                                     
                                                                                
 Developer-focused tools and experimental interfaces.                           
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ tui           Launch the developer request workbench TUI.                    │
│ http          Direct HTTP operations mapped from OpenAPI paths (nbx dev http │
│               <method> --path ...).                                          │
│ django-model  Inspect NetBox Django models: parse, cache, and visualize      │
│               relationships.                                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx dev http --help

**Input:**

```bash
nbx dev http --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.427`

**Output:**

```text
                                                                                
 Usage: nbx dev http [OPTIONS] COMMAND [ARGS]...                                
                                                                                
 Direct HTTP operations mapped from OpenAPI paths (nbx dev http <method> --path 
 ...).                                                                          
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ get     GET a list or detail endpoint. Use --id for a single object.         │
│ post    POST to create a new object.                                         │
│ put     PUT to fully replace an existing object. Requires --id.              │
│ patch   PATCH to partially update an existing object. Requires --id.         │
│ delete  DELETE an object by ID. Requires --id.                               │
│ paths   List all OpenAPI paths from the bundled NetBox schema.               │
│ ops     Show available HTTP operations for a specific OpenAPI path.          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx dev http get --help

**Input:**

```bash
nbx dev http get --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.475`

**Output:**

```text
                                                                                
 Usage: nbx dev http get [OPTIONS]                                              
                                                                                
 GET a list or detail endpoint. Use --id for a single object.                   
                                                                                
 Any unrecognised --flag is forwarded as a query filter:                        
 nbx dev http get --path /dcim/devices/ --status active --site mysite           
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ *  --path      -p      TEXT     API path, e.g. /dcim/devices/ [required]     │
│    --id                INTEGER  Object ID for detail endpoint                │
│    --query     -q      TEXT     Query filter as key=value (repeatable)       │
│    --json                       Output raw JSON                              │
│    --yaml                       Output YAML                                  │
│    --markdown                   Output Markdown (mutually exclusive with     │
│                                 --json/--yaml)                               │
│    --help                       Show this message and exit.                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx dev http post --help

**Input:**

```bash
nbx dev http post --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.460`

**Output:**

```text
                                                                                
 Usage: nbx dev http post [OPTIONS]                                             
                                                                                
 POST to create a new object.                                                   
                                                                                
 Pass body fields directly as flags or with --argument:                         
 nbx dev http post --path /dcim/devices/ --name router1 --site 3 --device-type  
 1                                                                              
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ *  --path       -p      TEXT  API path, e.g. /dcim/devices/ [required]       │
│    --argument   -a      TEXT  Body field as key=value (repeatable)           │
│    --body-json          TEXT  Inline JSON request body                       │
│    --body-file          TEXT  Path to JSON body file                         │
│    --json                     Output raw JSON                                │
│    --yaml                     Output YAML                                    │
│    --markdown                 Output Markdown (mutually exclusive with       │
│                               --json/--yaml)                                 │
│    --help                     Show this message and exit.                    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx dev http put --help

**Input:**

```bash
nbx dev http put --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.757`

**Output:**

```text
                                                                                
 Usage: nbx dev http put [OPTIONS]                                              
                                                                                
 PUT to fully replace an existing object. Requires --id.                        
                                                                                
 Pass body fields directly as flags:                                            
 nbx dev http put --path /dcim/devices/ --id 42 --name router1-renamed          
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ *  --path       -p      TEXT     API path, e.g. /dcim/devices/ [required]    │
│ *  --id                 INTEGER  Object ID (required for PUT) [required]     │
│    --argument   -a      TEXT     Body field as key=value (repeatable)        │
│    --body-json          TEXT     Inline JSON request body                    │
│    --body-file          TEXT     Path to JSON body file                      │
│    --json                        Output raw JSON                             │
│    --yaml                        Output YAML                                 │
│    --markdown                    Output Markdown (mutually exclusive with    │
│                                  --json/--yaml)                              │
│    --help                        Show this message and exit.                 │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx dev http patch --help

**Input:**

```bash
nbx dev http patch --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.838`

**Output:**

```text
                                                                                
 Usage: nbx dev http patch [OPTIONS]                                            
                                                                                
 PATCH to partially update an existing object. Requires --id.                   
                                                                                
 Pass only the fields you want to change:                                       
 nbx dev http patch --path /dcim/devices/ --id 42 --status active               
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ *  --path       -p      TEXT     API path, e.g. /dcim/devices/ [required]    │
│ *  --id                 INTEGER  Object ID (required for PATCH) [required]   │
│    --argument   -a      TEXT     Body field as key=value (repeatable)        │
│    --body-json          TEXT     Inline JSON request body                    │
│    --body-file          TEXT     Path to JSON body file                      │
│    --json                        Output raw JSON                             │
│    --yaml                        Output YAML                                 │
│    --markdown                    Output Markdown (mutually exclusive with    │
│                                  --json/--yaml)                              │
│    --help                        Show this message and exit.                 │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx dev http delete --help

**Input:**

```bash
nbx dev http delete --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.402`

**Output:**

```text
                                                                                
 Usage: nbx dev http delete [OPTIONS]                                           
                                                                                
 DELETE an object by ID. Requires --id.                                         
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ *  --path      -p      TEXT     API path, e.g. /dcim/devices/ [required]     │
│ *  --id                INTEGER  Object ID (required for DELETE) [required]   │
│    --json                       Output raw JSON                              │
│    --yaml                       Output YAML                                  │
│    --markdown                   Output Markdown (mutually exclusive with     │
│                                 --json/--yaml)                               │
│    --help                       Show this message and exit.                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx dev http paths --help

**Input:**

```bash
nbx dev http paths --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.428`

**Output:**

```text
                                                                                
 Usage: nbx dev http paths [OPTIONS] [SEARCH]                                   
                                                                                
 List all OpenAPI paths from the bundled NetBox schema.                         
                                                                                
╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   search      [SEARCH]  Optional substring filter on path                    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --method  -m      TEXT  Filter by HTTP method (GET, POST, PUT, PATCH,        │
│                         DELETE)                                              │
│ --group   -g      TEXT  Filter by API group, e.g. dcim                       │
│ --help                  Show this message and exit.                          │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx dev http ops --help

**Input:**

```bash
nbx dev http ops --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.414`

**Output:**

```text
                                                                                
 Usage: nbx dev http ops [OPTIONS]                                              
                                                                                
 Show available HTTP operations for a specific OpenAPI path.                    
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ *  --path  -p      TEXT  API path to inspect [required]                      │
│    --help                Show this message and exit.                         │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx dev http paths

**Input:**

```bash
nbx dev http paths
```

**Exit code:** `0`  ·  **Wall time (s):** `3.862`

**Output:**

```text
                                  312 path(s)                                   
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━┓
┃ Path                                                     ┃ Methods           ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━┩
│ /api/authentication-check/                               │ GET               │
│ /api/circuits/circuit-group-assignments/                 │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/circuits/circuit-group-assignments/{id}/            │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/circuits/circuit-groups/                            │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/circuits/circuit-groups/{id}/                       │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/circuits/circuit-terminations/                      │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/circuits/circuit-terminations/{id}/                 │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/circuits/circuit-terminations/{id}/paths/           │ GET               │
│ /api/circuits/circuit-types/                             │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/circuits/circuit-types/{id}/                        │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/circuits/circuits/                                  │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/circuits/circuits/{id}/                             │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/circuits/provider-accounts/                         │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/circuits/provider-accounts/{id}/                    │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/circuits/provider-networks/                         │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/circuits/provider-networks/{id}/                    │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/circuits/providers/                                 │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/circuits/providers/{id}/                            │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/circuits/virtual-circuit-terminations/              │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/circuits/virtual-circuit-terminations/{id}/         │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/circuits/virtual-circuit-terminations/{id}/paths/   │ GET               │
│ /api/circuits/virtual-circuit-types/                     │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/circuits/virtual-circuit-types/{id}/                │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/circuits/virtual-circuits/                          │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/circuits/virtual-circuits/{id}/                     │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/core/background-queues/                             │ GET               │
│ /api/core/background-queues/{name}/                      │ GET               │
│ /api/core/background-tasks/                              │ GET               │
│ /api/core/background-tasks/{id}/                         │ GET               │
│ /api/core/background-tasks/{id}/delete/                  │ POST              │
│ /api/core/background-tasks/{id}/enqueue/                 │ POST              │
│ /api/core/background-tasks/{id}/requeue/                 │ POST              │
│ /api/core/background-tasks/{id}/stop/                    │ POST              │
│ /api/core/background-workers/                            │ GET               │
│ /api/core/background-workers/{name}/                     │ GET               │
│ /api/core/data-files/                                    │ GET               │
│ /api/core/data-files/{id}/                               │ GET               │
│ /api/core/data-sources/                                  │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/core/data-sources/{id}/                             │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/core/data-sources/{id}/sync/                        │ POST              │
│ /api/core/jobs/                                          │ GET               │
│ /api/core/jobs/{id}/                                     │ GET               │
│ /api/core/object-changes/                                │ GET               │
│ /api/core/object-changes/{id}/                           │ GET               │
│ /api/core/object-types/                                  │ GET               │
│ /api/core/object-types/{id}/                             │ GET               │
│ /api/dcim/cable-terminations/                            │ GET               │
│ /api/dcim/cable-terminations/{id}/                       │ GET               │
│ /api/dcim/cables/                                        │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/cables/{id}/                                   │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/connected-device/                              │ GET               │
│ /api/dcim/console-port-templates/                        │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/console-port-templates/{id}/                   │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/console-ports/                                 │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/console-ports/{id}/                            │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/console-ports/{id}/trace/                      │ GET               │
│ /api/dcim/console-server-port-templates/                 │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/console-server-port-templates/{id}/            │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/console-server-ports/                          │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/console-server-ports/{id}/                     │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/console-server-ports/{id}/trace/               │ GET               │
│ /api/dcim/device-bay-templates/                          │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/device-bay-templates/{id}/                     │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/device-bays/                                   │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/device-bays/{id}/                              │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/device-roles/                                  │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/device-roles/{id}/                             │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/device-types/                                  │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/device-types/{id}/                             │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/devices/                                       │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/devices/{id}/                                  │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/devices/{id}/render-config/                    │ POST              │
│ /api/dcim/front-port-templates/                          │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/front-port-templates/{id}/                     │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/front-ports/                                   │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/front-ports/{id}/                              │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/front-ports/{id}/paths/                        │ GET               │
│ /api/dcim/interface-templates/                           │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/interface-templates/{id}/                      │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/interfaces/                                    │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/interfaces/{id}/                               │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/interfaces/{id}/trace/                         │ GET               │
│ /api/dcim/inventory-item-roles/                          │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/inventory-item-roles/{id}/                     │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/inventory-item-templates/                      │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/inventory-item-templates/{id}/                 │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/inventory-items/                               │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/inventory-items/{id}/                          │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/locations/                                     │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/locations/{id}/                                │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/mac-addresses/                                 │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/mac-addresses/{id}/                            │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/manufacturers/                                 │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/manufacturers/{id}/                            │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/module-bay-templates/                          │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/module-bay-templates/{id}/                     │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/module-bays/                                   │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/module-bays/{id}/                              │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/module-type-profiles/                          │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/module-type-profiles/{id}/                     │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/module-types/                                  │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/module-types/{id}/                             │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/modules/                                       │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/modules/{id}/                                  │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/platforms/                                     │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/platforms/{id}/                                │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/power-feeds/                                   │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/power-feeds/{id}/                              │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/power-feeds/{id}/trace/                        │ GET               │
│ /api/dcim/power-outlet-templates/                        │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/power-outlet-templates/{id}/                   │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/power-outlets/                                 │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/power-outlets/{id}/                            │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/power-outlets/{id}/trace/                      │ GET               │
│ /api/dcim/power-panels/                                  │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/power-panels/{id}/                             │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/power-port-templates/                          │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/power-port-templates/{id}/                     │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/power-ports/                                   │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/power-ports/{id}/                              │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/power-ports/{id}/trace/                        │ GET               │
│ /api/dcim/rack-reservations/                             │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/rack-reservations/{id}/                        │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/rack-roles/                                    │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/rack-roles/{id}/                               │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/rack-types/                                    │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/rack-types/{id}/                               │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/racks/                                         │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/racks/{id}/                                    │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/racks/{id}/elevation/                          │ GET               │
│ /api/dcim/rear-port-templates/                           │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/rear-port-templates/{id}/                      │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/rear-ports/                                    │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/rear-ports/{id}/                               │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/rear-ports/{id}/paths/                         │ GET               │
│ /api/dcim/regions/                                       │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/regions/{id}/                                  │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/site-groups/                                   │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/site-groups/{id}/                              │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/sites/                                         │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/sites/{id}/                                    │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/virtual-chassis/                               │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/virtual-chassis/{id}/                          │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/dcim/virtual-device-contexts/                       │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/dcim/virtual-device-contexts/{id}/                  │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/bookmarks/                                   │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/bookmarks/{id}/                              │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/config-context-profiles/                     │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/config-context-profiles/{id}/                │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/config-context-profiles/{id}/sync/           │ POST              │
│ /api/extras/config-contexts/                             │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/config-contexts/{id}/                        │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/config-contexts/{id}/sync/                   │ POST              │
│ /api/extras/config-templates/                            │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/config-templates/{id}/                       │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/config-templates/{id}/render/                │ POST              │
│ /api/extras/config-templates/{id}/sync/                  │ POST              │
│ /api/extras/custom-field-choice-sets/                    │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/custom-field-choice-sets/{id}/               │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/custom-field-choice-sets/{id}/choices/       │ GET               │
│ /api/extras/custom-fields/                               │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/custom-fields/{id}/                          │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/custom-links/                                │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/custom-links/{id}/                           │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/dashboard/                                   │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/event-rules/                                 │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/event-rules/{id}/                            │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/export-templates/                            │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/export-templates/{id}/                       │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/export-templates/{id}/sync/                  │ POST              │
│ /api/extras/image-attachments/                           │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/image-attachments/{id}/                      │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/journal-entries/                             │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/journal-entries/{id}/                        │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/notification-groups/                         │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/notification-groups/{id}/                    │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/notifications/                               │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/notifications/{id}/                          │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/saved-filters/                               │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/saved-filters/{id}/                          │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/scripts/                                     │ GET, POST         │
│ /api/extras/scripts/{id}/                                │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/subscriptions/                               │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/subscriptions/{id}/                          │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/table-configs/                               │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/table-configs/{id}/                          │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/tagged-objects/                              │ GET               │
│ /api/extras/tagged-objects/{id}/                         │ GET               │
│ /api/extras/tags/                                        │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/tags/{id}/                                   │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/extras/webhooks/                                    │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/extras/webhooks/{id}/                               │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/aggregates/                                    │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/aggregates/{id}/                               │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/asn-ranges/                                    │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/asn-ranges/{id}/                               │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/asn-ranges/{id}/available-asns/                │ GET, POST         │
│ /api/ipam/asns/                                          │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/asns/{id}/                                     │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/fhrp-group-assignments/                        │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/fhrp-group-assignments/{id}/                   │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/fhrp-groups/                                   │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/fhrp-groups/{id}/                              │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/ip-addresses/                                  │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/ip-addresses/{id}/                             │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/ip-ranges/                                     │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/ip-ranges/{id}/                                │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/ip-ranges/{id}/available-ips/                  │ GET, POST         │
│ /api/ipam/prefixes/                                      │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/prefixes/{id}/                                 │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/prefixes/{id}/available-ips/                   │ GET, POST         │
│ /api/ipam/prefixes/{id}/available-prefixes/              │ GET, POST         │
│ /api/ipam/rirs/                                          │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/rirs/{id}/                                     │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/roles/                                         │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/roles/{id}/                                    │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/route-targets/                                 │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/route-targets/{id}/                            │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/service-templates/                             │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/service-templates/{id}/                        │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/services/                                      │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/services/{id}/                                 │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/vlan-groups/                                   │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/vlan-groups/{id}/                              │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/vlan-groups/{id}/available-vlans/              │ GET, POST         │
│ /api/ipam/vlan-translation-policies/                     │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/vlan-translation-policies/{id}/                │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/vlan-translation-rules/                        │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/vlan-translation-rules/{id}/                   │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/vlans/                                         │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/vlans/{id}/                                    │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/ipam/vrfs/                                          │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/ipam/vrfs/{id}/                                     │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/plugins/gpon/boards/                                │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/plugins/gpon/boards/{id}/                           │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/plugins/gpon/line-profiles/                         │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/plugins/gpon/line-profiles/{id}/                    │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/plugins/gpon/olts/                                  │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/plugins/gpon/olts/{id}/                             │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/plugins/gpon/onts/                                  │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/plugins/gpon/onts/{id}/                             │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/plugins/gpon/ports/                                 │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/plugins/gpon/ports/{id}/                            │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/plugins/gpon/service-profiles/                      │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/plugins/gpon/service-profiles/{id}/                 │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/schema/                                             │ GET               │
│ /api/status/                                             │ GET               │
│ /api/tenancy/contact-assignments/                        │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/tenancy/contact-assignments/{id}/                   │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/tenancy/contact-groups/                             │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/tenancy/contact-groups/{id}/                        │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/tenancy/contact-roles/                              │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/tenancy/contact-roles/{id}/                         │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/tenancy/contacts/                                   │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/tenancy/contacts/{id}/                              │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/tenancy/tenant-groups/                              │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/tenancy/tenant-groups/{id}/                         │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/tenancy/tenants/                                    │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/tenancy/tenants/{id}/                               │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/users/config/                                       │ GET               │
│ /api/users/groups/                                       │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/users/groups/{id}/                                  │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/users/owner-groups/                                 │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/users/owner-groups/{id}/                            │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/users/owners/                                       │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/users/owners/{id}/                                  │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/users/permissions/                                  │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/users/permissions/{id}/                             │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/users/tokens/                                       │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/users/tokens/provision/                             │ POST              │
│ /api/users/tokens/{id}/                                  │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/users/users/                                        │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/users/users/{id}/                                   │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/virtualization/cluster-groups/                      │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/virtualization/cluster-groups/{id}/                 │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/virtualization/cluster-types/                       │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/virtualization/cluster-types/{id}/                  │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/virtualization/clusters/                            │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/virtualization/clusters/{id}/                       │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/virtualization/interfaces/                          │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/virtualization/interfaces/{id}/                     │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/virtualization/virtual-disks/                       │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/virtualization/virtual-disks/{id}/                  │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/virtualization/virtual-machines/                    │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/virtualization/virtual-machines/{id}/               │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/virtualization/virtual-machines/{id}/render-config/ │ POST              │
│ /api/vpn/ike-policies/                                   │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/vpn/ike-policies/{id}/                              │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/vpn/ike-proposals/                                  │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/vpn/ike-proposals/{id}/                             │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/vpn/ipsec-policies/                                 │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/vpn/ipsec-policies/{id}/                            │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/vpn/ipsec-profiles/                                 │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/vpn/ipsec-profiles/{id}/                            │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/vpn/ipsec-proposals/                                │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/vpn/ipsec-proposals/{id}/                           │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/vpn/l2vpn-terminations/                             │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/vpn/l2vpn-terminations/{id}/                        │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/vpn/l2vpns/                                         │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/vpn/l2vpns/{id}/                                    │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/vpn/tunnel-groups/                                  │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/vpn/tunnel-groups/{id}/                             │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/vpn/tunnel-terminations/                            │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/vpn/tunnel-terminations/{id}/                       │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/vpn/tunnels/                                        │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/vpn/tunnels/{id}/                                   │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/wireless/wireless-lan-groups/                       │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/wireless/wireless-lan-groups/{id}/                  │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/wireless/wireless-lans/                             │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/wireless/wireless-lans/{id}/                        │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
│ /api/wireless/wireless-links/                            │ DELETE, GET,      │
│                                                          │ PATCH, POST, PUT  │
│ /api/wireless/wireless-links/{id}/                       │ DELETE, GET,      │
│                                                          │ PATCH, PUT        │
└──────────────────────────────────────────────────────────┴───────────────────┘
```

---

#### nbx dev http ops --path /api/dcim/devices/

**Input:**

```bash
nbx dev http ops --path /api/dcim/devices/
```

**Exit code:** `0`  ·  **Wall time (s):** `3.530`

**Output:**

```text
            Operations: /api/dcim/devices/             
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Method ┃ Operation ID                     ┃ Summary ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ GET    │ dcim_devices_list                │ -       │
│ POST   │ dcim_devices_create              │ -       │
│ PUT    │ dcim_devices_bulk_update         │ -       │
│ PATCH  │ dcim_devices_bulk_partial_update │ -       │
│ DELETE │ dcim_devices_bulk_destroy        │ -       │
└────────┴──────────────────────────────────┴─────────┘
```

---

#### nbx demo dev http get --path /api/status/

**Input:**

```bash
nbx demo dev http get --path /api/status/ --markdown
```

**Exit code:** `124`  ·  **Wall time (s):** `60.041`

**Output:**

```text
(empty)
```

---

#### nbx dev django-model --help

**Input:**

```bash
nbx dev django-model --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.598`

**Output:**

```text
                                                                                
 Usage: nbx dev django-model [OPTIONS] COMMAND [ARGS]...                        
                                                                                
 Inspect NetBox Django models: parse, cache, and visualize relationships.       
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ build  Parse NetBox Django models and build the static cache.                │
│ tui    Launch the Django Model Inspector TUI.                                │
│ fetch  Fetch a NetBox release from GitHub and build the Django model graph.  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx dev django-model build --help

**Input:**

```bash
nbx dev django-model build --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.713`

**Output:**

```text
                                                                                
 Usage: nbx dev django-model build [OPTIONS]                                    
                                                                                
 Parse NetBox Django models and build the static cache.                         
                                                                                
 Run this once (or when NetBox is updated) to generate the model graph          
 used by the TUI.                                                               
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --netbox-root  -n      PATH  Path to the NetBox Django project root          │
│                              (contains dcim/, ipam/, etc.).                  │
│                              [default: /root/nms/netbox/netbox]              │
│ --rebuild      -r            Force rebuild even if cache exists.             │
│ --cache-path   -o      PATH  Output path for the JSON build file (default:   │
│                              ~/.config/netbox-sdk/django_models.json).       │
│ --help                       Show this message and exit.                     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx dev django-model fetch --help

**Input:**

```bash
nbx dev django-model fetch --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.796`

**Output:**

```text
                                                                                
 Usage: nbx dev django-model fetch [OPTIONS] [TAG]                              
                                                                                
 Fetch a NetBox release from GitHub and build the Django model graph.           
                                                                                
 Examples::                                                                     
                                                                                
 nbx dev django-model fetch v4.2.1                                              
 nbx dev django-model fetch --auto                                              
                                                                                
╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   tag      [TAG]  Release tag to fetch (e.g. v4.2.1). Omit with --auto to    │
│                   detect from connected NetBox.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --auto  -a        Detect NetBox version from the default profile and fetch   │
│                   the matching release.                                      │
│ --help            Show this message and exit.                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

### Demo Profile

#### nbx demo --help

**Input:**

```bash
nbx demo --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.428`

**Output:**

```text
                                                                                
 Usage: nbx demo [OPTIONS] COMMAND [ARGS]...                                    
                                                                                
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
│ config          Show the configured demo profile settings.                   │
│ test            Test connectivity to demo.netbox.dev using the configured    │
│                 demo profile.                                                │
│ reset           Remove the saved demo profile configuration.                 │
│ tui             Launch the TUI against the demo profile.                     │
│ cli             CLI builder tools against the demo.netbox.dev profile.       │
│ dev             Developer-focused tools against the demo.netbox.dev profile. │
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

---

#### nbx demo init --help

**Input:**

```bash
nbx demo init --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.421`

**Output:**

```text
                                                                                
 Usage: nbx demo init [OPTIONS]                                                 
                                                                                
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

---

#### nbx demo config --help

**Input:**

```bash
nbx demo config --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.477`

**Output:**

```text
                                                                                
 Usage: nbx demo config [OPTIONS]                                               
                                                                                
 Show the configured demo profile settings.                                     
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --show-token          Include API token in output                            │
│ --help                Show this message and exit.                            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx demo test --help

**Input:**

```bash
nbx demo test --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.415`

**Output:**

```text
                                                                                
 Usage: nbx demo test [OPTIONS]                                                 
                                                                                
 Test connectivity to demo.netbox.dev using the configured demo profile.        
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx demo reset --help

**Input:**

```bash
nbx demo reset --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.432`

**Output:**

```text
                                                                                
 Usage: nbx demo reset [OPTIONS]                                                
                                                                                
 Remove the saved demo profile configuration.                                   
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx demo dev --help

**Input:**

```bash
nbx demo dev --help
```

**Exit code:** `0`  ·  **Wall time (s):** `4.016`

**Output:**

```text
                                                                                
 Usage: nbx demo dev [OPTIONS] COMMAND [ARGS]...                                
                                                                                
 Developer-focused tools against the demo.netbox.dev profile.                   
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ tui            Launch the developer request workbench TUI against the demo   │
│                profile.                                                      │
│ http           Direct HTTP operations mapped from OpenAPI paths (nbx dev     │
│                http <method> --path ...).                                    │
│ django-model   Inspect NetBox Django models: parse, cache, and visualize     │
│                relationships.                                                │
│ django-models  Inspect NetBox Django models: parse, cache, and visualize     │
│                relationships.                                                │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx demo cli --help

**Input:**

```bash
nbx demo cli --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.512`

**Output:**

```text
                                                                                
 Usage: nbx demo cli [OPTIONS] COMMAND [ARGS]...                                
                                                                                
 CLI builder tools against the demo.netbox.dev profile.                         
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ tui  Launch the interactive CLI command builder against the demo profile.    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx demo dev django-model --help

**Input:**

```bash
nbx demo dev django-model --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.390`

**Output:**

```text
                                                                                
 Usage: nbx demo dev django-model [OPTIONS] COMMAND [ARGS]...                   
                                                                                
 Inspect NetBox Django models: parse, cache, and visualize relationships.       
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ build  Parse NetBox Django models and build the static cache.                │
│ tui    Launch the Django Model Inspector TUI.                                │
│ fetch  Fetch a NetBox release from GitHub and build the Django model graph.  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx demo config

**Input:**

```bash
nbx demo config
```

**Exit code:** `0`  ·  **Wall time (s):** `3.358`

**Output:**

```text
{
  "profile": "demo",
  "base_url": "https://demo.netbox.dev",
  "timeout": 30.0,
  "token_version": "v2",
  "demo_username": "unset",
  "demo_password": "unset",
  "token": "set",
  "token_key": "set",
  "token_secret": "set"
}
```

---

### Live API

#### nbx demo dcim devices list

**Input:**

```bash
nbx demo dcim devices list --markdown
```

**Exit code:** `124`  ·  **Wall time (s):** `60.045`

**Output:**

```text
(empty)
```

---

#### nbx demo ipam prefixes list

**Input:**

```bash
nbx demo ipam prefixes list --markdown
```

**Exit code:** `1`  ·  **Wall time (s):** `4.774`

**Output:**

```text
Error: Unexpected failure: Cannot connect to host demo.netbox.dev:443 ssl:default [Temporary failure in name resolution]. Please retry or check your configuration.

--- stderr ---
api request failed
Traceback (most recent call last):
  File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/connector.py", line 1562, in _create_direct_connection
    hosts = await self._resolve_host(host, port, traces=traces)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/connector.py", line 1178, in _resolve_host
    return await asyncio.shield(resolved_host_task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/connector.py", line 1209, in _resolve_host_with_throttle
    addrs = await self._resolver.resolve(host, port, family=self._family)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/resolver.py", line 40, in resolve
    infos = await self._loop.getaddrinfo(
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<5 lines>...
    )
    ^
  File "/root/.local/share/uv/python/cpython-3.14.3-linux-x86_64-gnu/lib/python3.14/asyncio/base_events.py", line 936, in getaddrinfo
    return await self.run_in_executor(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
        None, getaddr_func, host, port, family, type, proto, flags)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/root/.local/share/uv/python/cpython-3.14.3-linux-x86_64-gnu/lib/python3.14/concurrent/futures/thread.py", line 86, in run
    result = ctx.run(self.task)
  File "/root/.local/share/uv/python/cpython-3.14.3-linux-x86_64-gnu/lib/python3.14/concurrent/futures/thread.py", line 73, in run
    return fn(*args, **kwargs)
  File "/root/.local/share/uv/python/cpython-3.14.3-linux-x86_64-gnu/lib/python3.14/socket.py", line 983, in getaddrinfo
    for res in _socket.getaddrinfo(host, port, family, type, proto, flags):
               ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
socket.gaierror: [Errno -3] Temporary failure in name resolution

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
  File "/root/nms/netbox-sdk/.venv/lib/python3.14/site-packages/aiohttp/connector.py", line 1568, in _create_direct_connection
    raise ClientConnectorDNSError(req.connection_key, exc) from exc
aiohttp.client_exceptions.ClientConnectorDNSError: Cannot connect to host demo.netbox.dev:443 ssl:default [Temporary failure in name resolution]
```

---

#### nbx demo dcim sites list

**Input:**

```bash
nbx demo dcim sites list --markdown
```

**Exit code:** `124`  ·  **Wall time (s):** `60.079`

**Output:**

```text
(empty)
```

---

### Cable Trace

#### nbx demo dcim interfaces get --id 1 --trace

**Input:**

```bash
nbx demo dcim interfaces get --id 1 --trace --markdown
```

**Exit code:** `124`  ·  **Wall time (s):** `60.080`

**Output:**

```text
(empty)
```

---

#### nbx demo dcim interfaces get --id 1 --trace-only

**Input:**

```bash
nbx demo dcim interfaces get --id 1 --trace-only --markdown
```

**Exit code:** `124`  ·  **Wall time (s):** `60.045`

**Output:**

```text
(empty)
```

---

#### nbx demo circuits circuit-terminations get --id 15 --trace

**Input:**

```bash
nbx demo circuits circuit-terminations get --id 15 --trace --markdown
```

**Exit code:** `124`  ·  **Wall time (s):** `60.047`

**Output:**

```text
(empty)
```

---

#### nbx demo circuits circuit-terminations get --id 15 --trace-only

**Input:**

```bash
nbx demo circuits circuit-terminations get --id 15 --trace-only --markdown
```

**Exit code:** `124`  ·  **Wall time (s):** `60.075`

**Output:**

```text
(empty)
```

---

## TUI

### Main Browser

#### nbx tui --help

**Input:**

```bash
nbx tui --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.438`

**Output:**

```text
                                                                                
 Usage: nbx tui [OPTIONS]                                                       
                                                                                
 Launch the interactive NetBox terminal UI.                                     
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --theme          Theme selector. Use '--theme' to list available themes or   │
│                  '--theme <name>' to launch with one.                        │
│ --help           Show this message and exit.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx tui --theme

**Input:**

```bash
nbx tui --theme
```

**Exit code:** `0`  ·  **Wall time (s):** `4.165`

**Output:**

```text
Available themes:
- dracula
- netbox-dark
- netbox-light
- onedark-pro
- tokyo-night
```

---

#### nbx demo tui --help

**Input:**

```bash
nbx demo tui --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.737`

**Output:**

```text
                                                                                
 Usage: nbx demo tui [OPTIONS]                                                  
                                                                                
 Launch the TUI against the demo profile.                                       
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --theme          Theme selector. Use '--theme' to list available themes or   │
│                  '--theme <name>' to launch with one.                        │
│ --help           Show this message and exit.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx demo tui --theme

**Input:**

```bash
nbx demo tui --theme
```

**Exit code:** `0`  ·  **Wall time (s):** `4.014`

**Output:**

```text
Available themes:
- dracula
- netbox-dark
- netbox-light
- onedark-pro
- tokyo-night
```

---

### Logs Viewer

#### nbx tui logs --theme

**Input:**

```bash
nbx tui logs --theme
```

**Exit code:** `0`  ·  **Wall time (s):** `3.563`

**Output:**

```text
Available themes:
- dracula
- netbox-dark
- netbox-light
- onedark-pro
- tokyo-night
```

---

### Developer Workbench

#### nbx dev tui --help

**Input:**

```bash
nbx dev tui --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.856`

**Output:**

```text
                                                                                
 Usage: nbx dev tui [OPTIONS]                                                   
                                                                                
 Launch the developer request workbench TUI.                                    
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --theme          Theme selector. Use '--theme' to list available themes or   │
│                  '--theme <name>' to launch with one.                        │
│ --help           Show this message and exit.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx dev tui --theme

**Input:**

```bash
nbx dev tui --theme
```

**Exit code:** `0`  ·  **Wall time (s):** `3.769`

**Output:**

```text
Available themes:
- dracula
- netbox-dark
- netbox-light
- onedark-pro
- tokyo-night
```

---

#### nbx demo dev tui --help

**Input:**

```bash
nbx demo dev tui --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.419`

**Output:**

```text
                                                                                
 Usage: nbx demo dev tui [OPTIONS]                                              
                                                                                
 Launch the developer request workbench TUI against the demo profile.           
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --theme          Theme selector. Use '--theme' to list available themes or   │
│                  '--theme <name>' to launch with one.                        │
│ --help           Show this message and exit.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx demo dev tui --theme

**Input:**

```bash
nbx demo dev tui --theme
```

**Exit code:** `0`  ·  **Wall time (s):** `4.108`

**Output:**

```text
Available themes:
- dracula
- netbox-dark
- netbox-light
- onedark-pro
- tokyo-night
```

---

### CLI Builder

#### nbx cli --help

**Input:**

```bash
nbx cli --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.407`

**Output:**

```text
                                                                                
 Usage: nbx cli [OPTIONS] COMMAND [ARGS]...                                     
                                                                                
 CLI utilities: interactive command builder and helpers.                        
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ tui  Launch the interactive CLI command builder TUI.                         │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx cli tui --help

**Input:**

```bash
nbx cli tui --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.402`

**Output:**

```text
                                                                                
 Usage: nbx cli tui [OPTIONS]                                                   
                                                                                
 Launch the interactive CLI command builder TUI.                                
                                                                                
 Presents a navigable menu tree (group → resource → action) that                
 progressively builds an ``nbx`` command, then executes it and                  
 shows the output — all without leaving the terminal.                           
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx demo cli --help

**Input:**

```bash
nbx demo cli --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.666`

**Output:**

```text
                                                                                
 Usage: nbx demo cli [OPTIONS] COMMAND [ARGS]...                                
                                                                                
 CLI builder tools against the demo.netbox.dev profile.                         
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ tui  Launch the interactive CLI command builder against the demo profile.    │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx demo cli tui --help

**Input:**

```bash
nbx demo cli tui --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.400`

**Output:**

```text
                                                                                
 Usage: nbx demo cli tui [OPTIONS]                                              
                                                                                
 Launch the interactive CLI command builder against the demo profile.           
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --theme          Theme selector. Use '--theme' to list available themes or   │
│                  '--theme <name>' to launch with one.                        │
│ --help           Show this message and exit.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx demo cli tui --theme

**Input:**

```bash
nbx demo cli tui --theme
```

**Exit code:** `0`  ·  **Wall time (s):** `3.582`

**Output:**

```text
Available themes:
- dracula
- netbox-dark
- netbox-light
- onedark-pro
- tokyo-night
```

---

### Django Models Browser

#### nbx dev django-model tui --help

**Input:**

```bash
nbx dev django-model tui --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.563`

**Output:**

```text
                                                                                
 Usage: nbx dev django-model tui [OPTIONS]                                      
                                                                                
 Launch the Django Model Inspector TUI.                                         
                                                                                
 Automatically builds the model cache if it doesn't exist.                      
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --theme        -t      TEXT  Theme name (e.g. netbox-dark, dracula).         │
│ --netbox-root  -n      PATH  Path to the NetBox Django project root          │
│                              (auto-builds if cache missing).                 │
│                              [default: /root/nms/netbox/netbox]              │
│ --cache-path   -o      PATH  Path to a specific model graph JSON file.       │
│ --help                       Show this message and exit.                     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx demo dev django-model tui --help

**Input:**

```bash
nbx demo dev django-model tui --help
```

**Exit code:** `0`  ·  **Wall time (s):** `3.840`

**Output:**

```text
                                                                                
 Usage: nbx demo dev django-model tui [OPTIONS]                                 
                                                                                
 Launch the Django Model Inspector TUI.                                         
                                                                                
 Automatically builds the model cache if it doesn't exist.                      
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --theme        -t      TEXT  Theme name (e.g. netbox-dark, dracula).         │
│ --netbox-root  -n      PATH  Path to the NetBox Django project root          │
│                              (auto-builds if cache missing).                 │
│                              [default: /root/nms/netbox/netbox]              │
│ --cache-path   -o      PATH  Path to a specific model graph JSON file.       │
│ --help                       Show this message and exit.                     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---
