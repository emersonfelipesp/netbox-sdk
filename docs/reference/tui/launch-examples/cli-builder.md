# CLI Builder

## `nbx cli --help`

=== ":material-console: Command"

    ```bash
    nbx cli --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx cli --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.407s</span>

---

## `nbx cli tui --help`

=== ":material-console: Command"

    ```bash
    nbx cli tui --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx cli tui --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.402s</span>

---

## `nbx demo cli --help`

=== ":material-console: Command"

    ```bash
    nbx demo cli --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo cli --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.666s</span>

---

## `nbx demo cli tui --help`

=== ":material-console: Command"

    ```bash
    nbx demo cli tui --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo cli tui --help
    ```

    ```text
                                                                                    
     Usage: nbx demo cli tui [OPTIONS]                                              
                                                                                    
     Launch the interactive CLI command builder against the demo profile.           
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --theme          Theme selector. Use '--theme' to list available themes or   │
    │                  '--theme <name>' to launch with one.                        │
    │ --help           Show this message and exit.                                 │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.400s</span>

---

## `nbx demo cli tui --theme`

=== ":material-console: Command"

    ```bash
    nbx demo cli tui --theme
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo cli tui --theme
    ```

    ```text
    Available themes:
    - dracula
    - netbox-dark
    - netbox-light
    - onedark-pro
    - tokyo-night
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.582s</span>

---
