# Core Commands

## `nbx --help`

=== ":material-console: Command"

    ```bash
    nbx --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.780s</span>

---

## `nbx init --help`

=== ":material-console: Command"

    ```bash
    nbx init --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx init --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.430s</span>

---

## `nbx config --help`

=== ":material-console: Command"

    ```bash
    nbx config --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx config --help
    ```

    ```text
                                                                                    
     Usage: nbx config [OPTIONS]                                                    
                                                                                    
     Show the current default profile configuration.                                
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --show-token          Include API token in output                            │
    │ --help                Show this message and exit.                            │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.442s</span>

---

## `nbx logs --help`

=== ":material-console: Command"

    ```bash
    nbx logs --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx logs --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.509s</span>

---

## `nbx docs --help`

=== ":material-console: Command"

    ```bash
    nbx docs --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx docs --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.746s</span>

---

## `nbx docs generate-capture --help`

=== ":material-console: Command"

    ```bash
    nbx docs generate-capture --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx docs generate-capture --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.472s</span>

---
