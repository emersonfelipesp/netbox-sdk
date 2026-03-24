# Cable Trace — demo.netbox.dev

### `nbx demo dcim interfaces get --id 1 --trace`

=== ":material-console: Command"

    ```bash
    nbx demo dcim interfaces get --id 1 --trace --markdown
    ```

=== ":material-text-box-outline: Output"

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.015s</span>

---

### `nbx demo dcim interfaces get --id 1 --trace-only`

=== ":material-console: Command"

    ```bash
    nbx demo dcim interfaces get --id 1 --trace-only --markdown
    ```

=== ":material-text-box-outline: Output"

    ```text
    Cable Trace:
    ┌────────────────────────────────────┐
    │         dmi01-akron-rtr01          │
    │        GigabitEthernet0/0/0        │
    └────────────────────────────────────┘
    
    … (9 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">2.080s</span>

---

### `nbx demo circuits circuit-terminations get --id 15 --trace`

=== ":material-console: Command"

    ```bash
    nbx demo circuits circuit-terminations get --id 15 --trace --markdown
    ```

=== ":material-text-box-outline: Output"

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

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">2.767s</span>

---

### `nbx demo circuits circuit-terminations get --id 15 --trace-only`

=== ":material-console: Command"

    ```bash
    nbx demo circuits circuit-terminations get --id 15 --trace-only --markdown
    ```

=== ":material-text-box-outline: Output"

    ```text
    Cable Trace:
    ┌────────────────────────────────────┐
    │        dmi01-yonkers-rtr01         │
    │        GigabitEthernet0/0/0        │
    └────────────────────────────────────┘
    
    … (28 more lines truncated)
    ```

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">2.192s</span>

---
