# Schema Discovery

### `nbx groups`

=== ":material-console: Command"

    ```bash
    nbx groups
    ```

=== ":material-text-box-outline: Output"

    ```text
    circuits
    core
    dcim
    extras
    ipam
    
    … (6 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">2.450s</span>

!!! warning "Truncated"
    Output was truncated. Full text is in `docs/generated/raw/`.

---

### `nbx resources dcim`

=== ":material-console: Command"

    ```bash
    nbx resources dcim
    ```

=== ":material-text-box-outline: Output"

    ```text
    cable-terminations
    cables
    connected-device
    console-port-templates
    console-ports
    
    … (40 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">1.950s</span>

!!! warning "Truncated"
    Output was truncated. Full text is in `docs/generated/raw/`.

---

### `nbx ops dcim devices`

=== ":material-console: Command"

    ```bash
    nbx ops dcim devices
    ```

=== ":material-text-box-outline: Output"

    ```text
                                      dcim/devices                                  
    ┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Method ┃ Path                             ┃ Operation ID                     ┃
    ┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │ DELETE │ /api/dcim/devices/               │ dcim_devices_bulk_destroy        │
    
    … (10 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">2.319s</span>

!!! warning "Truncated"
    Output was truncated. Full text is in `docs/generated/raw/`.

---

### `nbx resources ipam`

=== ":material-console: Command"

    ```bash
    nbx resources ipam
    ```

=== ":material-text-box-outline: Output"

    ```text
    aggregates
    asn-ranges
    asns
    fhrp-group-assignments
    fhrp-groups
    
    … (13 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">2.162s</span>

!!! warning "Truncated"
    Output was truncated. Full text is in `docs/generated/raw/`.

---
