# NetBox CLI — captured command input and output

This file is **machine-generated**. Regenerate with:

```bash
cd /path/to/netbox-cli
uv sync --group docs --group dev   # once
uv run nbx docs generate-capture            # demo profile (default)
uv run nbx docs generate-capture --live     # default profile (real NetBox)
# or: uv run python docs/generate_command_docs.py
```

Run the capture **in the background** (log + pid):

```bash
./docs/run_capture_in_background.sh
```

## Generation metadata

- **UTC time:** `2026-03-23T19:36:19.521095+00:00`
- **Profile used:** **demo profile** (`nbx demo …` commands → demo.netbox.dev)
- **Effective NetBox URL:** `https://demo.netbox.dev`
- **Effective timeout (s):** `30`
- **Token configured:** `False`

> Live API calls reflect whatever is reachable at the configured URL. Connection errors and 401/403 responses are still useful documentation of real CLI behavior.

> **Typer `CliRunner` quirk:** help banners may show `Usage: root` instead of `Usage: nbx`. The installed `nbx` script uses the correct name.

---

## Top-level

### nbx --help

**Input:**

```bash
nbx --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.922`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root [OPTIONS] COMMAND [ARGS]...                                        
                                                                                
 NetBox API-first CLI/TUI. Dynamic command form: nbx <group> <resource>         
 <action>                                                                       
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ init            Create or update the default NetBox CLI profile.             │
│ config          Show the current default profile configuration.              │
│ groups          List all available OpenAPI app groups.                       │
│ resources       List resources available within a group.                     │
│ ops             Show available HTTP operations for a resource.               │
│ call            Call an arbitrary NetBox API path.                           │
│ tui             Launch the interactive NetBox terminal UI.                   │
│ logs            Show recent application logs from the shared on-disk log     │
│                 file.                                                        │
│ cli             CLI utilities: interactive command builder and helpers.      │
│ docs            Generate reference documentation (captured CLI               │
│                 input/output).                                               │
│ demo            NetBox demo.netbox.dev profile and command tree.             │
│ dev             Developer-focused tools and experimental interfaces.         │
│ circuits        OpenAPI app group: circuits           

… (truncated by character limit)
```

---

### nbx init --help

**Input:**

```bash
nbx init --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.953`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root init [OPTIONS]                                                     
                                                                                
 Create or update the default NetBox CLI profile.                               
                                                                                

… (10 more lines truncated)
```

---

### nbx config --help

**Input:**

```bash
nbx config --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.932`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root config [OPTIONS]                                                   
                                                                                
 Show the current default profile configuration.                                
                                                                                

… (5 more lines truncated)
```

---

### nbx groups --help

**Input:**

```bash
nbx groups --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.999`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root groups [OPTIONS]                                                   
                                                                                
 List all available OpenAPI app groups.                                         
                                                                                

… (4 more lines truncated)
```

---

### nbx resources --help

**Input:**

```bash
nbx resources --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.841`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root resources [OPTIONS] GROUP                                          
                                                                                
 List resources available within a group.                                       
                                                                                

… (7 more lines truncated)
```

---

### nbx ops --help

**Input:**

```bash
nbx ops --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.711`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root ops [OPTIONS] GROUP RESOURCE                                       
                                                                                
 Show available HTTP operations for a resource.                                 
                                                                                

… (8 more lines truncated)
```

---

### nbx call --help

**Input:**

```bash
nbx call --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.878`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root call [OPTIONS] METHOD PATH                                         
                                                                                
 Call an arbitrary NetBox API path.                                             
                                                                                

… (15 more lines truncated)
```

---

### nbx tui --help

**Input:**

```bash
nbx tui --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.677`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root tui [OPTIONS]                                                      
                                                                                
 Launch the interactive NetBox terminal UI.                                     
                                                                                

… (6 more lines truncated)
```

---

### nbx tui --theme

**Input:**

```bash
nbx tui --theme
```

**Exit code:** `0`  ·  **Wall time (s):** `1.852`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
Available themes:
- dracula
- netbox-dark
- netbox-light
- onedark-pro

… (1 more lines truncated)
```

---

### nbx docs --help

**Input:**

```bash
nbx docs --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.909`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root docs [OPTIONS] COMMAND [ARGS]...                                   
                                                                                
 Generate reference documentation (captured CLI input/output).                  
                                                                                

… (8 more lines truncated)
```

---

### nbx docs generate-capture --help

**Input:**

```bash
nbx docs generate-capture --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.947`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root docs generate-capture [OPTIONS]                                    
                                                                                
 Capture every nbx command (input + output) and write                           
 docs/generated/nbx-command-capture.md.                                         
                                                                                
 By default live-API specs run through ``nbx demo …`` (demo.netbox.dev).        
 Pass ``--live`` to run them against your configured default profile instead.   
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --output       -o                   PATH                Markdown             │
│                                                         destination.         │
│                                                         Default:             │
│                                                         <repo>/docs/generat… │
│ --raw-dir                           PATH                Raw JSON artifacts   │
│                                                         directory. Default:  │
│                                                         <repo>/docs/generat… │
│ --max-lines                         INTEGER             Max lines per        │
│                                                         command output in    │
│                                                         the Markdown.        │
│                                                         [default: 200]       │
│ --max-chars                         INTEGER             Max chars per        │
│                                                         command output in    │
│                                                         the Markdown.        │
│                                                       

… (truncated by character limit)
```

---

## Logs Viewer

### nbx logs --help

**Input:**

```bash
nbx logs --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.878`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root logs [OPTIONS]                                                     
                                                                                
 Show recent application logs from the shared on-disk log file.                 
                                                                                

… (9 more lines truncated)
```

---

## Developer Tools

### nbx dev --help

**Input:**

```bash
nbx dev --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.816`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root dev [OPTIONS] COMMAND [ARGS]...                                    
                                                                                
 Developer-focused tools and experimental interfaces.                           
                                                                                

… (9 more lines truncated)
```

---

### nbx dev tui --help

**Input:**

```bash
nbx dev tui --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.797`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root dev tui [OPTIONS]                                                  
                                                                                
 Launch the developer request workbench TUI.                                    
                                                                                

… (6 more lines truncated)
```

---

### nbx dev tui --theme

**Input:**

```bash
nbx dev tui --theme
```

**Exit code:** `0`  ·  **Wall time (s):** `2.529`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
Available themes:
- dracula
- netbox-dark
- netbox-light
- onedark-pro

… (1 more lines truncated)
```

---

### nbx dev http --help

**Input:**

```bash
nbx dev http --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.762`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root dev http [OPTIONS] COMMAND [ARGS]...                               
                                                                                
 Direct HTTP operations mapped from OpenAPI paths (nbx dev http <method> --path 
 ...).                                                                          

… (14 more lines truncated)
```

---

### nbx dev http get --help

**Input:**

```bash
nbx dev http get --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.765`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root dev http get [OPTIONS]                                             
                                                                                
 GET a list or detail endpoint. Use --id for a single object.                   
                                                                                

… (14 more lines truncated)
```

---

### nbx dev http post --help

**Input:**

```bash
nbx dev http post --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.990`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root dev http post [OPTIONS]                                            
                                                                                
 POST to create a new object.                                                   
                                                                                

… (16 more lines truncated)
```

---

### nbx dev http put --help

**Input:**

```bash
nbx dev http put --help
```

**Exit code:** `0`  ·  **Wall time (s):** `2.012`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root dev http put [OPTIONS]                                             
                                                                                
 PUT to fully replace an existing object. Requires --id.                        
                                                                                

… (16 more lines truncated)
```

---

### nbx dev http patch --help

**Input:**

```bash
nbx dev http patch --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.870`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root dev http patch [OPTIONS]                                           
                                                                                
 PATCH to partially update an existing object. Requires --id.                   
                                                                                

… (16 more lines truncated)
```

---

### nbx dev http delete --help

**Input:**

```bash
nbx dev http delete --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.936`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root dev http delete [OPTIONS]                                          
                                                                                
 DELETE an object by ID. Requires --id.                                         
                                                                                

… (10 more lines truncated)
```

---

### nbx dev http paths --help

**Input:**

```bash
nbx dev http paths --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.863`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root dev http paths [OPTIONS] [SEARCH]                                  
                                                                                
 List all OpenAPI paths from the bundled NetBox schema.                         
                                                                                

… (10 more lines truncated)
```

---

### nbx dev http ops --help

**Input:**

```bash
nbx dev http ops --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.743`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root dev http ops [OPTIONS]                                             
                                                                                
 Show available HTTP operations for a specific OpenAPI path.                    
                                                                                

… (5 more lines truncated)
```

---

### nbx dev http paths

**Input:**

```bash
nbx dev http paths
```

**Exit code:** `0`  ·  **Wall time (s):** `2.144`

*Output truncated for this doc (max 5 lines / 2000 chars).*

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
│ /api/circuits/circuits/{id}/                          

… (truncated by character limit)
```

---

### nbx dev http ops --path /api/dcim/devices/

**Input:**

```bash
nbx dev http ops --path /api/dcim/devices/
```

**Exit code:** `0`  ·  **Wall time (s):** `1.852`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
            Operations: /api/dcim/devices/             
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Method ┃ Operation ID                     ┃ Summary ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ GET    │ dcim_devices_list                │ -       │

… (5 more lines truncated)
```

---

## Demo profile

### nbx demo --help

**Input:**

```bash
nbx demo --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.890`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

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
│ config          Show the configured demo profile settings.                   │
│ test            Test connectivity to demo.netbox.dev using the configured    │
│                 demo profile.                                                │
│ reset           Remove the saved demo profile configuration.                 │
│ tui             Launch the TUI against the demo profile.                     │
│ cli             CLI builder tools against the demo.netbox.dev profile.       │
│ dev             Developer-focused tools against the demo.netbox.dev profile. │
│ circuits        OpenAPI app group: circuits                                  │
│ core            OpenAPI app group: core                                      │
│ dcim            OpenAPI app group: dcim               

… (truncated by character limit)
```

---

### nbx demo init --help

**Input:**

```bash
nbx demo init --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.858`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root demo init [OPTIONS]                                                
                                                                                
 Authenticate with demo.netbox.dev via Playwright and save the demo profile.    
                                                                                

… (20 more lines truncated)
```

---

### nbx demo config --help

**Input:**

```bash
nbx demo config --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.973`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root demo config [OPTIONS]                                              
                                                                                
 Show the configured demo profile settings.                                     
                                                                                

… (5 more lines truncated)
```

---

### nbx demo test --help

**Input:**

```bash
nbx demo test --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.729`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root demo test [OPTIONS]                                                
                                                                                
 Test connectivity to demo.netbox.dev using the configured demo profile.        
                                                                                

… (4 more lines truncated)
```

---

### nbx demo reset --help

**Input:**

```bash
nbx demo reset --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.786`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root demo reset [OPTIONS]                                               
                                                                                
 Remove the saved demo profile configuration.                                   
                                                                                

… (4 more lines truncated)
```

---

### nbx demo tui --help

**Input:**

```bash
nbx demo tui --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.871`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root demo tui [OPTIONS]                                                 
                                                                                
 Launch the TUI against the demo profile.                                       
                                                                                

… (6 more lines truncated)
```

---

### nbx demo tui --theme

**Input:**

```bash
nbx demo tui --theme
```

**Exit code:** `0`  ·  **Wall time (s):** `1.934`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
Available themes:
- dracula
- netbox-dark
- netbox-light
- onedark-pro

… (1 more lines truncated)
```

---

### nbx demo dev --help

**Input:**

```bash
nbx demo dev --help
```

**Exit code:** `0`  ·  **Wall time (s):** `2.009`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root demo dev [OPTIONS] COMMAND [ARGS]...                               
                                                                                
 Developer-focused tools against the demo.netbox.dev profile.                   
                                                                                

… (9 more lines truncated)
```

---

### nbx demo dev tui --help

**Input:**

```bash
nbx demo dev tui --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.722`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root demo dev tui [OPTIONS]                                             
                                                                                
 Launch the developer request workbench TUI against the demo profile.           
                                                                                

… (6 more lines truncated)
```

---

### nbx demo dev tui --theme

**Input:**

```bash
nbx demo dev tui --theme
```

**Exit code:** `0`  ·  **Wall time (s):** `2.090`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
Available themes:
- dracula
- netbox-dark
- netbox-light
- onedark-pro

… (1 more lines truncated)
```

---

## Schema Discovery

### nbx groups

**Input:**

```bash
nbx groups
```

**Exit code:** `0`  ·  **Wall time (s):** `2.450`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
circuits
core
dcim
extras
ipam

… (6 more lines truncated)
```

---

### nbx resources dcim

**Input:**

```bash
nbx resources dcim
```

**Exit code:** `0`  ·  **Wall time (s):** `1.950`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
cable-terminations
cables
connected-device
console-port-templates
console-ports

… (40 more lines truncated)
```

---

### nbx ops dcim devices

**Input:**

```bash
nbx ops dcim devices
```

**Exit code:** `0`  ·  **Wall time (s):** `2.319`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                  dcim/devices                                  
┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Method ┃ Path                             ┃ Operation ID                     ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ DELETE │ /api/dcim/devices/               │ dcim_devices_bulk_destroy        │

… (10 more lines truncated)
```

---

### nbx resources ipam

**Input:**

```bash
nbx resources ipam
```

**Exit code:** `0`  ·  **Wall time (s):** `2.162`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
aggregates
asn-ranges
asns
fhrp-group-assignments
fhrp-groups

… (13 more lines truncated)
```

---

## Dynamic Commands

### nbx dcim --help

**Input:**

```bash
nbx dcim --help
```

**Exit code:** `0`  ·  **Wall time (s):** `2.014`

*Output truncated for this doc (max 5 lines / 2000 chars).*

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
│ interfaces                     Resource: dcim/interfac

… (truncated by character limit)
```

---

### nbx dcim devices --help

**Input:**

```bash
nbx dcim devices --help
```

**Exit code:** `0`  ·  **Wall time (s):** `1.913`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root dcim devices [OPTIONS] COMMAND [ARGS]...                           
                                                                                
 Resource: dcim/devices                                                         
                                                                                

… (12 more lines truncated)
```

---

### nbx dcim devices list --help

**Input:**

```bash
nbx dcim devices list --help
```

**Exit code:** `0`  ·  **Wall time (s):** `2.860`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root dcim devices list [OPTIONS]                                        
                                                                                
 list dcim/devices                                                              
                                                                                

… (16 more lines truncated)
```

---

### nbx ipam prefixes --help

**Input:**

```bash
nbx ipam prefixes --help
```

**Exit code:** `0`  ·  **Wall time (s):** `2.888`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root ipam prefixes [OPTIONS] COMMAND [ARGS]...                          
                                                                                
 Resource: ipam/prefixes                                                        
                                                                                

… (12 more lines truncated)
```

---

### nbx dcim interfaces get --help

**Input:**

```bash
nbx dcim interfaces get --help
```

**Exit code:** `0`  ·  **Wall time (s):** `2.243`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root dcim interfaces get [OPTIONS]                                      
                                                                                
 get dcim/interfaces                                                            
                                                                                

… (16 more lines truncated)
```

---

### nbx circuits circuit-terminations get --help

**Input:**

```bash
nbx circuits circuit-terminations get --help
```

**Exit code:** `0`  ·  **Wall time (s):** `2.472`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
                                                                                
 Usage: root circuits circuit-terminations get [OPTIONS]                        
                                                                                
 get circuits/circuit-terminations                                              
                                                                                

… (16 more lines truncated)
```

---

## Live API — demo.netbox.dev

### nbx demo dcim devices list

**Input:**

```bash
nbx demo dcim devices list --markdown
```

**Exit code:** `0`  ·  **Wall time (s):** `3.459`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
Status: 200
| ID | Name | Display | Status | Role | Site | Location | Tenant |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 27 | dmi01-akron-pdu01 | dmi01-akron-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"PDU","id":5,"name":"PDU","slug":"pdu","url":"https://demo.netbox.dev/api/dcim/device-roles/5/","virtualmachine_count":0} | {"description":"","display":"DM-Akron","id":2,"name":"DM-Akron","slug":"dm-akron","url":"https://demo.netbox.dev/api/dcim/sites/2/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
| 1 | dmi01-akron-rtr01 | dmi01-akron-rtr01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Router","id":1,"name":"Router","slug":"router","url":"https://demo.netbox.dev/api/dcim/device-roles/1/","virtualmachine_count":0} | {"description":"","display":"DM-Akron","id":2,"name":"DM-Akron","slug":"dm-akron","url":"https://demo.netbox.dev/api/dcim/sites/2/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
| 14 | dmi01-akron-sw01 | dmi01-akron-sw01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Access Switch","id":4,"name":"Access Switch","slug":"access-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/4/","virtualmachine_count":0} | {"description":"","display":"DM-Akron","id":2,"name":"DM-Akron","slug":"dm-akron","url":"https://demo.netbox.dev/api/dcim/sites/2/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
| 34 | dmi01-albany-pdu01 | dmi01-albany-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":

… (truncated by character limit)
```

---

### nbx demo ipam prefixes list

**Input:**

```bash
nbx demo ipam prefixes list --markdown
```

**Exit code:** `0`  ·  **Wall time (s):** `2.995`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
Status: 200
| ID | Display | Status | Role | Prefix | VLAN | Tenant |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 10.112.0.0/15 | {"label":"Container","value":"container"} | - | 10.112.0.0/15 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
| 2 | 10.112.0.0/17 | {"label":"Container","value":"container"} | - | 10.112.0.0/17 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
| 3 | 10.112.128.0/17 | {"label":"Container","value":"container"} | - | 10.112.128.0/17 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
| 60 | 10.112.128.0/22 | {"label":"Container","value":"container"} | - | 10.112.128.0/22 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
| 7 | 10.112.128.0/28 | {"label":"Active","value":"active"} | {"description":"","display":"Management","id":4,"name":"Management","slug":"management","url":"https://demo.netbox.dev/api/ipam/roles/4/"} | 10.112.128.0/28 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
| 8 | 10.112.129.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Data","id":1,"name":"Access - Data","slug":"access-data","url":"https://demo.netbox.dev/api/ipam/roles/1/"} | 10.112.129.0/24 | {"description":"","display":"Data (100)","id":1,"name":"Data","url":"https://demo.netbox.dev/api/ipam/vlans/1/","vid":100} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","

… (truncated by character limit)
```

---

### nbx demo dcim sites list

**Input:**

```bash
nbx demo dcim sites list --markdown
```

**Exit code:** `0`  ·  **Wall time (s):** `2.780`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
Status: 200
| ID | Name | Display | Status | Tenant |
| --- | --- | --- | --- | --- |
| 26 | Amsterdam-DC | Amsterdam-DC | {"label":"Active","value":"active"} | - |
| 24 | Butler Communications | Butler Communications | {"label":"Active","value":"active"} | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
| 22 | D. S. Weaver Labs | D. S. Weaver Labs | {"label":"Active","value":"active"} | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
| 27 | Demo site with contact | Demo site with contact | {"label":"Active","value":"active"} | - |
| 2 | DM-Akron | DM-Akron | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
| 3 | DM-Albany | DM-Albany | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
| 4 | DM-Binghamton | DM-Binghamton | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
| 5 | DM-Buffalo | DM-Buffalo | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
| 6 | DM-Camden | DM-Camden | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
| 7 | DM-Nashua | DM-Nashua | {"

… (truncated by character limit)
```

---

## Cable Trace — demo.netbox.dev

### nbx demo dcim interfaces get --id 1 --trace

**Input:**

```bash
nbx demo dcim interfaces get --id 1 --trace --markdown
```

**Exit code:** `0`  ·  **Wall time (s):** `3.015`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
Status: 200
| Field | Value |
| --- | --- |
| ID | 1 |
| Name | GigabitEthernet0/0/0 |
| Display | GigabitEthernet0/0/0 |
| Label |  |
| Type | {"label":"SFP (1GE)","value":"1000base-x-sfp"} |
| Device | {"description":"","display":"dmi01-akron-rtr01","id":1,"name":"dmi01-akron-rtr01","url":"https://demo.netbox.dev/api/dcim/devices/1/"} |
| Description |  |
| URL | https://demo.netbox.dev/api/dcim/interfaces/1/ |
| Connected Endpoints Type | circuits.providernetwork |
| Link Peers Type | circuits.circuittermination |
| Poe Type | - |
| Rf Role | - |
| MAC Address | - |
| Primary MAC Address | - |
| Untagged VLAN | - |
| Display URL | https://demo.netbox.dev/dcim/interfaces/1/ |
| Occupied | true |
| Bridge | - |
| Bridge Interfaces | [] |
| Cable | {"description":"","display":"#7","id":7,"label":"","url":"https://demo.netbox.dev/api/dcim/cables/7/"} |
| Cable End | B |
| Connected Endpoints | [{"description":"","display":"Level3 MPLS","id":1,"name":"Level3 MPLS","url":"https://demo.netbox.dev/api/circuits/provider-networks/1/"}] |
| Connected Endpoints Reachable | true |
| Count FHRP Groups | 0 |
| Count Ipaddresses | 0 |
| Custom Fields | {} |
| Duplex | - |
| Enabled | true |
| L2VPN Termination | - |
| Lag | - |
| Link Peers | [{"_occupied":true,"cable":{"description":"","display":"#7","id":7,"label":"","url":"https://demo.netbox.dev/api/dcim/cables/7/"},"circuit":{"cid":"KKDG4923","description":"","display":"KKDG4923","id":1,"provider":{"description":"","display":"Level 3","id":5,"name":"Level 3","slug":"level-3","url":"https://demo.netbox.dev/api/circuits/providers/5/"},"url":"https://demo.netbox.dev/api/circuits/circuits/1/"},"description":"","display":"KKDG4923: Termination Z","id":1,"term_side":"Z","url":"https://demo.netbox.dev/api/circuits/circuit-terminations/1/"}] |
| MAC Addresses | [] |
| Mark Connected | false |
| Mgmt Only | false |
| Mode | - |
| Module | - |
| Mtu | - |
| Owner | - |
| Parent | - |
| Poe Mode | - |
| Qinq Svlan | - |
| Rf Channel |

… (truncated by character limit)
```

---

### nbx demo dcim interfaces get --id 1 --trace-only

**Input:**

```bash
nbx demo dcim interfaces get --id 1 --trace-only --markdown
```

**Exit code:** `0`  ·  **Wall time (s):** `2.080`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
Cable Trace:
┌────────────────────────────────────┐
│         dmi01-akron-rtr01          │
│        GigabitEthernet0/0/0        │
└────────────────────────────────────┘

… (9 more lines truncated)
```

---

### nbx demo circuits circuit-terminations get --id 15 --trace

**Input:**

```bash
nbx demo circuits circuit-terminations get --id 15 --trace --markdown
```

**Exit code:** `0`  ·  **Wall time (s):** `2.767`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
Status: 200
| Field | Value |
| --- | --- |
| ID | 15 |
| Display | DEOW4921: Termination Z |
| Description |  |
| URL | https://demo.netbox.dev/api/circuits/circuit-terminations/15/ |
| Termination ID | 14 |
| Xconnect ID |  |
| Link Peers Type | dcim.interface |
| Termination Type | dcim.site |
| Display URL | https://demo.netbox.dev/circuits/circuit-terminations/15/ |
| Occupied | true |
| Cable | {"description":"","display":"#1","id":1,"label":"","url":"https://demo.netbox.dev/api/dcim/cables/1/"} |
| Cable End | A |
| Circuit | {"cid":"DEOW4921","description":"","display":"DEOW4921","id":14,"provider":{"description":"","display":"Level 3","id":5,"name":"Level 3","slug":"level-3","url":"https://demo.netbox.dev/api/circuits/providers/5/"},"url":"https://demo.netbox.dev/api/circuits/circuits/14/"} |
| Custom Fields | {} |
| Link Peers | [{"_occupied":true,"cable":{"description":"","display":"#1","id":1,"label":"","url":"https://demo.netbox.dev/api/dcim/cables/1/"},"description":"","device":{"description":"","display":"dmi01-yonkers-rtr01","id":13,"name":"dmi01-yonkers-rtr01","url":"https://demo.netbox.dev/api/dcim/devices/13/"},"display":"GigabitEthernet0/0/0","id":157,"name":"GigabitEthernet0/0/0","url":"https://demo.netbox.dev/api/dcim/interfaces/157/"}] |
| Mark Connected | false |
| Port Speed | - |
| Pp Info |  |
| Tags | [] |
| Term Side | Z |
| Termination | {"description":"","display":"DM-Yonkers","id":14,"name":"DM-Yonkers","slug":"dm-yonkers","url":"https://demo.netbox.dev/api/dcim/sites/14/"} |
| Upstream Speed | - |
| Created | 2021-04-14T00:00:00Z |
| Last Updated | 2021-04-14T17:36:14.032000Z |
Cable Trace:
┌────────────────────────────────────┐
│        dmi01-yonkers-rtr01         │
│        GigabitEthernet0/0/0        │
└────────────────────────────────────┘
                │
                │  Cable #1
                │  Connected
                │
                │
                │
                │
┌────────────────────────────────────┐
│      

… (truncated by character limit)
```

---

### nbx demo circuits circuit-terminations get --id 15 --trace-only

**Input:**

```bash
nbx demo circuits circuit-terminations get --id 15 --trace-only --markdown
```

**Exit code:** `0`  ·  **Wall time (s):** `2.192`

*Output truncated for this doc (max 5 lines / 2000 chars).*

**Output:**

```text
Cable Trace:
┌────────────────────────────────────┐
│        dmi01-yonkers-rtr01         │
│        GigabitEthernet0/0/0        │
└────────────────────────────────────┘

… (28 more lines truncated)
```

---
