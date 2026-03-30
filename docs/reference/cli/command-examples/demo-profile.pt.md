# Demo Profile

## `nbx demo --help`

=== ":material-console: Comando"

    ```bash
    nbx demo --help
    ```

=== ":material-text-box-outline: Saída"

    ```bash
    nbx demo --help
    ```

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

<span class="nbx-badge nbx-badge--ok">saída&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.922s</span>

---

## `nbx demo init --help`

=== ":material-console: Comando"

    ```bash
    nbx demo init --help
    ```

=== ":material-text-box-outline: Saída"

    ```bash
    nbx demo init --help
    ```

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

<span class="nbx-badge nbx-badge--ok">saída&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.930s</span>

---

## `nbx demo config --help`

=== ":material-console: Comando"

    ```bash
    nbx demo config --help
    ```

=== ":material-text-box-outline: Saída"

    ```bash
    nbx demo config --help
    ```

    ```text
                                                                                    
     Usage: nbx demo config [OPTIONS]                                               
                                                                                    
     Show the configured demo profile settings.                                     
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --show-token          Include API token in output                            │
    │ --help                Show this message and exit.                            │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">saída&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.755s</span>

---

## `nbx demo dev --help`

=== ":material-console: Comando"

    ```bash
    nbx demo dev --help
    ```

=== ":material-text-box-outline: Saída"

    ```bash
    nbx demo dev --help
    ```

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

<span class="nbx-badge nbx-badge--ok">saída&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.848s</span>

---

## `nbx demo cli --help`

=== ":material-console: Comando"

    ```bash
    nbx demo cli --help
    ```

=== ":material-text-box-outline: Saída"

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

<span class="nbx-badge nbx-badge--ok">saída&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.791s</span>

---

## `nbx demo dev django-model --help`

=== ":material-console: Comando"

    ```bash
    nbx demo dev django-model --help
    ```

=== ":material-text-box-outline: Saída"

    ```bash
    nbx demo dev django-model --help
    ```

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

<span class="nbx-badge nbx-badge--ok">saída&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.895s</span>

---

## `nbx demo config`

=== ":material-console: Comando"

    ```bash
    nbx demo config
    ```

=== ":material-text-box-outline: Saída"

    ```bash
    nbx demo config
    ```

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

<span class="nbx-badge nbx-badge--ok">saída&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.726s</span>

---
