# Top-level

### `nbx --help`

=== ":material-console: Command"

    ```bash
    nbx --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.922s</span>

---

### `nbx init --help`

=== ":material-console: Command"

    ```bash
    nbx init --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx init --help
    ```

    ```text
                                                                                    
     Usage: root init [OPTIONS]                                                     
                                                                                    
     Create or update the default NetBox CLI profile.                               
                                                                                    
    
    … (10 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.953s</span>

---

### `nbx config --help`

=== ":material-console: Command"

    ```bash
    nbx config --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx config --help
    ```

    ```text
                                                                                    
     Usage: root config [OPTIONS]                                                   
                                                                                    
     Show the current default profile configuration.                                
                                                                                    
    
    … (5 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.932s</span>

---

### `nbx groups --help`

=== ":material-console: Command"

    ```bash
    nbx groups --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx groups --help
    ```

    ```text
                                                                                    
     Usage: root groups [OPTIONS]                                                   
                                                                                    
     List all available OpenAPI app groups.                                         
                                                                                    
    
    … (4 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.999s</span>

---

### `nbx resources --help`

=== ":material-console: Command"

    ```bash
    nbx resources --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx resources --help
    ```

    ```text
                                                                                    
     Usage: root resources [OPTIONS] GROUP                                          
                                                                                    
     List resources available within a group.                                       
                                                                                    
    
    … (7 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.841s</span>

---

### `nbx ops --help`

=== ":material-console: Command"

    ```bash
    nbx ops --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx ops --help
    ```

    ```text
                                                                                    
     Usage: root ops [OPTIONS] GROUP RESOURCE                                       
                                                                                    
     Show available HTTP operations for a resource.                                 
                                                                                    
    
    … (8 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.711s</span>

---

### `nbx call --help`

=== ":material-console: Command"

    ```bash
    nbx call --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx call --help
    ```

    ```text
                                                                                    
     Usage: root call [OPTIONS] METHOD PATH                                         
                                                                                    
     Call an arbitrary NetBox API path.                                             
                                                                                    
    
    … (15 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.878s</span>

---

### `nbx tui --help`

=== ":material-console: Command"

    ```bash
    nbx tui --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx tui --help
    ```

    ```text
                                                                                    
     Usage: root tui [OPTIONS]                                                      
                                                                                    
     Launch the interactive NetBox terminal UI.                                     
                                                                                    
    
    … (6 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.677s</span>

---

### `nbx tui --theme`

=== ":material-console: Command"

    ```bash
    nbx tui --theme
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx tui --theme
    ```

    ```text
    Available themes:
    - dracula
    - netbox-dark
    - netbox-light
    - onedark-pro
    
    … (1 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.852s</span>

---

### `nbx docs --help`

=== ":material-console: Command"

    ```bash
    nbx docs --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx docs --help
    ```

    ```text
                                                                                    
     Usage: root docs [OPTIONS] COMMAND [ARGS]...                                   
                                                                                    
     Generate reference documentation (captured CLI input/output).                  
                                                                                    
    
    … (8 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.909s</span>

---

### `nbx docs generate-capture --help`

=== ":material-console: Command"

    ```bash
    nbx docs generate-capture --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx docs generate-capture --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.947s</span>

---
