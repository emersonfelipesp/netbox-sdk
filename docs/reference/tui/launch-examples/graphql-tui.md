# GraphQL TUI

## `nbx graphql --help`

=== ":material-console: Command"

    ```bash
    nbx graphql --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx graphql --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.736s</span>

---

## `nbx graphql tui --help`

=== ":material-console: Command"

    ```bash
    nbx graphql tui --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx graphql tui --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.667s</span>

---

## `nbx graphql tui --theme`

=== ":material-console: Command"

    ```bash
    nbx graphql tui --theme
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx graphql tui --theme
    ```

    ```text
    Available themes:
    - dracula
    - netbox-dark
    - netbox-light
    - onedark-pro
    - tokyo-night
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.919s</span>

---

## `nbx demo graphql --help`

=== ":material-console: Command"

    ```bash
    nbx demo graphql --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo graphql --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.578s</span>

---

## `nbx demo graphql tui --help`

=== ":material-console: Command"

    ```bash
    nbx demo graphql tui --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo graphql tui --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.763s</span>

---

## `nbx demo graphql tui --theme`

=== ":material-console: Command"

    ```bash
    nbx demo graphql tui --theme
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx demo graphql tui --theme
    ```

    ```text
    Available themes:
    - dracula
    - netbox-dark
    - netbox-light
    - onedark-pro
    - tokyo-night
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">4.188s</span>

---
