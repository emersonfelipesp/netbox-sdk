# NetBox CLI — captured command input and output

This file is **machine-generated**. Regenerate with:

```bash
cd /path/to/netbox-cli
pip install -e .   # once
nbx docs generate-capture
# or: python docs/generate_command_docs.py
```

Run the capture **in the background** (log + pid):

```bash
./docs/run_capture_in_background.sh
```

## Generation metadata

- **UTC time:** `2026-03-20T21:58:29.593852+00:00`
- **Effective `NETBOX_URL`:** `https://demo.netbox.dev`
- **Effective timeout (s):** `30`
- **`NETBOX_TOKEN_KEY` set:** `False`

> Live API calls (`call`, dynamic-form list/get/…) reflect whatever is reachable at NETBOX_URL. Connection errors and 401/403 responses are still useful documentation of real CLI behavior.

> **Typer `CliRunner` quirk:** help banners may show `Usage: root` instead of `Usage: nbx`. The installed `nbx` script uses the correct name.

---

## Top-level

### nbx --help

**Input:**

```bash
nbx --help
```

**Exit code:** `0`  ·  **Wall time (s):** `0.712`

**Output:**

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

### nbx init --help

**Input:**

```bash
nbx init --help
```

**Exit code:** `0`  ·  **Wall time (s):** `0.690`

**Output:**

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

---

### nbx config --help

**Input:**

```bash
nbx config --help
```

**Exit code:** `0`  ·  **Wall time (s):** `0.762`

**Output:**

```text
                                                                                
 Usage: root config [OPTIONS]                                                   
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --show-token          Include API token in output                            │
│ --help                Show this message and exit.                            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

### nbx config

**Input:**

```bash
nbx config
```

*Displays current connection config. Token fields show 'set'/'unset' unless --show-token is passed.*

**Exit code:** `0`  ·  **Wall time (s):** `0.628`

**Output:**

```text
{
  "base_url": "https://demo.netbox.dev",
  "timeout": 30.0,
  "token_v2": "set",
  "token_key": "set",
  "token_secret": "set"
}
```

---

### nbx groups --help

**Input:**

```bash
nbx groups --help
```

**Exit code:** `0`  ·  **Wall time (s):** `0.611`

**Output:**

```text
                                                                                
 Usage: root groups [OPTIONS]                                                   
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

### nbx resources --help

**Input:**

```bash
nbx resources --help
```

**Exit code:** `0`  ·  **Wall time (s):** `0.621`

**Output:**

```text
                                                                                
 Usage: root resources [OPTIONS] GROUP                                          
                                                                                
╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    group      TEXT  OpenAPI app group, e.g. dcim [required]                │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

### nbx ops --help

**Input:**

```bash
nbx ops --help
```

**Exit code:** `0`  ·  **Wall time (s):** `0.622`

**Output:**

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

---

### nbx call --help

**Input:**

```bash
nbx call --help
```

**Exit code:** `0`  ·  **Wall time (s):** `0.613`

**Output:**

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

---

### nbx tui --help

**Input:**

```bash
nbx tui --help
```

*Launches the full Textual TUI when invoked without flags. --help shown here only.*

**Exit code:** `0`  ·  **Wall time (s):** `0.611`

**Output:**

```text
                                                                                
 Usage: root tui [OPTIONS]                                                      
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --theme          Theme selector. Use '--theme' to list available themes or   │
│                  '--theme <name>' to launch with one.                        │
│ --help           Show this message and exit.                                 │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

### nbx tui --theme

**Input:**

```bash
nbx tui --theme
```

*Lists available themes without launching the TUI.*

**Exit code:** `0`  ·  **Wall time (s):** `0.688`

**Output:**

```text
Available themes:
- default
- dracula
```

---

### nbx docs --help

**Input:**

```bash
nbx docs --help
```

**Exit code:** `0`  ·  **Wall time (s):** `0.613`

**Output:**

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

---

### nbx docs generate-capture --help

**Input:**

```bash
nbx docs generate-capture --help
```

**Exit code:** `0`  ·  **Wall time (s):** `0.622`

**Output:**

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

---

## Schema Discovery

### nbx groups

**Input:**

```bash
nbx groups
```

*Lists all OpenAPI app groups from the bundled schema. No network call.*

**Exit code:** `0`  ·  **Wall time (s):** `0.603`

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

### nbx resources dcim

**Input:**

```bash
nbx resources dcim
```

*Lists all resources under the 'dcim' app group.*

**Exit code:** `0`  ·  **Wall time (s):** `0.606`

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

### nbx ops dcim devices

**Input:**

```bash
nbx ops dcim devices
```

*Lists HTTP operations (method, path, operationId) for dcim/devices.*

**Exit code:** `0`  ·  **Wall time (s):** `0.613`

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

### nbx resources ipam

**Input:**

```bash
nbx resources ipam
```

*Lists all resources under the 'ipam' app group.*

**Exit code:** `0`  ·  **Wall time (s):** `0.608`

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

## Dynamic Commands

### nbx dcim --help

**Input:**

```bash
nbx dcim --help
```

*Auto-generated Typer sub-app for the 'dcim' OpenAPI group.*

**Exit code:** `0`  ·  **Wall time (s):** `0.692`

**Output:**

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

---

### nbx dcim devices --help

**Input:**

```bash
nbx dcim devices --help
```

*Auto-generated Typer sub-app for dcim/devices.*

**Exit code:** `0`  ·  **Wall time (s):** `0.614`

**Output:**

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

---

### nbx dcim devices list --help

**Input:**

```bash
nbx dcim devices list --help
```

*Auto-generated list action for dcim/devices.*

**Exit code:** `0`  ·  **Wall time (s):** `0.633`

**Output:**

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

---

### nbx ipam prefixes --help

**Input:**

```bash
nbx ipam prefixes --help
```

**Exit code:** `0`  ·  **Wall time (s):** `0.633`

**Output:**

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

---

## Live API

### nbx call GET /api/status/

**Input:**

```bash
nbx call GET /api/status/
```

*Requires a reachable NetBox at NETBOX_URL. Connection errors are expected in offline runs and are valid documentation.*

**Exit code:** `0`  ·  **Wall time (s):** `1.356`

**Output:**

```text
Status: 403
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Field  ┃ Value            ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ Detail │ Invalid v2 token │
└────────┴──────────────────┘
```

---

### nbx call GET /api/dcim/sites/ --json

**Input:**

```bash
nbx call GET /api/dcim/sites/ --json
```

*Returns paginated list as raw JSON. Requires a NetBox with a valid token.*

**Exit code:** `0`  ·  **Wall time (s):** `0.983`

**Output:**

```text
Status: 403
{
  "detail": "Invalid v2 token"
}
```

---

## Dynamic Form

### nbx dcim devices list (dynamic form)

**Input:**

```bash
nbx dcim devices list
```

*Invoked via the auto-registered Typer sub-command (not dynamic ctx.args path). Requires live NetBox. Connection errors are expected in offline runs.*

**Exit code:** `0`  ·  **Wall time (s):** `1.021`

**Output:**

```text
Status: 403
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━┓
┃ Field  ┃ Value            ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━┩
│ Detail │ Invalid v2 token │
└────────┴──────────────────┘
```

---
