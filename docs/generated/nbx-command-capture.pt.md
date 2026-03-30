# netbox-sdk — entrada e saída de comandos capturados

Este arquivo é **gerado automaticamente**. Para regenerar:

```bash
cd /path/to/netbox-sdk
uv sync --group docs --group dev   # uma vez
uv run nbx docs generate-capture
# ou: uv run python docs/generate_command_docs.py
```

Execute a captura **em segundo plano** (log + pid):

```bash
./docs/run_capture_in_background.sh
```

## Metadados de geração

- **Hora UTC:** `2026-03-28T02:54:01.319776+00:00`
- **Perfil usado:** **perfil demo** (comandos `nbx demo ...` → demo.netbox.dev)
- **URL efetiva do NetBox:** `https://demo.netbox.dev`
- **Timeout efetivo (s):** `30`
- **Token configurado:** `True`

> A geração de documentação está restrita ao perfil demo. Qualquer dado ao vivo mostrado aqui vem de demo.netbox.dev, nunca de uma instância NetBox de produção.

> **Comportamento do Typer `CliRunner`:** os banners de ajuda podem mostrar `Usage: root` em vez de `Usage: nbx`. O script instalado `nbx` usa o nome correto.

---

## CLI

### Core Commands

#### nbx --help

**Entrada:**

```bash
nbx --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `5.761`

**Saída:**

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
│ graphql         Execute a GraphQL query against the NetBox API, or launch    │
│                 the GraphQL TUI.                                             │
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

**Entrada:**

```bash
nbx init --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.178`

**Saída:**

```text
                                                                                
 Usage: nbx init [OPTIONS]                                                      
                                                                                
 Create or update the default NetBox SDK profile.                               
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ *  --base-url                           TEXT   NetBox base URL, e.g.         │
│                                                https://netbox.example.com    │
│                                                [required]                    │
│ *  --token-key                          TEXT   NetBox API token key          │
│                                                [required]                    │
│ *  --token-secret                       TEXT   NetBox API token secret       │
│                                                [required]                    │
│    --timeout                            FLOAT  HTTP timeout in seconds       │
│                                                [default: 30.0]               │
│    --verify-ssl      --no-verify-ssl           HTTPS TLS certificate         │
│                                                verification (default:        │
│                                                verify; omit to leave unset   │
│                                                until first failure)          │
│    --help                                      Show this message and exit.   │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx config --help

**Entrada:**

```bash
nbx config --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `5.443`

**Saída:**

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

**Entrada:**

```bash
nbx logs --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.265`

**Saída:**

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

**Entrada:**

```bash
nbx docs --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.575`

**Saída:**

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

**Entrada:**

```bash
nbx docs generate-capture --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.764`

**Saída:**

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

**Entrada:**

```bash
nbx groups --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.529`

**Saída:**

```text
                                                                                
 Usage: nbx groups [OPTIONS]                                                    
                                                                                
 List all available OpenAPI app groups.                                         
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx resources --help

**Entrada:**

```bash
nbx resources --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.328`

**Saída:**

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

**Entrada:**

```bash
nbx ops --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.989`

**Saída:**

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

**Entrada:**

```bash
nbx groups
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.968`

**Saída:**

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

**Entrada:**

```bash
nbx resources dcim
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.320`

**Saída:**

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

**Entrada:**

```bash
nbx ops dcim devices
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.193`

**Saída:**

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

### GraphQL and HTTP

#### nbx graphql --help

**Entrada:**

```bash
nbx graphql --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.968`

**Saída:**

```text
                                                                                
 Usage: nbx graphql [OPTIONS] QUERY                                             
                                                                                
 Execute a GraphQL query against the NetBox API, or launch the GraphQL TUI.     
                                                                                
╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    query      TEXT  GraphQL query string, or 'tui' to launch the GraphQL   │
│                       TUI                                                    │
│                       [required]                                             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --variables  -v      TEXT  GraphQL variables: one JSON object, or repeat for │
│                            multiple key=value pairs                          │
│ --json                     Output raw JSON                                   │
│ --yaml                     Output YAML                                       │
│ --theme                    For `nbx graphql tui`: list available themes or   │
│                            launch with `--theme <name>`.                     │
│ --help                     Show this message and exit.                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx call --help

**Entrada:**

```bash
nbx call --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.014`

**Saída:**

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

**Entrada:**

```bash
nbx dcim --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.337`

**Saída:**

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

#### nbx dcim devices list --help

**Entrada:**

```bash
nbx dcim devices list --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.322`

**Saída:**

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

#### nbx dcim interfaces get --help

**Entrada:**

```bash
nbx dcim interfaces get --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.081`

**Saída:**

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

#### nbx demo dcim devices create --dry-run --body-json {"name":"test"}

**Entrada:**

```bash
nbx demo dcim devices create --dry-run --body-json {"name":"test"} --markdown
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.986`

**Saída:**

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

**Entrada:**

```bash
nbx dev --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.926`

**Saída:**

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

**Entrada:**

```bash
nbx dev http --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.831`

**Saída:**

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

#### nbx dev http paths --help

**Entrada:**

```bash
nbx dev http paths --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.911`

**Saída:**

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

**Entrada:**

```bash
nbx dev http ops --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.919`

**Saída:**

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

**Entrada:**

```bash
nbx dev http paths
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.203`

**Saída:**

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

**Entrada:**

```bash
nbx dev http ops --path /api/dcim/devices/
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.027`

**Saída:**

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

#### nbx dev django-model --help

**Entrada:**

```bash
nbx dev django-model --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.911`

**Saída:**

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

**Entrada:**

```bash
nbx dev django-model build --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.971`

**Saída:**

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

**Entrada:**

```bash
nbx dev django-model fetch --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.913`

**Saída:**

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

**Entrada:**

```bash
nbx demo --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.922`

**Saída:**

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
│ graphql         Execute a GraphQL query against the demo NetBox API, or      │
│                 launch the GraphQL TUI.                                      │
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

**Entrada:**

```bash
nbx demo init --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.930`

**Saída:**

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

**Entrada:**

```bash
nbx demo config --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.755`

**Saída:**

```text
                                                                                
 Usage: nbx demo config [OPTIONS]                                               
                                                                                
 Show the configured demo profile settings.                                     
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --show-token          Include API token in output                            │
│ --help                Show this message and exit.                            │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx demo dev --help

**Entrada:**

```bash
nbx demo dev --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.848`

**Saída:**

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

**Entrada:**

```bash
nbx demo cli --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.791`

**Saída:**

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

**Entrada:**

```bash
nbx demo dev django-model --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.895`

**Saída:**

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

**Entrada:**

```bash
nbx demo config
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.726`

**Saída:**

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

## TUI

### Main Browser

#### nbx tui --help

**Entrada:**

```bash
nbx tui --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.835`

**Saída:**

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

**Entrada:**

```bash
nbx tui --theme
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.970`

**Saída:**

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

**Entrada:**

```bash
nbx demo tui --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.690`

**Saída:**

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

### Logs Viewer

#### nbx tui logs --theme

**Entrada:**

```bash
nbx tui logs --theme
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.914`

**Saída:**

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

**Entrada:**

```bash
nbx dev tui --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.643`

**Saída:**

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

**Entrada:**

```bash
nbx dev tui --theme
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.865`

**Saída:**

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

**Entrada:**

```bash
nbx demo dev tui --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.808`

**Saída:**

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

**Entrada:**

```bash
nbx demo dev tui --theme
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.158`

**Saída:**

```text
Available themes:
- dracula
- netbox-dark
- netbox-light
- onedark-pro
- tokyo-night
```

---

### GraphQL TUI

#### nbx graphql --help

**Entrada:**

```bash
nbx graphql --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.736`

**Saída:**

```text
                                                                                
 Usage: nbx graphql [OPTIONS] QUERY                                             
                                                                                
 Execute a GraphQL query against the NetBox API, or launch the GraphQL TUI.     
                                                                                
╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    query      TEXT  GraphQL query string, or 'tui' to launch the GraphQL   │
│                       TUI                                                    │
│                       [required]                                             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --variables  -v      TEXT  GraphQL variables: one JSON object, or repeat for │
│                            multiple key=value pairs                          │
│ --json                     Output raw JSON                                   │
│ --yaml                     Output YAML                                       │
│ --theme                    For `nbx graphql tui`: list available themes or   │
│                            launch with `--theme <name>`.                     │
│ --help                     Show this message and exit.                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx graphql tui --help

**Entrada:**

```bash
nbx graphql tui --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.667`

**Saída:**

```text
                                                                                
 Usage: nbx graphql [OPTIONS] QUERY                                             
                                                                                
 Execute a GraphQL query against the NetBox API, or launch the GraphQL TUI.     
                                                                                
╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    query      TEXT  GraphQL query string, or 'tui' to launch the GraphQL   │
│                       TUI                                                    │
│                       [required]                                             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --variables  -v      TEXT  GraphQL variables: one JSON object, or repeat for │
│                            multiple key=value pairs                          │
│ --json                     Output raw JSON                                   │
│ --yaml                     Output YAML                                       │
│ --theme                    For `nbx graphql tui`: list available themes or   │
│                            launch with `--theme <name>`.                     │
│ --help                     Show this message and exit.                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx graphql tui --theme

**Entrada:**

```bash
nbx graphql tui --theme
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.919`

**Saída:**

```text
Available themes:
- dracula
- netbox-dark
- netbox-light
- onedark-pro
- tokyo-night
```

---

#### nbx demo graphql --help

**Entrada:**

```bash
nbx demo graphql --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.578`

**Saída:**

```text
                                                                                
 Usage: nbx demo graphql [OPTIONS] QUERY                                        
                                                                                
 Execute a GraphQL query against the demo NetBox API, or launch the GraphQL     
 TUI.                                                                           
                                                                                
╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    query      TEXT  GraphQL query string, or 'tui' to launch the GraphQL   │
│                       TUI                                                    │
│                       [required]                                             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --variables  -v      TEXT  GraphQL variables: one JSON object, or repeat for │
│                            multiple key=value pairs                          │
│ --json                     Output raw JSON                                   │
│ --yaml                     Output YAML                                       │
│ --theme                    For `nbx demo graphql tui`: list available themes │
│                            or launch with `--theme <name>`.                  │
│ --help                     Show this message and exit.                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx demo graphql tui --help

**Entrada:**

```bash
nbx demo graphql tui --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.763`

**Saída:**

```text
                                                                                
 Usage: nbx demo graphql [OPTIONS] QUERY                                        
                                                                                
 Execute a GraphQL query against the demo NetBox API, or launch the GraphQL     
 TUI.                                                                           
                                                                                
╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│ *    query      TEXT  GraphQL query string, or 'tui' to launch the GraphQL   │
│                       TUI                                                    │
│                       [required]                                             │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --variables  -v      TEXT  GraphQL variables: one JSON object, or repeat for │
│                            multiple key=value pairs                          │
│ --json                     Output raw JSON                                   │
│ --yaml                     Output YAML                                       │
│ --theme                    For `nbx demo graphql tui`: list available themes │
│                            or launch with `--theme <name>`.                  │
│ --help                     Show this message and exit.                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

---

#### nbx demo graphql tui --theme

**Entrada:**

```bash
nbx demo graphql tui --theme
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.188`

**Saída:**

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

#### nbx cli tui --help

**Entrada:**

```bash
nbx cli tui --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.043`

**Saída:**

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

#### nbx demo cli tui --help

**Entrada:**

```bash
nbx demo cli tui --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.471`

**Saída:**

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

**Entrada:**

```bash
nbx demo cli tui --theme
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.196`

**Saída:**

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

**Entrada:**

```bash
nbx dev django-model tui --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `4.369`

**Saída:**

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

**Entrada:**

```bash
nbx demo dev django-model tui --help
```

**Código de saída:** `0`  ·  **Tempo de parede (s):** `3.970`

**Saída:**

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
