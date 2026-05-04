# Schema Discovery

## `nbx groups --help`

=== ":material-console: Comando"

    ```bash
    nbx groups --help
    ```

=== ":material-text-box-outline: Saída"

    ```bash
    nbx groups --help
    ```

    ```text
                                                                                    
     Usage: nbx groups [OPTIONS]                                                    
                                                                                    
     List all available OpenAPI app groups.                                         
                                                                                    
    ╭─ Options ────────────────────────────────────────────────────────────────────╮
    │ --help          Show this message and exit.                                  │
    ╰──────────────────────────────────────────────────────────────────────────────╯
    ```

<span class="nbx-badge nbx-badge--ok">saída&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">4.529s</span>

---

## `nbx resources --help`

=== ":material-console: Comando"

    ```bash
    nbx resources --help
    ```

=== ":material-text-box-outline: Saída"

    ```bash
    nbx resources --help
    ```

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

<span class="nbx-badge nbx-badge--ok">saída&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">4.328s</span>

---

## `nbx ops --help`

=== ":material-console: Comando"

    ```bash
    nbx ops --help
    ```

=== ":material-text-box-outline: Saída"

    ```bash
    nbx ops --help
    ```

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

<span class="nbx-badge nbx-badge--ok">saída&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.989s</span>

---

## `nbx groups`

=== ":material-console: Comando"

    ```bash
    nbx groups
    ```

=== ":material-text-box-outline: Saída"

    ```bash
    nbx groups
    ```

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

<span class="nbx-badge nbx-badge--ok">saída&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.968s</span>

---

## `nbx resources dcim`

=== ":material-console: Comando"

    ```bash
    nbx resources dcim
    ```

=== ":material-text-box-outline: Saída"

    ```bash
    nbx resources dcim
    ```

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

<span class="nbx-badge nbx-badge--ok">saída&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">4.320s</span>

---

## `nbx ops dcim devices`

=== ":material-console: Comando"

    ```bash
    nbx ops dcim devices
    ```

=== ":material-text-box-outline: Saída"

    ```bash
    nbx ops dcim devices
    ```

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

<span class="nbx-badge nbx-badge--ok">saída&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">4.193s</span>

---
