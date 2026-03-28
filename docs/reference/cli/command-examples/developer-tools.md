# Developer Tools

## `nbx dev --help`

=== ":material-console: Command"

    ```bash
    nbx dev --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dev --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.593s</span>

---

## `nbx dev http --help`

=== ":material-console: Command"

    ```bash
    nbx dev http --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dev http --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.427s</span>

---

## `nbx dev http get --help`

=== ":material-console: Command"

    ```bash
    nbx dev http get --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dev http get --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.475s</span>

---

## `nbx dev http post --help`

=== ":material-console: Command"

    ```bash
    nbx dev http post --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dev http post --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.460s</span>

---

## `nbx dev http put --help`

=== ":material-console: Command"

    ```bash
    nbx dev http put --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dev http put --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.757s</span>

---

## `nbx dev http patch --help`

=== ":material-console: Command"

    ```bash
    nbx dev http patch --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dev http patch --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.838s</span>

---

## `nbx dev http delete --help`

=== ":material-console: Command"

    ```bash
    nbx dev http delete --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dev http delete --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.402s</span>

---

## `nbx dev http paths --help`

=== ":material-console: Command"

    ```bash
    nbx dev http paths --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dev http paths --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.428s</span>

---

## `nbx dev http ops --help`

=== ":material-console: Command"

    ```bash
    nbx dev http ops --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dev http ops --help
    ```

    ```text
                                                                                    
     Usage: nbx dev http ops [OPTIONS]                                              
                                                                                    
     Show available HTTP operations for a specific OpenAPI path.                    
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ *  --path  -p      TEXT  API path to inspect [required]                      │
    │    --help                Show this message and exit.                         │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.414s</span>

---

## `nbx dev http paths`

=== ":material-console: Command"

    ```bash
    nbx dev http paths
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dev http paths
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.862s</span>

---

## `nbx dev http ops --path /api/dcim/devices/`

=== ":material-console: Command"

    ```bash
    nbx dev http ops --path /api/dcim/devices/
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dev http ops --path /api/dcim/devices/
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.530s</span>

---

## `nbx demo dev http get --path /api/status/`

=== ":material-console: Command"

    ```bash
    nbx demo dev http get --path /api/status/
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo dev http get --path /api/status/
    ```

    ```text
    (empty)
    ```

<span class="nbx-badge nbx-badge--err">exit&nbsp;124</span> <span class="nbx-badge nbx-badge--neutral">60.041s</span>

---

## `nbx dev django-model --help`

=== ":material-console: Command"

    ```bash
    nbx dev django-model --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dev django-model --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.598s</span>

---

## `nbx dev django-model build --help`

=== ":material-console: Command"

    ```bash
    nbx dev django-model build --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dev django-model build --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.713s</span>

---

## `nbx dev django-model fetch --help`

=== ":material-console: Command"

    ```bash
    nbx dev django-model fetch --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx dev django-model fetch --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.796s</span>

---
