# GraphQL and HTTP

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.451s</span>

---

## `nbx call --help`

=== ":material-console: Command"

    ```bash
    nbx call --help
    ```

=== ":material-text-box-outline: Output"

    ```bash
    nbx call --help
    ```

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.973s</span>

---
