# Demo profile

### `nbx demo --help`

=== ":material-console: Command"

    ```bash
    nbx demo --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.890s</span>

---

### `nbx demo init --help`

=== ":material-console: Command"

    ```bash
    nbx demo init --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo init --help
    ```

    ```text
                                                                                    
     Usage: root demo init [OPTIONS]                                                
                                                                                    
     Authenticate with demo.netbox.dev via Playwright and save the demo profile.    
                                                                                    
    
    … (20 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.858s</span>

---

### `nbx demo config --help`

=== ":material-console: Command"

    ```bash
    nbx demo config --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo config --help
    ```

    ```text
                                                                                    
     Usage: root demo config [OPTIONS]                                              
                                                                                    
     Show the configured demo profile settings.                                     
                                                                                    
    
    … (5 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.973s</span>

---

### `nbx demo test --help`

=== ":material-console: Command"

    ```bash
    nbx demo test --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo test --help
    ```

    ```text
                                                                                    
     Usage: root demo test [OPTIONS]                                                
                                                                                    
     Test connectivity to demo.netbox.dev using the configured demo profile.        
                                                                                    
    
    … (4 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.729s</span>

---

### `nbx demo reset --help`

=== ":material-console: Command"

    ```bash
    nbx demo reset --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo reset --help
    ```

    ```text
                                                                                    
     Usage: root demo reset [OPTIONS]                                               
                                                                                    
     Remove the saved demo profile configuration.                                   
                                                                                    
    
    … (4 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.786s</span>

---

### `nbx demo tui --help`

=== ":material-console: Command"

    ```bash
    nbx demo tui --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo tui --help
    ```

    ```text
                                                                                    
     Usage: root demo tui [OPTIONS]                                                 
                                                                                    
     Launch the TUI against the demo profile.                                       
                                                                                    
    
    … (6 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.871s</span>

---

### `nbx demo tui --theme`

=== ":material-console: Command"

    ```bash
    nbx demo tui --theme
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo tui --theme
    ```

    ```text
    Available themes:
    - dracula
    - netbox-dark
    - netbox-light
    - onedark-pro
    
    … (1 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.934s</span>

---

### `nbx demo dev --help`

=== ":material-console: Command"

    ```bash
    nbx demo dev --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo dev --help
    ```

    ```text
                                                                                    
     Usage: root demo dev [OPTIONS] COMMAND [ARGS]...                               
                                                                                    
     Developer-focused tools against the demo.netbox.dev profile.                   
                                                                                    
    
    … (9 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">2.009s</span>

---

### `nbx demo dev tui --help`

=== ":material-console: Command"

    ```bash
    nbx demo dev tui --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo dev tui --help
    ```

    ```text
                                                                                    
     Usage: root demo dev tui [OPTIONS]                                             
                                                                                    
     Launch the developer request workbench TUI against the demo profile.           
                                                                                    
    
    … (6 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.722s</span>

---

### `nbx demo dev tui --theme`

=== ":material-console: Command"

    ```bash
    nbx demo dev tui --theme
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo dev tui --theme
    ```

    ```text
    Available themes:
    - dracula
    - netbox-dark
    - netbox-light
    - onedark-pro
    
    … (1 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">2.090s</span>

---
