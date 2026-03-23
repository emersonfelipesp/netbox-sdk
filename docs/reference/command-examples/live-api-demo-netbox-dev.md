# Live API — demo.netbox.dev

### `nbx demo dcim devices list`

=== ":material-console: Command"

    ```bash
    nbx demo dcim devices list --markdown
    ```

=== ":material-text-box-outline: Output"

    ```text
    Status: 200
    | ID | Name | Display | Status | Role | Site | Location | Tenant |
    | --- | --- | --- | --- | --- | --- | --- | --- |
    | 27 | dmi01-akron-pdu01 | dmi01-akron-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"PDU","id":5,"name":"PDU","slug":"pdu","url":"https://demo.netbox.dev/api/dcim/device-roles/5/","virtualmachine_count":0} | {"description":"","display":"DM-Akron","id":2,"name":"DM-Akron","slug":"dm-akron","url":"https://demo.netbox.dev/api/dcim/sites/2/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 1 | dmi01-akron-rtr01 | dmi01-akron-rtr01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Router","id":1,"name":"Router","slug":"router","url":"https://demo.netbox.dev/api/dcim/device-roles/1/","virtualmachine_count":0} | {"description":"","display":"DM-Akron","id":2,"name":"DM-Akron","slug":"dm-akron","url":"https://demo.netbox.dev/api/dcim/sites/2/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 14 | dmi01-akron-sw01 | dmi01-akron-sw01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Access Switch","id":4,"name":"Access Switch","slug":"access-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/4/","virtualmachine_count":0} | {"description":"","display":"DM-Akron","id":2,"name":"DM-Akron","slug":"dm-akron","url":"https://demo.netbox.dev/api/dcim/sites/2/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 34 | dmi01-albany-pdu01 | dmi01-albany-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":
    
    … (truncated by character limit)
    ```

=== ":material-code-json: JSON Output"

    ```json
    {
      "count": 79,
      "next": "https://demo.netbox.dev/api/dcim/devices/?limit=50&offset=50",
      "previous": null,
      "results": [
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": "3232",
            "environment": null
          },
          "description": "TEST",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "AP7901",
            "id": 8,
            "manufacturer": {
              "description": "",
              "display": "APC",
              "id": 11,
              "name": "APC",
              "slug": "apc",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/11/"
            },
            "model": "AP7901",
            "slug": "ap7901",
            "url": "https://demo.netbox.dev/api/dcim/device-types/8/"
          },
          "display": "dmi01-akron-pdu01",
          "display_url": "https://demo.netbox.dev/dcim/devices/27/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 27,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2026-03-23T10:39:34.986647Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-akron-pdu01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 1.0,
          "power_outlet_count": 8,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 1,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/1/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "PDU",
            "id": 5,
            "name": "PDU",
            "slug": "pdu",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/5/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Akron",
            "id": 2,
            "name": "DM-Akron",
            "slug": "dm-akron",
            "url": "https://demo.netbox.dev/api/dcim/sites/2/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/27/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {
            "syslog-servers": [
              "192.168.1.200"
            ]
          },
          "config_template": null,
          "console_port_count": 2,
          "console_server_port_count": 0,
          "created": "2020-12-20T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "ISR 1111-8P",
            "id": 6,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "ISR 1111-8P",
            "slug": "isr1111",
            "url": "https://demo.netbox.dev/api/dcim/device-types/6/"
          },
          "display": "dmi01-akron-rtr01",
          "display_url": "https://demo.netbox.dev/dcim/devices/1/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 1,
          "interface_count": 14,
          "inventory_item_count": 0,
          "last_updated": "2020-12-20T02:51:03.257000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-akron-rtr01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Cisco IOS",
            "id": 1,
            "name": "Cisco IOS",
            "slug": "cisco-ios",
            "url": "https://demo.netbox.dev/api/dcim/platforms/1/",
            "virtualmachine_count": 0
          },
          "position": 4.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 1,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/1/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Router",
            "id": 1,
            "name": "Router",
            "slug": "router",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/1/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Akron",
            "id": 2,
            "name": "DM-Akron",
            "slug": "dm-akron",
            "url": "https://demo.netbox.dev/api/dcim/sites/2/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/1/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 16,
            "display": "C9200-48P",
            "id": 7,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "C9200-48P",
            "slug": "c9200-48p",
            "url": "https://demo.netbox.dev/api/dcim/device-types/7/"
          },
          "display": "dmi01-akron-sw01",
          "display_url": "https://demo.netbox.dev/dcim/devices/14/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 14,
          "interface_count": 52,
          "inventory_item_count": 0,
          "last_updated": "2020-12-22T02:11:11.625000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-akron-sw01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 10.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 1,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/1/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Access Switch",
            "id": 4,
            "name": "Access Switch",
            "slug": "access-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/4/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Akron",
            "id": 2,
            "name": "DM-Akron",
            "slug": "dm-akron",
            "url": "https://demo.netbox.dev/api/dcim/sites/2/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/14/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "AP7901",
            "id": 8,
            "manufacturer": {
              "description": "",
              "display": "APC",
              "id": 11,
              "name": "APC",
              "slug": "apc",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/11/"
            },
            "model": "AP7901",
            "slug": "ap7901",
            "url": "https://demo.netbox.dev/api/dcim/device-types/8/"
          },
          "display": "dmi01-albany-pdu01",
          "display_url": "https://demo.netbox.dev/dcim/devices/34/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 34,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2020-12-30T19:02:55.909000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-albany-pdu01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 1.0,
          "power_outlet_count": 8,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 2,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/2/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "PDU",
            "id": 5,
            "name": "PDU",
            "slug": "pdu",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/5/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Albany",
            "id": 3,
            "name": "DM-Albany",
            "slug": "dm-albany",
            "url": "https://demo.netbox.dev/api/dcim/sites/3/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/34/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {
            "syslog-servers": [
              "192.168.1.100"
            ]
          },
          "config_template": null,
          "console_port_count": 2,
          "console_server_port_count": 0,
          "created": "2020-12-20T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "ISR 1111-8P",
            "id": 6,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "ISR 1111-8P",
            "slug": "isr1111",
            "url": "https://demo.netbox.dev/api/dcim/device-types/6/"
          },
          "display": "dmi01-albany-rtr01",
          "display_url": "https://demo.netbox.dev/dcim/devices/2/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 2,
          "interface_count": 14,
          "inventory_item_count": 0,
          "last_updated": "2020-12-20T02:51:32.863000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-albany-rtr01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Cisco IOS",
            "id": 1,
            "name": "Cisco IOS",
            "slug": "cisco-ios",
            "url": "https://demo.netbox.dev/api/dcim/platforms/1/",
            "virtualmachine_count": 0
          },
          "position": 4.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 2,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/2/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Router",
            "id": 1,
            "name": "Router",
            "slug": "router",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/1/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Albany",
            "id": 3,
            "name": "DM-Albany",
            "slug": "dm-albany",
            "url": "https://demo.netbox.dev/api/dcim/sites/3/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/2/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 16,
            "display": "C9200-48P",
            "id": 7,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "C9200-48P",
            "slug": "c9200-48p",
            "url": "https://demo.netbox.dev/api/dcim/device-types/7/"
          },
          "display": "dmi01-albany-sw01",
          "display_url": "https://demo.netbox.dev/dcim/devices/15/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 15,
          "interface_count": 52,
          "inventory_item_count": 0,
          "last_updated": "2020-12-22T02:11:11.714000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-albany-sw01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 10.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 2,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/2/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Access Switch",
            "id": 4,
            "name": "Access Switch",
            "slug": "access-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/4/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Albany",
            "id": 3,
            "name": "DM-Albany",
            "slug": "dm-albany",
            "url": "https://demo.netbox.dev/api/dcim/sites/3/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/15/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "AP7901",
            "id": 8,
            "manufacturer": {
              "description": "",
              "display": "APC",
              "id": 11,
              "name": "APC",
              "slug": "apc",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/11/"
            },
            "model": "AP7901",
            "slug": "ap7901",
            "url": "https://demo.netbox.dev/api/dcim/device-types/8/"
          },
          "display": "dmi01-binghamton-pdu01",
          "display_url": "https://demo.netbox.dev/dcim/devices/35/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 35,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2020-12-30T19:02:56.038000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-binghamton-pdu01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 1.0,
          "power_outlet_count": 8,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 3,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/3/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "PDU",
            "id": 5,
            "name": "PDU",
            "slug": "pdu",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/5/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Binghamton",
            "id": 4,
            "name": "DM-Binghamton",
            "slug": "dm-binghamton",
            "url": "https://demo.netbox.dev/api/dcim/sites/4/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/35/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {
            "syslog-servers": [
              "192.168.1.100"
            ]
          },
          "config_template": null,
          "console_port_count": 2,
          "console_server_port_count": 0,
          "created": "2020-12-20T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "ISR 1111-8P",
            "id": 6,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "ISR 1111-8P",
            "slug": "isr1111",
            "url": "https://demo.netbox.dev/api/dcim/device-types/6/"
          },
          "display": "dmi01-binghamton-rtr01",
          "display_url": "https://demo.netbox.dev/dcim/devices/3/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 3,
          "interface_count": 14,
          "inventory_item_count": 0,
          "last_updated": "2020-12-20T02:52:02.614000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-binghamton-rtr01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Cisco IOS",
            "id": 1,
            "name": "Cisco IOS",
            "slug": "cisco-ios",
            "url": "https://demo.netbox.dev/api/dcim/platforms/1/",
            "virtualmachine_count": 0
          },
          "position": 4.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 3,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/3/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Router",
            "id": 1,
            "name": "Router",
            "slug": "router",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/1/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Binghamton",
            "id": 4,
            "name": "DM-Binghamton",
            "slug": "dm-binghamton",
            "url": "https://demo.netbox.dev/api/dcim/sites/4/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/3/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 16,
            "display": "C9200-48P",
            "id": 7,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "C9200-48P",
            "slug": "c9200-48p",
            "url": "https://demo.netbox.dev/api/dcim/device-types/7/"
          },
          "display": "dmi01-binghamton-sw01",
          "display_url": "https://demo.netbox.dev/dcim/devices/16/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 16,
          "interface_count": 52,
          "inventory_item_count": 0,
          "last_updated": "2020-12-22T02:11:11.799000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-binghamton-sw01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 10.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 3,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/3/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Access Switch",
            "id": 4,
            "name": "Access Switch",
            "slug": "access-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/4/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Binghamton",
            "id": 4,
            "name": "DM-Binghamton",
            "slug": "dm-binghamton",
            "url": "https://demo.netbox.dev/api/dcim/sites/4/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/16/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "AP7901",
            "id": 8,
            "manufacturer": {
              "description": "",
              "display": "APC",
              "id": 11,
              "name": "APC",
              "slug": "apc",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/11/"
            },
            "model": "AP7901",
            "slug": "ap7901",
            "url": "https://demo.netbox.dev/api/dcim/device-types/8/"
          },
          "display": "dmi01-buffalo-pdu01",
          "display_url": "https://demo.netbox.dev/dcim/devices/36/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 36,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2020-12-30T19:02:56.155000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-buffalo-pdu01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 1.0,
          "power_outlet_count": 8,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 4,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/4/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "PDU",
            "id": 5,
            "name": "PDU",
            "slug": "pdu",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/5/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Buffalo",
            "id": 5,
            "name": "DM-Buffalo",
            "slug": "dm-buffalo",
            "url": "https://demo.netbox.dev/api/dcim/sites/5/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/36/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {
            "syslog-servers": [
              "192.168.1.100"
            ]
          },
          "config_template": null,
          "console_port_count": 2,
          "console_server_port_count": 0,
          "created": "2020-12-20T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "ISR 1111-8P",
            "id": 6,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "ISR 1111-8P",
            "slug": "isr1111",
            "url": "https://demo.netbox.dev/api/dcim/device-types/6/"
          },
          "display": "dmi01-buffalo-rtr01",
          "display_url": "https://demo.netbox.dev/dcim/devices/4/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 4,
          "interface_count": 14,
          "inventory_item_count": 0,
          "last_updated": "2020-12-20T02:52:26.146000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-buffalo-rtr01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Cisco IOS",
            "id": 1,
            "name": "Cisco IOS",
            "slug": "cisco-ios",
            "url": "https://demo.netbox.dev/api/dcim/platforms/1/",
            "virtualmachine_count": 0
          },
          "position": 4.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 4,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/4/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Router",
            "id": 1,
            "name": "Router",
            "slug": "router",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/1/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Buffalo",
            "id": 5,
            "name": "DM-Buffalo",
            "slug": "dm-buffalo",
            "url": "https://demo.netbox.dev/api/dcim/sites/5/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/4/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 16,
            "display": "C9200-48P",
            "id": 7,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "C9200-48P",
            "slug": "c9200-48p",
            "url": "https://demo.netbox.dev/api/dcim/device-types/7/"
          },
          "display": "dmi01-buffalo-sw01",
          "display_url": "https://demo.netbox.dev/dcim/devices/17/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 17,
          "interface_count": 52,
          "inventory_item_count": 0,
          "last_updated": "2020-12-22T02:11:11.883000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-buffalo-sw01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 10.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 4,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/4/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Access Switch",
            "id": 4,
            "name": "Access Switch",
            "slug": "access-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/4/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Buffalo",
            "id": 5,
            "name": "DM-Buffalo",
            "slug": "dm-buffalo",
            "url": "https://demo.netbox.dev/api/dcim/sites/5/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/17/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "AP7901",
            "id": 8,
            "manufacturer": {
              "description": "",
              "display": "APC",
              "id": 11,
              "name": "APC",
              "slug": "apc",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/11/"
            },
            "model": "AP7901",
            "slug": "ap7901",
            "url": "https://demo.netbox.dev/api/dcim/device-types/8/"
          },
          "display": "dmi01-camden-pdu01",
          "display_url": "https://demo.netbox.dev/dcim/devices/37/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 37,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2020-12-30T19:02:56.256000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-camden-pdu01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 1.0,
          "power_outlet_count": 8,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 5,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/5/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "PDU",
            "id": 5,
            "name": "PDU",
            "slug": "pdu",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/5/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Camden",
            "id": 6,
            "name": "DM-Camden",
            "slug": "dm-camden",
            "url": "https://demo.netbox.dev/api/dcim/sites/6/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/37/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {
            "syslog-servers": [
              "192.168.1.100"
            ]
          },
          "config_template": null,
          "console_port_count": 2,
          "console_server_port_count": 0,
          "created": "2020-12-20T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "ISR 1111-8P",
            "id": 6,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "ISR 1111-8P",
            "slug": "isr1111",
            "url": "https://demo.netbox.dev/api/dcim/device-types/6/"
          },
          "display": "dmi01-camden-rtr01",
          "display_url": "https://demo.netbox.dev/dcim/devices/5/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 5,
          "interface_count": 14,
          "inventory_item_count": 0,
          "last_updated": "2020-12-20T02:53:47.838000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-camden-rtr01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Cisco IOS",
            "id": 1,
            "name": "Cisco IOS",
            "slug": "cisco-ios",
            "url": "https://demo.netbox.dev/api/dcim/platforms/1/",
            "virtualmachine_count": 0
          },
          "position": 4.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 5,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/5/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Router",
            "id": 1,
            "name": "Router",
            "slug": "router",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/1/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Camden",
            "id": 6,
            "name": "DM-Camden",
            "slug": "dm-camden",
            "url": "https://demo.netbox.dev/api/dcim/sites/6/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/5/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 16,
            "display": "C9200-48P",
            "id": 7,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "C9200-48P",
            "slug": "c9200-48p",
            "url": "https://demo.netbox.dev/api/dcim/device-types/7/"
          },
          "display": "dmi01-camden-sw01",
          "display_url": "https://demo.netbox.dev/dcim/devices/18/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 18,
          "interface_count": 52,
          "inventory_item_count": 0,
          "last_updated": "2020-12-22T02:11:11.968000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-camden-sw01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 10.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 5,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/5/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Access Switch",
            "id": 4,
            "name": "Access Switch",
            "slug": "access-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/4/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Camden",
            "id": 6,
            "name": "DM-Camden",
            "slug": "dm-camden",
            "url": "https://demo.netbox.dev/api/dcim/sites/6/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/18/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "AP7901",
            "id": 8,
            "manufacturer": {
              "description": "",
              "display": "APC",
              "id": 11,
              "name": "APC",
              "slug": "apc",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/11/"
            },
            "model": "AP7901",
            "slug": "ap7901",
            "url": "https://demo.netbox.dev/api/dcim/device-types/8/"
          },
          "display": "dmi01-nashua-pdu01",
          "display_url": "https://demo.netbox.dev/dcim/devices/38/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 38,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2020-12-30T19:02:56.357000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-nashua-pdu01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 1.0,
          "power_outlet_count": 8,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 6,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/6/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "PDU",
            "id": 5,
            "name": "PDU",
            "slug": "pdu",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/5/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Nashua",
            "id": 7,
            "name": "DM-Nashua",
            "slug": "dm-nashua",
            "url": "https://demo.netbox.dev/api/dcim/sites/7/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/38/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {
            "syslog-servers": [
              "192.168.1.100"
            ]
          },
          "config_template": null,
          "console_port_count": 2,
          "console_server_port_count": 0,
          "created": "2020-12-20T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "ISR 1111-8P",
            "id": 6,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "ISR 1111-8P",
            "slug": "isr1111",
            "url": "https://demo.netbox.dev/api/dcim/device-types/6/"
          },
          "display": "dmi01-nashua-rtr01",
          "display_url": "https://demo.netbox.dev/dcim/devices/6/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 6,
          "interface_count": 14,
          "inventory_item_count": 0,
          "last_updated": "2020-12-20T02:54:08.200000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-nashua-rtr01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Cisco IOS",
            "id": 1,
            "name": "Cisco IOS",
            "slug": "cisco-ios",
            "url": "https://demo.netbox.dev/api/dcim/platforms/1/",
            "virtualmachine_count": 0
          },
          "position": 4.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 6,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/6/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Router",
            "id": 1,
            "name": "Router",
            "slug": "router",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/1/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Nashua",
            "id": 7,
            "name": "DM-Nashua",
            "slug": "dm-nashua",
            "url": "https://demo.netbox.dev/api/dcim/sites/7/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/6/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 16,
            "display": "C9200-48P",
            "id": 7,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "C9200-48P",
            "slug": "c9200-48p",
            "url": "https://demo.netbox.dev/api/dcim/device-types/7/"
          },
          "display": "dmi01-nashua-sw01",
          "display_url": "https://demo.netbox.dev/dcim/devices/19/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 19,
          "interface_count": 52,
          "inventory_item_count": 0,
          "last_updated": "2020-12-22T02:11:12.071000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-nashua-sw01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 10.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 6,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/6/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Access Switch",
            "id": 4,
            "name": "Access Switch",
            "slug": "access-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/4/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Nashua",
            "id": 7,
            "name": "DM-Nashua",
            "slug": "dm-nashua",
            "url": "https://demo.netbox.dev/api/dcim/sites/7/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/19/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "AP7901",
            "id": 8,
            "manufacturer": {
              "description": "",
              "display": "APC",
              "id": 11,
              "name": "APC",
              "slug": "apc",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/11/"
            },
            "model": "AP7901",
            "slug": "ap7901",
            "url": "https://demo.netbox.dev/api/dcim/device-types/8/"
          },
          "display": "dmi01-pittsfield-pdu01",
          "display_url": "https://demo.netbox.dev/dcim/devices/39/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 39,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2020-12-30T19:02:56.460000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-pittsfield-pdu01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 1.0,
          "power_outlet_count": 8,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 7,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/7/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "PDU",
            "id": 5,
            "name": "PDU",
            "slug": "pdu",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/5/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Pittsfield",
            "id": 8,
            "name": "DM-Pittsfield",
            "slug": "dm-pittsfield",
            "url": "https://demo.netbox.dev/api/dcim/sites/8/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/39/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {
            "syslog-servers": [
              "192.168.1.100"
            ]
          },
          "config_template": null,
          "console_port_count": 2,
          "console_server_port_count": 0,
          "created": "2020-12-20T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "ISR 1111-8P",
            "id": 6,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "ISR 1111-8P",
            "slug": "isr1111",
            "url": "https://demo.netbox.dev/api/dcim/device-types/6/"
          },
          "display": "dmi01-pittsfield-rtr01",
          "display_url": "https://demo.netbox.dev/dcim/devices/7/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 7,
          "interface_count": 14,
          "inventory_item_count": 0,
          "last_updated": "2020-12-20T02:55:17.095000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-pittsfield-rtr01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Cisco IOS",
            "id": 1,
            "name": "Cisco IOS",
            "slug": "cisco-ios",
            "url": "https://demo.netbox.dev/api/dcim/platforms/1/",
            "virtualmachine_count": 0
          },
          "position": 4.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 7,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/7/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Router",
            "id": 1,
            "name": "Router",
            "slug": "router",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/1/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Pittsfield",
            "id": 8,
            "name": "DM-Pittsfield",
            "slug": "dm-pittsfield",
            "url": "https://demo.netbox.dev/api/dcim/sites/8/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/7/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 16,
            "display": "C9200-48P",
            "id": 7,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "C9200-48P",
            "slug": "c9200-48p",
            "url": "https://demo.netbox.dev/api/dcim/device-types/7/"
          },
          "display": "dmi01-pittsfield-sw01",
          "display_url": "https://demo.netbox.dev/dcim/devices/20/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 20,
          "interface_count": 52,
          "inventory_item_count": 0,
          "last_updated": "2020-12-22T02:11:12.204000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-pittsfield-sw01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 10.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 7,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/7/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Access Switch",
            "id": 4,
            "name": "Access Switch",
            "slug": "access-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/4/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Pittsfield",
            "id": 8,
            "name": "DM-Pittsfield",
            "slug": "dm-pittsfield",
            "url": "https://demo.netbox.dev/api/dcim/sites/8/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/20/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "AP7901",
            "id": 8,
            "manufacturer": {
              "description": "",
              "display": "APC",
              "id": 11,
              "name": "APC",
              "slug": "apc",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/11/"
            },
            "model": "AP7901",
            "slug": "ap7901",
            "url": "https://demo.netbox.dev/api/dcim/device-types/8/"
          },
          "display": "dmi01-rochester-pdu01",
          "display_url": "https://demo.netbox.dev/dcim/devices/40/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 40,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2020-12-30T19:02:56.562000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-rochester-pdu01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 1.0,
          "power_outlet_count": 8,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 8,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/8/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "PDU",
            "id": 5,
            "name": "PDU",
            "slug": "pdu",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/5/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Rochester",
            "id": 9,
            "name": "DM-Rochester",
            "slug": "dm-rochester",
            "url": "https://demo.netbox.dev/api/dcim/sites/9/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/40/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {
            "syslog-servers": [
              "192.168.1.100"
            ]
          },
          "config_template": null,
          "console_port_count": 2,
          "console_server_port_count": 0,
          "created": "2020-12-20T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "ISR 1111-8P",
            "id": 6,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "ISR 1111-8P",
            "slug": "isr1111",
            "url": "https://demo.netbox.dev/api/dcim/device-types/6/"
          },
          "display": "dmi01-rochester-rtr01",
          "display_url": "https://demo.netbox.dev/dcim/devices/8/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 8,
          "interface_count": 14,
          "inventory_item_count": 0,
          "last_updated": "2020-12-20T02:55:35.846000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-rochester-rtr01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Cisco IOS",
            "id": 1,
            "name": "Cisco IOS",
            "slug": "cisco-ios",
            "url": "https://demo.netbox.dev/api/dcim/platforms/1/",
            "virtualmachine_count": 0
          },
          "position": 4.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 8,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/8/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Router",
            "id": 1,
            "name": "Router",
            "slug": "router",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/1/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Rochester",
            "id": 9,
            "name": "DM-Rochester",
            "slug": "dm-rochester",
            "url": "https://demo.netbox.dev/api/dcim/sites/9/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/8/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 16,
            "display": "C9200-48P",
            "id": 7,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "C9200-48P",
            "slug": "c9200-48p",
            "url": "https://demo.netbox.dev/api/dcim/device-types/7/"
          },
          "display": "dmi01-rochster-sw01",
          "display_url": "https://demo.netbox.dev/dcim/devices/21/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 21,
          "interface_count": 52,
          "inventory_item_count": 0,
          "last_updated": "2020-12-22T02:11:12.287000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-rochster-sw01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 10.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 8,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/8/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Access Switch",
            "id": 4,
            "name": "Access Switch",
            "slug": "access-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/4/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Rochester",
            "id": 9,
            "name": "DM-Rochester",
            "slug": "dm-rochester",
            "url": "https://demo.netbox.dev/api/dcim/sites/9/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/21/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "AP7901",
            "id": 8,
            "manufacturer": {
              "description": "",
              "display": "APC",
              "id": 11,
              "name": "APC",
              "slug": "apc",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/11/"
            },
            "model": "AP7901",
            "slug": "ap7901",
            "url": "https://demo.netbox.dev/api/dcim/device-types/8/"
          },
          "display": "dmi01-scranton-pdu01",
          "display_url": "https://demo.netbox.dev/dcim/devices/41/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 41,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2020-12-30T19:02:56.664000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-scranton-pdu01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 1.0,
          "power_outlet_count": 8,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 9,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/9/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "PDU",
            "id": 5,
            "name": "PDU",
            "slug": "pdu",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/5/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Scranton",
            "id": 10,
            "name": "DM-Scranton",
            "slug": "dm-scranton",
            "url": "https://demo.netbox.dev/api/dcim/sites/10/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/41/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {
            "syslog-servers": [
              "192.168.1.100"
            ]
          },
          "config_template": null,
          "console_port_count": 2,
          "console_server_port_count": 0,
          "created": "2020-12-20T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "ISR 1111-8P",
            "id": 6,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "ISR 1111-8P",
            "slug": "isr1111",
            "url": "https://demo.netbox.dev/api/dcim/device-types/6/"
          },
          "display": "dmi01-scranton-rtr01",
          "display_url": "https://demo.netbox.dev/dcim/devices/9/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 9,
          "interface_count": 14,
          "inventory_item_count": 0,
          "last_updated": "2020-12-20T02:55:49.316000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-scranton-rtr01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Cisco IOS",
            "id": 1,
            "name": "Cisco IOS",
            "slug": "cisco-ios",
            "url": "https://demo.netbox.dev/api/dcim/platforms/1/",
            "virtualmachine_count": 0
          },
          "position": 4.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 9,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/9/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Router",
            "id": 1,
            "name": "Router",
            "slug": "router",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/1/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Scranton",
            "id": 10,
            "name": "DM-Scranton",
            "slug": "dm-scranton",
            "url": "https://demo.netbox.dev/api/dcim/sites/10/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/9/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 16,
            "display": "C9200-48P",
            "id": 7,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "C9200-48P",
            "slug": "c9200-48p",
            "url": "https://demo.netbox.dev/api/dcim/device-types/7/"
          },
          "display": "dmi01-scranton-sw01",
          "display_url": "https://demo.netbox.dev/dcim/devices/22/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 22,
          "interface_count": 52,
          "inventory_item_count": 0,
          "last_updated": "2020-12-22T02:11:12.370000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-scranton-sw01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 10.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 9,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/9/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Access Switch",
            "id": 4,
            "name": "Access Switch",
            "slug": "access-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/4/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Scranton",
            "id": 10,
            "name": "DM-Scranton",
            "slug": "dm-scranton",
            "url": "https://demo.netbox.dev/api/dcim/sites/10/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/22/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "AP7901",
            "id": 8,
            "manufacturer": {
              "description": "",
              "display": "APC",
              "id": 11,
              "name": "APC",
              "slug": "apc",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/11/"
            },
            "model": "AP7901",
            "slug": "ap7901",
            "url": "https://demo.netbox.dev/api/dcim/device-types/8/"
          },
          "display": "dmi01-stamford-pdu01",
          "display_url": "https://demo.netbox.dev/dcim/devices/42/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 42,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2020-12-30T19:02:56.767000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-stamford-pdu01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 1.0,
          "power_outlet_count": 8,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 10,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/10/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "PDU",
            "id": 5,
            "name": "PDU",
            "slug": "pdu",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/5/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Stamford",
            "id": 11,
            "name": "DM-Stamford",
            "slug": "dm-stamford",
            "url": "https://demo.netbox.dev/api/dcim/sites/11/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/42/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {
            "syslog-servers": [
              "192.168.1.100"
            ]
          },
          "config_template": null,
          "console_port_count": 2,
          "console_server_port_count": 0,
          "created": "2020-12-20T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "ISR 1111-8P",
            "id": 6,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "ISR 1111-8P",
            "slug": "isr1111",
            "url": "https://demo.netbox.dev/api/dcim/device-types/6/"
          },
          "display": "dmi01-stamford-rtr01",
          "display_url": "https://demo.netbox.dev/dcim/devices/10/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 10,
          "interface_count": 14,
          "inventory_item_count": 0,
          "last_updated": "2020-12-20T02:56:06.592000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-stamford-rtr01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Cisco IOS",
            "id": 1,
            "name": "Cisco IOS",
            "slug": "cisco-ios",
            "url": "https://demo.netbox.dev/api/dcim/platforms/1/",
            "virtualmachine_count": 0
          },
          "position": 4.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 10,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/10/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Router",
            "id": 1,
            "name": "Router",
            "slug": "router",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/1/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Stamford",
            "id": 11,
            "name": "DM-Stamford",
            "slug": "dm-stamford",
            "url": "https://demo.netbox.dev/api/dcim/sites/11/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/10/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 16,
            "display": "C9200-48P",
            "id": 7,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "C9200-48P",
            "slug": "c9200-48p",
            "url": "https://demo.netbox.dev/api/dcim/device-types/7/"
          },
          "display": "dmi01-stamford-sw01",
          "display_url": "https://demo.netbox.dev/dcim/devices/23/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 23,
          "interface_count": 52,
          "inventory_item_count": 0,
          "last_updated": "2020-12-22T02:11:12.454000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-stamford-sw01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 10.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 10,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/10/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Access Switch",
            "id": 4,
            "name": "Access Switch",
            "slug": "access-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/4/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Stamford",
            "id": 11,
            "name": "DM-Stamford",
            "slug": "dm-stamford",
            "url": "https://demo.netbox.dev/api/dcim/sites/11/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/23/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "AP7901",
            "id": 8,
            "manufacturer": {
              "description": "",
              "display": "APC",
              "id": 11,
              "name": "APC",
              "slug": "apc",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/11/"
            },
            "model": "AP7901",
            "slug": "ap7901",
            "url": "https://demo.netbox.dev/api/dcim/device-types/8/"
          },
          "display": "dmi01-syracuse-pdu01",
          "display_url": "https://demo.netbox.dev/dcim/devices/43/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 43,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2020-12-30T19:02:56.870000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-syracuse-pdu01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 1.0,
          "power_outlet_count": 8,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 11,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/11/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "PDU",
            "id": 5,
            "name": "PDU",
            "slug": "pdu",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/5/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Syracuse",
            "id": 12,
            "name": "DM-Syracuse",
            "slug": "dm-syracuse",
            "url": "https://demo.netbox.dev/api/dcim/sites/12/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/43/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {
            "syslog-servers": [
              "192.168.1.100"
            ]
          },
          "config_template": null,
          "console_port_count": 2,
          "console_server_port_count": 0,
          "created": "2020-12-20T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "ISR 1111-8P",
            "id": 6,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "ISR 1111-8P",
            "slug": "isr1111",
            "url": "https://demo.netbox.dev/api/dcim/device-types/6/"
          },
          "display": "dmi01-syracuse-rtr01",
          "display_url": "https://demo.netbox.dev/dcim/devices/11/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 11,
          "interface_count": 14,
          "inventory_item_count": 0,
          "last_updated": "2020-12-20T02:56:24.173000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-syracuse-rtr01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Cisco IOS",
            "id": 1,
            "name": "Cisco IOS",
            "slug": "cisco-ios",
            "url": "https://demo.netbox.dev/api/dcim/platforms/1/",
            "virtualmachine_count": 0
          },
          "position": 4.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 11,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/11/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Router",
            "id": 1,
            "name": "Router",
            "slug": "router",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/1/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Syracuse",
            "id": 12,
            "name": "DM-Syracuse",
            "slug": "dm-syracuse",
            "url": "https://demo.netbox.dev/api/dcim/sites/12/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/11/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 16,
            "display": "C9200-48P",
            "id": 7,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "C9200-48P",
            "slug": "c9200-48p",
            "url": "https://demo.netbox.dev/api/dcim/device-types/7/"
          },
          "display": "dmi01-syracuse-sw01",
          "display_url": "https://demo.netbox.dev/dcim/devices/24/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 24,
          "interface_count": 52,
          "inventory_item_count": 0,
          "last_updated": "2020-12-22T02:11:12.540000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-syracuse-sw01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 10.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 11,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/11/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Access Switch",
            "id": 4,
            "name": "Access Switch",
            "slug": "access-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/4/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Syracuse",
            "id": 12,
            "name": "DM-Syracuse",
            "slug": "dm-syracuse",
            "url": "https://demo.netbox.dev/api/dcim/sites/12/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/24/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "AP7901",
            "id": 8,
            "manufacturer": {
              "description": "",
              "display": "APC",
              "id": 11,
              "name": "APC",
              "slug": "apc",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/11/"
            },
            "model": "AP7901",
            "slug": "ap7901",
            "url": "https://demo.netbox.dev/api/dcim/device-types/8/"
          },
          "display": "dmi01-utica-pdu01",
          "display_url": "https://demo.netbox.dev/dcim/devices/44/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 44,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2020-12-30T19:02:56.973000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-utica-pdu01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 1.0,
          "power_outlet_count": 8,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 12,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/12/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "PDU",
            "id": 5,
            "name": "PDU",
            "slug": "pdu",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/5/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Utica",
            "id": 13,
            "name": "DM-Utica",
            "slug": "dm-utica",
            "url": "https://demo.netbox.dev/api/dcim/sites/13/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/44/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {
            "syslog-servers": [
              "192.168.1.100"
            ]
          },
          "config_template": null,
          "console_port_count": 2,
          "console_server_port_count": 0,
          "created": "2020-12-20T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "ISR 1111-8P",
            "id": 6,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "ISR 1111-8P",
            "slug": "isr1111",
            "url": "https://demo.netbox.dev/api/dcim/device-types/6/"
          },
          "display": "dmi01-utica-rtr01",
          "display_url": "https://demo.netbox.dev/dcim/devices/12/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 12,
          "interface_count": 14,
          "inventory_item_count": 0,
          "last_updated": "2020-12-20T02:56:38.212000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-utica-rtr01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Cisco IOS",
            "id": 1,
            "name": "Cisco IOS",
            "slug": "cisco-ios",
            "url": "https://demo.netbox.dev/api/dcim/platforms/1/",
            "virtualmachine_count": 0
          },
          "position": 4.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 12,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/12/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Router",
            "id": 1,
            "name": "Router",
            "slug": "router",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/1/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Utica",
            "id": 13,
            "name": "DM-Utica",
            "slug": "dm-utica",
            "url": "https://demo.netbox.dev/api/dcim/sites/13/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/12/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 16,
            "display": "C9200-48P",
            "id": 7,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "C9200-48P",
            "slug": "c9200-48p",
            "url": "https://demo.netbox.dev/api/dcim/device-types/7/"
          },
          "display": "dmi01-utica-sw01",
          "display_url": "https://demo.netbox.dev/dcim/devices/25/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 25,
          "interface_count": 52,
          "inventory_item_count": 0,
          "last_updated": "2020-12-22T02:11:12.622000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-utica-sw01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 10.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 12,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/12/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Access Switch",
            "id": 4,
            "name": "Access Switch",
            "slug": "access-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/4/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Utica",
            "id": 13,
            "name": "DM-Utica",
            "slug": "dm-utica",
            "url": "https://demo.netbox.dev/api/dcim/sites/13/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/25/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "AP7901",
            "id": 8,
            "manufacturer": {
              "description": "",
              "display": "APC",
              "id": 11,
              "name": "APC",
              "slug": "apc",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/11/"
            },
            "model": "AP7901",
            "slug": "ap7901",
            "url": "https://demo.netbox.dev/api/dcim/device-types/8/"
          },
          "display": "dmi01-yonkers-pdu01",
          "display_url": "https://demo.netbox.dev/dcim/devices/45/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 45,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2020-12-30T19:02:57.075000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-yonkers-pdu01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 1.0,
          "power_outlet_count": 8,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 13,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/13/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "PDU",
            "id": 5,
            "name": "PDU",
            "slug": "pdu",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/5/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Yonkers",
            "id": 14,
            "name": "DM-Yonkers",
            "slug": "dm-yonkers",
            "url": "https://demo.netbox.dev/api/dcim/sites/14/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/45/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {
            "syslog-servers": [
              "192.168.1.100"
            ]
          },
          "config_template": null,
          "console_port_count": 2,
          "console_server_port_count": 0,
          "created": "2020-12-20T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 13,
            "display": "ISR 1111-8P",
            "id": 6,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "ISR 1111-8P",
            "slug": "isr1111",
            "url": "https://demo.netbox.dev/api/dcim/device-types/6/"
          },
          "display": "dmi01-yonkers-rtr01",
          "display_url": "https://demo.netbox.dev/dcim/devices/13/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 13,
          "interface_count": 14,
          "inventory_item_count": 0,
          "last_updated": "2020-12-20T02:56:52.908000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-yonkers-rtr01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Cisco IOS",
            "id": 1,
            "name": "Cisco IOS",
            "slug": "cisco-ios",
            "url": "https://demo.netbox.dev/api/dcim/platforms/1/",
            "virtualmachine_count": 0
          },
          "position": 4.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 13,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/13/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Router",
            "id": 1,
            "name": "Router",
            "slug": "router",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/1/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Yonkers",
            "id": 14,
            "name": "DM-Yonkers",
            "slug": "dm-yonkers",
            "url": "https://demo.netbox.dev/api/dcim/sites/14/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/13/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2020-12-22T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 16,
            "display": "C9200-48P",
            "id": 7,
            "manufacturer": {
              "description": "",
              "display": "Cisco",
              "id": 3,
              "name": "Cisco",
              "slug": "cisco",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/3/"
            },
            "model": "C9200-48P",
            "slug": "c9200-48p",
            "url": "https://demo.netbox.dev/api/dcim/device-types/7/"
          },
          "display": "dmi01-yonkers-sw01",
          "display_url": "https://demo.netbox.dev/dcim/devices/26/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 26,
          "interface_count": 52,
          "inventory_item_count": 0,
          "last_updated": "2020-12-22T02:11:12.705000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "dmi01-yonkers-sw01",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 10.0,
          "power_outlet_count": 0,
          "power_port_count": 1,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Comms closet",
            "id": 13,
            "name": "Comms closet",
            "url": "https://demo.netbox.dev/api/dcim/racks/13/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Access Switch",
            "id": 4,
            "name": "Access Switch",
            "slug": "access-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/4/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "DM-Yonkers",
            "id": 14,
            "name": "DM-Yonkers",
            "slug": "dm-yonkers",
            "url": "https://demo.netbox.dev/api/dcim/sites/14/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/26/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 2,
          "console_server_port_count": 0,
          "created": "2021-04-02T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 2,
            "display": "EX9214",
            "id": 3,
            "manufacturer": {
              "description": "",
              "display": "Juniper",
              "id": 7,
              "name": "Juniper",
              "slug": "juniper",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/7/"
            },
            "model": "EX9214",
            "slug": "ex9214",
            "url": "https://demo.netbox.dev/api/dcim/device-types/3/"
          },
          "display": "ncsu-coreswitch1",
          "display_url": "https://demo.netbox.dev/dcim/devices/96/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 96,
          "interface_count": 64,
          "inventory_item_count": 0,
          "last_updated": "2021-04-02T17:31:41.398000Z",
          "latitude": null,
          "local_context_data": null,
          "location": {
            "_depth": 0,
            "description": "",
            "display": "Row 1",
            "id": 1,
            "name": "Row 1",
            "rack_count": 0,
            "slug": "row-1",
            "url": "https://demo.netbox.dev/api/dcim/locations/1/"
          },
          "longitude": null,
          "module_bay_count": 14,
          "name": "ncsu-coreswitch1",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 6.0,
          "power_outlet_count": 0,
          "power_port_count": 4,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "R103",
            "id": 16,
            "name": "R103",
            "url": "https://demo.netbox.dev/api/dcim/racks/16/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Core Switch",
            "id": 2,
            "name": "Core Switch",
            "slug": "core-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/2/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "Main Distribution Frame",
            "display": "MDF",
            "id": 21,
            "name": "MDF",
            "slug": "ncsu-065",
            "url": "https://demo.netbox.dev/api/dcim/sites/21/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "NC State University",
            "id": 13,
            "name": "NC State University",
            "slug": "nc-state",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/13/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/96/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 2,
          "console_server_port_count": 0,
          "created": "2021-04-02T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 2,
            "display": "EX9214",
            "id": 3,
            "manufacturer": {
              "description": "",
              "display": "Juniper",
              "id": 7,
              "name": "Juniper",
              "slug": "juniper",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/7/"
            },
            "model": "EX9214",
            "slug": "ex9214",
            "url": "https://demo.netbox.dev/api/dcim/device-types/3/"
          },
          "display": "ncsu-coreswitch2",
          "display_url": "https://demo.netbox.dev/dcim/devices/97/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 97,
          "interface_count": 64,
          "inventory_item_count": 0,
          "last_updated": "2021-04-02T17:31:56.519000Z",
          "latitude": null,
          "local_context_data": null,
          "location": {
            "_depth": 0,
            "description": "",
            "display": "Row 1",
            "id": 1,
            "name": "Row 1",
            "rack_count": 0,
            "slug": "row-1",
            "url": "https://demo.netbox.dev/api/dcim/locations/1/"
          },
          "longitude": null,
          "module_bay_count": 14,
          "name": "ncsu-coreswitch2",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 6.0,
          "power_outlet_count": 0,
          "power_port_count": 4,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "R104",
            "id": 17,
            "name": "R104",
            "url": "https://demo.netbox.dev/api/dcim/racks/17/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Core Switch",
            "id": 2,
            "name": "Core Switch",
            "slug": "core-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/2/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "Main Distribution Frame",
            "display": "MDF",
            "id": 21,
            "name": "MDF",
            "slug": "ncsu-065",
            "url": "https://demo.netbox.dev/api/dcim/sites/21/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "NC State University",
            "id": 13,
            "name": "NC State University",
            "slug": "nc-state",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/13/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/97/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 1,
          "console_server_port_count": 0,
          "created": "2021-04-02T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 3,
            "display": "QFX5110-48S-4C",
            "id": 12,
            "manufacturer": {
              "description": "",
              "display": "Juniper",
              "id": 7,
              "name": "Juniper",
              "slug": "juniper",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/7/"
            },
            "model": "QFX5110-48S-4C",
            "slug": "qfx5110-48s-4c",
            "url": "https://demo.netbox.dev/api/dcim/device-types/12/"
          },
          "display": "ncsu117-distswitch1",
          "display_url": "https://demo.netbox.dev/dcim/devices/94/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 94,
          "interface_count": 53,
          "inventory_item_count": 0,
          "last_updated": "2021-04-02T17:29:22.719000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "ncsu117-distswitch1",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 36.0,
          "power_outlet_count": 0,
          "power_port_count": 2,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "IDF117",
            "id": 40,
            "name": "IDF117",
            "url": "https://demo.netbox.dev/api/dcim/racks/40/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Distribution Switch",
            "id": 3,
            "name": "Distribution Switch",
            "slug": "distribution-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/3/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "D. S. Weaver Labs",
            "id": 22,
            "name": "D. S. Weaver Labs",
            "slug": "ncsu-117",
            "url": "https://demo.netbox.dev/api/dcim/sites/22/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "NC State University",
            "id": 13,
            "name": "NC State University",
            "slug": "nc-state",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/13/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/94/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 1,
          "console_server_port_count": 0,
          "created": "2021-04-02T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 3,
            "display": "QFX5110-48S-4C",
            "id": 12,
            "manufacturer": {
              "description": "",
              "display": "Juniper",
              "id": 7,
              "name": "Juniper",
              "slug": "juniper",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/7/"
            },
            "model": "QFX5110-48S-4C",
            "slug": "qfx5110-48s-4c",
            "url": "https://demo.netbox.dev/api/dcim/device-types/12/"
          },
          "display": "ncsu118-distswitch1",
          "display_url": "https://demo.netbox.dev/dcim/devices/95/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 95,
          "interface_count": 53,
          "inventory_item_count": 0,
          "last_updated": "2021-04-02T17:29:56.066000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "ncsu118-distswitch1",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 36.0,
          "power_outlet_count": 0,
          "power_port_count": 2,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "IDF118",
            "id": 38,
            "name": "IDF118",
            "url": "https://demo.netbox.dev/api/dcim/racks/38/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Distribution Switch",
            "id": 3,
            "name": "Distribution Switch",
            "slug": "distribution-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/3/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "Grinnells Lab",
            "id": 23,
            "name": "Grinnells Lab",
            "slug": "ncsu-118",
            "url": "https://demo.netbox.dev/api/dcim/sites/23/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "NC State University",
            "id": 13,
            "name": "NC State University",
            "slug": "nc-state",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/13/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/95/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 1,
          "console_server_port_count": 0,
          "created": "2021-04-02T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 3,
            "display": "QFX5110-48S-4C",
            "id": 12,
            "manufacturer": {
              "description": "",
              "display": "Juniper",
              "id": 7,
              "name": "Juniper",
              "slug": "juniper",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/7/"
            },
            "model": "QFX5110-48S-4C",
            "slug": "qfx5110-48s-4c",
            "url": "https://demo.netbox.dev/api/dcim/device-types/12/"
          },
          "display": "ncsu128-distswitch1",
          "display_url": "https://demo.netbox.dev/dcim/devices/93/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 0,
          "id": 93,
          "interface_count": 53,
          "inventory_item_count": 0,
          "last_updated": "2021-04-02T17:28:42.498000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "ncsu128-distswitch1",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 32.0,
          "power_outlet_count": 0,
          "power_port_count": 2,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "IDF128",
            "id": 39,
            "name": "IDF128",
            "url": "https://demo.netbox.dev/api/dcim/racks/39/"
          },
          "rear_port_count": 0,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Distribution Switch",
            "id": 3,
            "name": "Distribution Switch",
            "slug": "distribution-switch",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/3/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "Butler Communications",
            "id": 24,
            "name": "Butler Communications",
            "slug": "ncsu-128",
            "url": "https://demo.netbox.dev/api/dcim/sites/24/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "NC State University",
            "id": 13,
            "name": "NC State University",
            "slug": "nc-state",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/13/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/93/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": {
            "label": "Rear to side",
            "value": "rear-to-side"
          },
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2026-03-23T15:19:02.851159Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": "lk",
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 7,
            "display": "48-Pair Fiber Panel",
            "id": 11,
            "manufacturer": {
              "description": "",
              "display": "Generic",
              "id": 13,
              "name": "Generic",
              "slug": "generic",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/13/"
            },
            "model": "48-Pair Fiber Panel",
            "slug": "48-pair-fiber-panel",
            "url": "https://demo.netbox.dev/api/dcim/device-types/11/"
          },
          "display": "Patch Panel 1",
          "display_url": "https://demo.netbox.dev/dcim/devices/113/",
          "face": null,
          "front_port_count": 48,
          "id": 113,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2026-03-23T15:19:02.851175Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "Patch Panel 1",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": null,
          "power_outlet_count": 0,
          "power_port_count": 0,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": null,
          "rear_port_count": 1,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Patch Panel",
            "id": 6,
            "name": "Patch Panel",
            "slug": "patch-panel",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/6/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "Butler Communications",
            "id": 24,
            "name": "Butler Communications",
            "slug": "ncsu-128",
            "url": "https://demo.netbox.dev/api/dcim/sites/24/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": null,
          "url": "https://demo.netbox.dev/api/dcim/devices/113/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2021-04-02T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 7,
            "display": "48-Pair Fiber Panel",
            "id": 11,
            "manufacturer": {
              "description": "",
              "display": "Generic",
              "id": 13,
              "name": "Generic",
              "slug": "generic",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/13/"
            },
            "model": "48-Pair Fiber Panel",
            "slug": "48-pair-fiber-panel",
            "url": "https://demo.netbox.dev/api/dcim/device-types/11/"
          },
          "display": "PP:B117",
          "display_url": "https://demo.netbox.dev/dcim/devices/88/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 48,
          "id": 88,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2021-04-02T17:17:28.425000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "PP:B117",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 37.0,
          "power_outlet_count": 0,
          "power_port_count": 0,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Plant 1",
            "id": 41,
            "name": "Plant 1",
            "url": "https://demo.netbox.dev/api/dcim/racks/41/"
          },
          "rear_port_count": 1,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Patch Panel",
            "id": 6,
            "name": "Patch Panel",
            "slug": "patch-panel",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/6/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "Main Distribution Frame",
            "display": "MDF",
            "id": 21,
            "name": "MDF",
            "slug": "ncsu-065",
            "url": "https://demo.netbox.dev/api/dcim/sites/21/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "NC State University",
            "id": 13,
            "name": "NC State University",
            "slug": "nc-state",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/13/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/88/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2021-04-02T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 7,
            "display": "48-Pair Fiber Panel",
            "id": 11,
            "manufacturer": {
              "description": "",
              "display": "Generic",
              "id": 13,
              "name": "Generic",
              "slug": "generic",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/13/"
            },
            "model": "48-Pair Fiber Panel",
            "slug": "48-pair-fiber-panel",
            "url": "https://demo.netbox.dev/api/dcim/device-types/11/"
          },
          "display": "PP:B118",
          "display_url": "https://demo.netbox.dev/dcim/devices/89/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 48,
          "id": 89,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2021-04-02T17:17:57.268000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "PP:B118",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 35.0,
          "power_outlet_count": 0,
          "power_port_count": 0,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Plant 1",
            "id": 41,
            "name": "Plant 1",
            "url": "https://demo.netbox.dev/api/dcim/racks/41/"
          },
          "rear_port_count": 1,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Patch Panel",
            "id": 6,
            "name": "Patch Panel",
            "slug": "patch-panel",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/6/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "Main Distribution Frame",
            "display": "MDF",
            "id": 21,
            "name": "MDF",
            "slug": "ncsu-065",
            "url": "https://demo.netbox.dev/api/dcim/sites/21/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "NC State University",
            "id": 13,
            "name": "NC State University",
            "slug": "nc-state",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/13/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/89/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2021-04-02T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 7,
            "display": "48-Pair Fiber Panel",
            "id": 11,
            "manufacturer": {
              "description": "",
              "display": "Generic",
              "id": 13,
              "name": "Generic",
              "slug": "generic",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/13/"
            },
            "model": "48-Pair Fiber Panel",
            "slug": "48-pair-fiber-panel",
            "url": "https://demo.netbox.dev/api/dcim/device-types/11/"
          },
          "display": "PP:B128",
          "display_url": "https://demo.netbox.dev/dcim/devices/87/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 48,
          "id": 87,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2021-04-02T17:16:58.069000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "PP:B128",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 39.0,
          "power_outlet_count": 0,
          "power_port_count": 0,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "Plant 1",
            "id": 41,
            "name": "Plant 1",
            "url": "https://demo.netbox.dev/api/dcim/racks/41/"
          },
          "rear_port_count": 1,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Patch Panel",
            "id": 6,
            "name": "Patch Panel",
            "slug": "patch-panel",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/6/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "Main Distribution Frame",
            "display": "MDF",
            "id": 21,
            "name": "MDF",
            "slug": "ncsu-065",
            "url": "https://demo.netbox.dev/api/dcim/sites/21/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "NC State University",
            "id": 13,
            "name": "NC State University",
            "slug": "nc-state",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/13/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/87/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2021-04-02T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 7,
            "display": "48-Pair Fiber Panel",
            "id": 11,
            "manufacturer": {
              "description": "",
              "display": "Generic",
              "id": 13,
              "name": "Generic",
              "slug": "generic",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/13/"
            },
            "model": "48-Pair Fiber Panel",
            "slug": "48-pair-fiber-panel",
            "url": "https://demo.netbox.dev/api/dcim/device-types/11/"
          },
          "display": "PP:MDF",
          "display_url": "https://demo.netbox.dev/dcim/devices/90/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 48,
          "id": 90,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2021-04-02T17:19:12.870000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "PP:MDF",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 39.0,
          "power_outlet_count": 0,
          "power_port_count": 0,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "IDF128",
            "id": 39,
            "name": "IDF128",
            "url": "https://demo.netbox.dev/api/dcim/racks/39/"
          },
          "rear_port_count": 1,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Patch Panel",
            "id": 6,
            "name": "Patch Panel",
            "slug": "patch-panel",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/6/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "Butler Communications",
            "id": 24,
            "name": "Butler Communications",
            "slug": "ncsu-128",
            "url": "https://demo.netbox.dev/api/dcim/sites/24/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "NC State University",
            "id": 13,
            "name": "NC State University",
            "slug": "nc-state",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/13/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/90/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        },
        {
          "airflow": null,
          "asset_tag": null,
          "cluster": null,
          "comments": "",
          "config_context": {},
          "config_template": null,
          "console_port_count": 0,
          "console_server_port_count": 0,
          "created": "2021-04-02T00:00:00Z",
          "custom_fields": {
            "Exposure": null,
            "Test2": null,
            "cpe": null,
            "environment": null
          },
          "description": "",
          "device_bay_count": 0,
          "device_type": {
            "description": "",
            "device_count": 7,
            "display": "48-Pair Fiber Panel",
            "id": 11,
            "manufacturer": {
              "description": "",
              "display": "Generic",
              "id": 13,
              "name": "Generic",
              "slug": "generic",
              "url": "https://demo.netbox.dev/api/dcim/manufacturers/13/"
            },
            "model": "48-Pair Fiber Panel",
            "slug": "48-pair-fiber-panel",
            "url": "https://demo.netbox.dev/api/dcim/device-types/11/"
          },
          "display": "PP:MDF",
          "display_url": "https://demo.netbox.dev/dcim/devices/91/",
          "face": {
            "label": "Front",
            "value": "front"
          },
          "front_port_count": 48,
          "id": 91,
          "interface_count": 0,
          "inventory_item_count": 0,
          "last_updated": "2021-04-02T17:19:41.498000Z",
          "latitude": null,
          "local_context_data": null,
          "location": null,
          "longitude": null,
          "module_bay_count": 0,
          "name": "PP:MDF",
          "oob_ip": null,
          "owner": null,
          "parent_device": null,
          "platform": null,
          "position": 39.0,
          "power_outlet_count": 0,
          "power_port_count": 0,
          "primary_ip": null,
          "primary_ip4": null,
          "primary_ip6": null,
          "rack": {
            "description": "",
            "display": "IDF117",
            "id": 40,
            "name": "IDF117",
            "url": "https://demo.netbox.dev/api/dcim/racks/40/"
          },
          "rear_port_count": 1,
          "role": {
            "_depth": 0,
            "description": "",
            "device_count": 0,
            "display": "Patch Panel",
            "id": 6,
            "name": "Patch Panel",
            "slug": "patch-panel",
            "url": "https://demo.netbox.dev/api/dcim/device-roles/6/",
            "virtualmachine_count": 0
          },
          "serial": "",
          "site": {
            "description": "",
            "display": "D. S. Weaver Labs",
            "id": 22,
            "name": "D. S. Weaver Labs",
            "slug": "ncsu-117",
            "url": "https://demo.netbox.dev/api/dcim/sites/22/"
          },
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "NC State University",
            "id": 13,
            "name": "NC State University",
            "slug": "nc-state",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/13/"
          },
          "url": "https://demo.netbox.dev/api/dcim/devices/91/",
          "vc_position": null,
          "vc_priority": null,
          "virtual_chassis": null
        }
      ]
    }
    ```

=== ":material-file-document-outline: YAML Output"

    ```yaml
    count: 79
    next: https://demo.netbox.dev/api/dcim/devices/?limit=50&offset=50
    previous: null
    results:
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: '3232'
        environment: null
      description: TEST
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: AP7901
        id: 8
        manufacturer:
          description: ''
          display: APC
          id: 11
          name: APC
          slug: apc
          url: https://demo.netbox.dev/api/dcim/manufacturers/11/
        model: AP7901
        slug: ap7901
        url: https://demo.netbox.dev/api/dcim/device-types/8/
      display: dmi01-akron-pdu01
      display_url: https://demo.netbox.dev/dcim/devices/27/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 27
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2026-03-23T10:39:34.986647Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-akron-pdu01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 1.0
      power_outlet_count: 8
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 1
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/1/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: PDU
        id: 5
        name: PDU
        slug: pdu
        url: https://demo.netbox.dev/api/dcim/device-roles/5/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Akron
        id: 2
        name: DM-Akron
        slug: dm-akron
        url: https://demo.netbox.dev/api/dcim/sites/2/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/27/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context:
        syslog-servers:
        - 192.168.1.200
      config_template: null
      console_port_count: 2
      console_server_port_count: 0
      created: '2020-12-20T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: ISR 1111-8P
        id: 6
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: ISR 1111-8P
        slug: isr1111
        url: https://demo.netbox.dev/api/dcim/device-types/6/
      display: dmi01-akron-rtr01
      display_url: https://demo.netbox.dev/dcim/devices/1/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 1
      interface_count: 14
      inventory_item_count: 0
      last_updated: '2020-12-20T02:51:03.257000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-akron-rtr01
      oob_ip: null
      owner: null
      parent_device: null
      platform:
        _depth: 0
        description: ''
        device_count: 0
        display: Cisco IOS
        id: 1
        name: Cisco IOS
        slug: cisco-ios
        url: https://demo.netbox.dev/api/dcim/platforms/1/
        virtualmachine_count: 0
      position: 4.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 1
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/1/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Router
        id: 1
        name: Router
        slug: router
        url: https://demo.netbox.dev/api/dcim/device-roles/1/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Akron
        id: 2
        name: DM-Akron
        slug: dm-akron
        url: https://demo.netbox.dev/api/dcim/sites/2/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/1/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 16
        display: C9200-48P
        id: 7
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: C9200-48P
        slug: c9200-48p
        url: https://demo.netbox.dev/api/dcim/device-types/7/
      display: dmi01-akron-sw01
      display_url: https://demo.netbox.dev/dcim/devices/14/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 14
      interface_count: 52
      inventory_item_count: 0
      last_updated: '2020-12-22T02:11:11.625000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-akron-sw01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 10.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 1
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/1/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Access Switch
        id: 4
        name: Access Switch
        slug: access-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/4/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Akron
        id: 2
        name: DM-Akron
        slug: dm-akron
        url: https://demo.netbox.dev/api/dcim/sites/2/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/14/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: AP7901
        id: 8
        manufacturer:
          description: ''
          display: APC
          id: 11
          name: APC
          slug: apc
          url: https://demo.netbox.dev/api/dcim/manufacturers/11/
        model: AP7901
        slug: ap7901
        url: https://demo.netbox.dev/api/dcim/device-types/8/
      display: dmi01-albany-pdu01
      display_url: https://demo.netbox.dev/dcim/devices/34/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 34
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2020-12-30T19:02:55.909000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-albany-pdu01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 1.0
      power_outlet_count: 8
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 2
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/2/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: PDU
        id: 5
        name: PDU
        slug: pdu
        url: https://demo.netbox.dev/api/dcim/device-roles/5/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Albany
        id: 3
        name: DM-Albany
        slug: dm-albany
        url: https://demo.netbox.dev/api/dcim/sites/3/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/34/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context:
        syslog-servers:
        - 192.168.1.100
      config_template: null
      console_port_count: 2
      console_server_port_count: 0
      created: '2020-12-20T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: ISR 1111-8P
        id: 6
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: ISR 1111-8P
        slug: isr1111
        url: https://demo.netbox.dev/api/dcim/device-types/6/
      display: dmi01-albany-rtr01
      display_url: https://demo.netbox.dev/dcim/devices/2/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 2
      interface_count: 14
      inventory_item_count: 0
      last_updated: '2020-12-20T02:51:32.863000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-albany-rtr01
      oob_ip: null
      owner: null
      parent_device: null
      platform:
        _depth: 0
        description: ''
        device_count: 0
        display: Cisco IOS
        id: 1
        name: Cisco IOS
        slug: cisco-ios
        url: https://demo.netbox.dev/api/dcim/platforms/1/
        virtualmachine_count: 0
      position: 4.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 2
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/2/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Router
        id: 1
        name: Router
        slug: router
        url: https://demo.netbox.dev/api/dcim/device-roles/1/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Albany
        id: 3
        name: DM-Albany
        slug: dm-albany
        url: https://demo.netbox.dev/api/dcim/sites/3/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/2/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 16
        display: C9200-48P
        id: 7
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: C9200-48P
        slug: c9200-48p
        url: https://demo.netbox.dev/api/dcim/device-types/7/
      display: dmi01-albany-sw01
      display_url: https://demo.netbox.dev/dcim/devices/15/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 15
      interface_count: 52
      inventory_item_count: 0
      last_updated: '2020-12-22T02:11:11.714000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-albany-sw01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 10.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 2
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/2/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Access Switch
        id: 4
        name: Access Switch
        slug: access-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/4/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Albany
        id: 3
        name: DM-Albany
        slug: dm-albany
        url: https://demo.netbox.dev/api/dcim/sites/3/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/15/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: AP7901
        id: 8
        manufacturer:
          description: ''
          display: APC
          id: 11
          name: APC
          slug: apc
          url: https://demo.netbox.dev/api/dcim/manufacturers/11/
        model: AP7901
        slug: ap7901
        url: https://demo.netbox.dev/api/dcim/device-types/8/
      display: dmi01-binghamton-pdu01
      display_url: https://demo.netbox.dev/dcim/devices/35/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 35
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2020-12-30T19:02:56.038000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-binghamton-pdu01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 1.0
      power_outlet_count: 8
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 3
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/3/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: PDU
        id: 5
        name: PDU
        slug: pdu
        url: https://demo.netbox.dev/api/dcim/device-roles/5/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Binghamton
        id: 4
        name: DM-Binghamton
        slug: dm-binghamton
        url: https://demo.netbox.dev/api/dcim/sites/4/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/35/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context:
        syslog-servers:
        - 192.168.1.100
      config_template: null
      console_port_count: 2
      console_server_port_count: 0
      created: '2020-12-20T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: ISR 1111-8P
        id: 6
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: ISR 1111-8P
        slug: isr1111
        url: https://demo.netbox.dev/api/dcim/device-types/6/
      display: dmi01-binghamton-rtr01
      display_url: https://demo.netbox.dev/dcim/devices/3/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 3
      interface_count: 14
      inventory_item_count: 0
      last_updated: '2020-12-20T02:52:02.614000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-binghamton-rtr01
      oob_ip: null
      owner: null
      parent_device: null
      platform:
        _depth: 0
        description: ''
        device_count: 0
        display: Cisco IOS
        id: 1
        name: Cisco IOS
        slug: cisco-ios
        url: https://demo.netbox.dev/api/dcim/platforms/1/
        virtualmachine_count: 0
      position: 4.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 3
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/3/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Router
        id: 1
        name: Router
        slug: router
        url: https://demo.netbox.dev/api/dcim/device-roles/1/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Binghamton
        id: 4
        name: DM-Binghamton
        slug: dm-binghamton
        url: https://demo.netbox.dev/api/dcim/sites/4/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/3/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 16
        display: C9200-48P
        id: 7
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: C9200-48P
        slug: c9200-48p
        url: https://demo.netbox.dev/api/dcim/device-types/7/
      display: dmi01-binghamton-sw01
      display_url: https://demo.netbox.dev/dcim/devices/16/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 16
      interface_count: 52
      inventory_item_count: 0
      last_updated: '2020-12-22T02:11:11.799000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-binghamton-sw01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 10.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 3
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/3/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Access Switch
        id: 4
        name: Access Switch
        slug: access-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/4/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Binghamton
        id: 4
        name: DM-Binghamton
        slug: dm-binghamton
        url: https://demo.netbox.dev/api/dcim/sites/4/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/16/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: AP7901
        id: 8
        manufacturer:
          description: ''
          display: APC
          id: 11
          name: APC
          slug: apc
          url: https://demo.netbox.dev/api/dcim/manufacturers/11/
        model: AP7901
        slug: ap7901
        url: https://demo.netbox.dev/api/dcim/device-types/8/
      display: dmi01-buffalo-pdu01
      display_url: https://demo.netbox.dev/dcim/devices/36/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 36
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2020-12-30T19:02:56.155000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-buffalo-pdu01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 1.0
      power_outlet_count: 8
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 4
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/4/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: PDU
        id: 5
        name: PDU
        slug: pdu
        url: https://demo.netbox.dev/api/dcim/device-roles/5/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Buffalo
        id: 5
        name: DM-Buffalo
        slug: dm-buffalo
        url: https://demo.netbox.dev/api/dcim/sites/5/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/36/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context:
        syslog-servers:
        - 192.168.1.100
      config_template: null
      console_port_count: 2
      console_server_port_count: 0
      created: '2020-12-20T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: ISR 1111-8P
        id: 6
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: ISR 1111-8P
        slug: isr1111
        url: https://demo.netbox.dev/api/dcim/device-types/6/
      display: dmi01-buffalo-rtr01
      display_url: https://demo.netbox.dev/dcim/devices/4/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 4
      interface_count: 14
      inventory_item_count: 0
      last_updated: '2020-12-20T02:52:26.146000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-buffalo-rtr01
      oob_ip: null
      owner: null
      parent_device: null
      platform:
        _depth: 0
        description: ''
        device_count: 0
        display: Cisco IOS
        id: 1
        name: Cisco IOS
        slug: cisco-ios
        url: https://demo.netbox.dev/api/dcim/platforms/1/
        virtualmachine_count: 0
      position: 4.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 4
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/4/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Router
        id: 1
        name: Router
        slug: router
        url: https://demo.netbox.dev/api/dcim/device-roles/1/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Buffalo
        id: 5
        name: DM-Buffalo
        slug: dm-buffalo
        url: https://demo.netbox.dev/api/dcim/sites/5/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/4/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 16
        display: C9200-48P
        id: 7
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: C9200-48P
        slug: c9200-48p
        url: https://demo.netbox.dev/api/dcim/device-types/7/
      display: dmi01-buffalo-sw01
      display_url: https://demo.netbox.dev/dcim/devices/17/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 17
      interface_count: 52
      inventory_item_count: 0
      last_updated: '2020-12-22T02:11:11.883000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-buffalo-sw01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 10.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 4
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/4/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Access Switch
        id: 4
        name: Access Switch
        slug: access-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/4/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Buffalo
        id: 5
        name: DM-Buffalo
        slug: dm-buffalo
        url: https://demo.netbox.dev/api/dcim/sites/5/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/17/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: AP7901
        id: 8
        manufacturer:
          description: ''
          display: APC
          id: 11
          name: APC
          slug: apc
          url: https://demo.netbox.dev/api/dcim/manufacturers/11/
        model: AP7901
        slug: ap7901
        url: https://demo.netbox.dev/api/dcim/device-types/8/
      display: dmi01-camden-pdu01
      display_url: https://demo.netbox.dev/dcim/devices/37/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 37
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2020-12-30T19:02:56.256000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-camden-pdu01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 1.0
      power_outlet_count: 8
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 5
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/5/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: PDU
        id: 5
        name: PDU
        slug: pdu
        url: https://demo.netbox.dev/api/dcim/device-roles/5/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Camden
        id: 6
        name: DM-Camden
        slug: dm-camden
        url: https://demo.netbox.dev/api/dcim/sites/6/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/37/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context:
        syslog-servers:
        - 192.168.1.100
      config_template: null
      console_port_count: 2
      console_server_port_count: 0
      created: '2020-12-20T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: ISR 1111-8P
        id: 6
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: ISR 1111-8P
        slug: isr1111
        url: https://demo.netbox.dev/api/dcim/device-types/6/
      display: dmi01-camden-rtr01
      display_url: https://demo.netbox.dev/dcim/devices/5/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 5
      interface_count: 14
      inventory_item_count: 0
      last_updated: '2020-12-20T02:53:47.838000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-camden-rtr01
      oob_ip: null
      owner: null
      parent_device: null
      platform:
        _depth: 0
        description: ''
        device_count: 0
        display: Cisco IOS
        id: 1
        name: Cisco IOS
        slug: cisco-ios
        url: https://demo.netbox.dev/api/dcim/platforms/1/
        virtualmachine_count: 0
      position: 4.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 5
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/5/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Router
        id: 1
        name: Router
        slug: router
        url: https://demo.netbox.dev/api/dcim/device-roles/1/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Camden
        id: 6
        name: DM-Camden
        slug: dm-camden
        url: https://demo.netbox.dev/api/dcim/sites/6/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/5/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 16
        display: C9200-48P
        id: 7
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: C9200-48P
        slug: c9200-48p
        url: https://demo.netbox.dev/api/dcim/device-types/7/
      display: dmi01-camden-sw01
      display_url: https://demo.netbox.dev/dcim/devices/18/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 18
      interface_count: 52
      inventory_item_count: 0
      last_updated: '2020-12-22T02:11:11.968000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-camden-sw01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 10.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 5
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/5/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Access Switch
        id: 4
        name: Access Switch
        slug: access-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/4/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Camden
        id: 6
        name: DM-Camden
        slug: dm-camden
        url: https://demo.netbox.dev/api/dcim/sites/6/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/18/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: AP7901
        id: 8
        manufacturer:
          description: ''
          display: APC
          id: 11
          name: APC
          slug: apc
          url: https://demo.netbox.dev/api/dcim/manufacturers/11/
        model: AP7901
        slug: ap7901
        url: https://demo.netbox.dev/api/dcim/device-types/8/
      display: dmi01-nashua-pdu01
      display_url: https://demo.netbox.dev/dcim/devices/38/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 38
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2020-12-30T19:02:56.357000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-nashua-pdu01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 1.0
      power_outlet_count: 8
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 6
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/6/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: PDU
        id: 5
        name: PDU
        slug: pdu
        url: https://demo.netbox.dev/api/dcim/device-roles/5/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Nashua
        id: 7
        name: DM-Nashua
        slug: dm-nashua
        url: https://demo.netbox.dev/api/dcim/sites/7/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/38/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context:
        syslog-servers:
        - 192.168.1.100
      config_template: null
      console_port_count: 2
      console_server_port_count: 0
      created: '2020-12-20T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: ISR 1111-8P
        id: 6
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: ISR 1111-8P
        slug: isr1111
        url: https://demo.netbox.dev/api/dcim/device-types/6/
      display: dmi01-nashua-rtr01
      display_url: https://demo.netbox.dev/dcim/devices/6/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 6
      interface_count: 14
      inventory_item_count: 0
      last_updated: '2020-12-20T02:54:08.200000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-nashua-rtr01
      oob_ip: null
      owner: null
      parent_device: null
      platform:
        _depth: 0
        description: ''
        device_count: 0
        display: Cisco IOS
        id: 1
        name: Cisco IOS
        slug: cisco-ios
        url: https://demo.netbox.dev/api/dcim/platforms/1/
        virtualmachine_count: 0
      position: 4.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 6
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/6/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Router
        id: 1
        name: Router
        slug: router
        url: https://demo.netbox.dev/api/dcim/device-roles/1/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Nashua
        id: 7
        name: DM-Nashua
        slug: dm-nashua
        url: https://demo.netbox.dev/api/dcim/sites/7/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/6/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 16
        display: C9200-48P
        id: 7
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: C9200-48P
        slug: c9200-48p
        url: https://demo.netbox.dev/api/dcim/device-types/7/
      display: dmi01-nashua-sw01
      display_url: https://demo.netbox.dev/dcim/devices/19/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 19
      interface_count: 52
      inventory_item_count: 0
      last_updated: '2020-12-22T02:11:12.071000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-nashua-sw01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 10.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 6
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/6/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Access Switch
        id: 4
        name: Access Switch
        slug: access-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/4/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Nashua
        id: 7
        name: DM-Nashua
        slug: dm-nashua
        url: https://demo.netbox.dev/api/dcim/sites/7/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/19/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: AP7901
        id: 8
        manufacturer:
          description: ''
          display: APC
          id: 11
          name: APC
          slug: apc
          url: https://demo.netbox.dev/api/dcim/manufacturers/11/
        model: AP7901
        slug: ap7901
        url: https://demo.netbox.dev/api/dcim/device-types/8/
      display: dmi01-pittsfield-pdu01
      display_url: https://demo.netbox.dev/dcim/devices/39/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 39
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2020-12-30T19:02:56.460000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-pittsfield-pdu01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 1.0
      power_outlet_count: 8
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 7
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/7/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: PDU
        id: 5
        name: PDU
        slug: pdu
        url: https://demo.netbox.dev/api/dcim/device-roles/5/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Pittsfield
        id: 8
        name: DM-Pittsfield
        slug: dm-pittsfield
        url: https://demo.netbox.dev/api/dcim/sites/8/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/39/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context:
        syslog-servers:
        - 192.168.1.100
      config_template: null
      console_port_count: 2
      console_server_port_count: 0
      created: '2020-12-20T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: ISR 1111-8P
        id: 6
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: ISR 1111-8P
        slug: isr1111
        url: https://demo.netbox.dev/api/dcim/device-types/6/
      display: dmi01-pittsfield-rtr01
      display_url: https://demo.netbox.dev/dcim/devices/7/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 7
      interface_count: 14
      inventory_item_count: 0
      last_updated: '2020-12-20T02:55:17.095000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-pittsfield-rtr01
      oob_ip: null
      owner: null
      parent_device: null
      platform:
        _depth: 0
        description: ''
        device_count: 0
        display: Cisco IOS
        id: 1
        name: Cisco IOS
        slug: cisco-ios
        url: https://demo.netbox.dev/api/dcim/platforms/1/
        virtualmachine_count: 0
      position: 4.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 7
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/7/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Router
        id: 1
        name: Router
        slug: router
        url: https://demo.netbox.dev/api/dcim/device-roles/1/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Pittsfield
        id: 8
        name: DM-Pittsfield
        slug: dm-pittsfield
        url: https://demo.netbox.dev/api/dcim/sites/8/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/7/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 16
        display: C9200-48P
        id: 7
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: C9200-48P
        slug: c9200-48p
        url: https://demo.netbox.dev/api/dcim/device-types/7/
      display: dmi01-pittsfield-sw01
      display_url: https://demo.netbox.dev/dcim/devices/20/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 20
      interface_count: 52
      inventory_item_count: 0
      last_updated: '2020-12-22T02:11:12.204000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-pittsfield-sw01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 10.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 7
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/7/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Access Switch
        id: 4
        name: Access Switch
        slug: access-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/4/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Pittsfield
        id: 8
        name: DM-Pittsfield
        slug: dm-pittsfield
        url: https://demo.netbox.dev/api/dcim/sites/8/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/20/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: AP7901
        id: 8
        manufacturer:
          description: ''
          display: APC
          id: 11
          name: APC
          slug: apc
          url: https://demo.netbox.dev/api/dcim/manufacturers/11/
        model: AP7901
        slug: ap7901
        url: https://demo.netbox.dev/api/dcim/device-types/8/
      display: dmi01-rochester-pdu01
      display_url: https://demo.netbox.dev/dcim/devices/40/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 40
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2020-12-30T19:02:56.562000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-rochester-pdu01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 1.0
      power_outlet_count: 8
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 8
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/8/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: PDU
        id: 5
        name: PDU
        slug: pdu
        url: https://demo.netbox.dev/api/dcim/device-roles/5/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Rochester
        id: 9
        name: DM-Rochester
        slug: dm-rochester
        url: https://demo.netbox.dev/api/dcim/sites/9/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/40/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context:
        syslog-servers:
        - 192.168.1.100
      config_template: null
      console_port_count: 2
      console_server_port_count: 0
      created: '2020-12-20T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: ISR 1111-8P
        id: 6
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: ISR 1111-8P
        slug: isr1111
        url: https://demo.netbox.dev/api/dcim/device-types/6/
      display: dmi01-rochester-rtr01
      display_url: https://demo.netbox.dev/dcim/devices/8/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 8
      interface_count: 14
      inventory_item_count: 0
      last_updated: '2020-12-20T02:55:35.846000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-rochester-rtr01
      oob_ip: null
      owner: null
      parent_device: null
      platform:
        _depth: 0
        description: ''
        device_count: 0
        display: Cisco IOS
        id: 1
        name: Cisco IOS
        slug: cisco-ios
        url: https://demo.netbox.dev/api/dcim/platforms/1/
        virtualmachine_count: 0
      position: 4.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 8
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/8/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Router
        id: 1
        name: Router
        slug: router
        url: https://demo.netbox.dev/api/dcim/device-roles/1/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Rochester
        id: 9
        name: DM-Rochester
        slug: dm-rochester
        url: https://demo.netbox.dev/api/dcim/sites/9/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/8/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 16
        display: C9200-48P
        id: 7
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: C9200-48P
        slug: c9200-48p
        url: https://demo.netbox.dev/api/dcim/device-types/7/
      display: dmi01-rochster-sw01
      display_url: https://demo.netbox.dev/dcim/devices/21/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 21
      interface_count: 52
      inventory_item_count: 0
      last_updated: '2020-12-22T02:11:12.287000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-rochster-sw01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 10.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 8
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/8/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Access Switch
        id: 4
        name: Access Switch
        slug: access-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/4/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Rochester
        id: 9
        name: DM-Rochester
        slug: dm-rochester
        url: https://demo.netbox.dev/api/dcim/sites/9/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/21/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: AP7901
        id: 8
        manufacturer:
          description: ''
          display: APC
          id: 11
          name: APC
          slug: apc
          url: https://demo.netbox.dev/api/dcim/manufacturers/11/
        model: AP7901
        slug: ap7901
        url: https://demo.netbox.dev/api/dcim/device-types/8/
      display: dmi01-scranton-pdu01
      display_url: https://demo.netbox.dev/dcim/devices/41/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 41
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2020-12-30T19:02:56.664000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-scranton-pdu01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 1.0
      power_outlet_count: 8
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 9
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/9/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: PDU
        id: 5
        name: PDU
        slug: pdu
        url: https://demo.netbox.dev/api/dcim/device-roles/5/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Scranton
        id: 10
        name: DM-Scranton
        slug: dm-scranton
        url: https://demo.netbox.dev/api/dcim/sites/10/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/41/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context:
        syslog-servers:
        - 192.168.1.100
      config_template: null
      console_port_count: 2
      console_server_port_count: 0
      created: '2020-12-20T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: ISR 1111-8P
        id: 6
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: ISR 1111-8P
        slug: isr1111
        url: https://demo.netbox.dev/api/dcim/device-types/6/
      display: dmi01-scranton-rtr01
      display_url: https://demo.netbox.dev/dcim/devices/9/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 9
      interface_count: 14
      inventory_item_count: 0
      last_updated: '2020-12-20T02:55:49.316000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-scranton-rtr01
      oob_ip: null
      owner: null
      parent_device: null
      platform:
        _depth: 0
        description: ''
        device_count: 0
        display: Cisco IOS
        id: 1
        name: Cisco IOS
        slug: cisco-ios
        url: https://demo.netbox.dev/api/dcim/platforms/1/
        virtualmachine_count: 0
      position: 4.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 9
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/9/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Router
        id: 1
        name: Router
        slug: router
        url: https://demo.netbox.dev/api/dcim/device-roles/1/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Scranton
        id: 10
        name: DM-Scranton
        slug: dm-scranton
        url: https://demo.netbox.dev/api/dcim/sites/10/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/9/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 16
        display: C9200-48P
        id: 7
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: C9200-48P
        slug: c9200-48p
        url: https://demo.netbox.dev/api/dcim/device-types/7/
      display: dmi01-scranton-sw01
      display_url: https://demo.netbox.dev/dcim/devices/22/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 22
      interface_count: 52
      inventory_item_count: 0
      last_updated: '2020-12-22T02:11:12.370000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-scranton-sw01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 10.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 9
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/9/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Access Switch
        id: 4
        name: Access Switch
        slug: access-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/4/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Scranton
        id: 10
        name: DM-Scranton
        slug: dm-scranton
        url: https://demo.netbox.dev/api/dcim/sites/10/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/22/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: AP7901
        id: 8
        manufacturer:
          description: ''
          display: APC
          id: 11
          name: APC
          slug: apc
          url: https://demo.netbox.dev/api/dcim/manufacturers/11/
        model: AP7901
        slug: ap7901
        url: https://demo.netbox.dev/api/dcim/device-types/8/
      display: dmi01-stamford-pdu01
      display_url: https://demo.netbox.dev/dcim/devices/42/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 42
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2020-12-30T19:02:56.767000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-stamford-pdu01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 1.0
      power_outlet_count: 8
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 10
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/10/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: PDU
        id: 5
        name: PDU
        slug: pdu
        url: https://demo.netbox.dev/api/dcim/device-roles/5/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Stamford
        id: 11
        name: DM-Stamford
        slug: dm-stamford
        url: https://demo.netbox.dev/api/dcim/sites/11/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/42/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context:
        syslog-servers:
        - 192.168.1.100
      config_template: null
      console_port_count: 2
      console_server_port_count: 0
      created: '2020-12-20T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: ISR 1111-8P
        id: 6
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: ISR 1111-8P
        slug: isr1111
        url: https://demo.netbox.dev/api/dcim/device-types/6/
      display: dmi01-stamford-rtr01
      display_url: https://demo.netbox.dev/dcim/devices/10/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 10
      interface_count: 14
      inventory_item_count: 0
      last_updated: '2020-12-20T02:56:06.592000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-stamford-rtr01
      oob_ip: null
      owner: null
      parent_device: null
      platform:
        _depth: 0
        description: ''
        device_count: 0
        display: Cisco IOS
        id: 1
        name: Cisco IOS
        slug: cisco-ios
        url: https://demo.netbox.dev/api/dcim/platforms/1/
        virtualmachine_count: 0
      position: 4.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 10
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/10/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Router
        id: 1
        name: Router
        slug: router
        url: https://demo.netbox.dev/api/dcim/device-roles/1/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Stamford
        id: 11
        name: DM-Stamford
        slug: dm-stamford
        url: https://demo.netbox.dev/api/dcim/sites/11/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/10/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 16
        display: C9200-48P
        id: 7
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: C9200-48P
        slug: c9200-48p
        url: https://demo.netbox.dev/api/dcim/device-types/7/
      display: dmi01-stamford-sw01
      display_url: https://demo.netbox.dev/dcim/devices/23/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 23
      interface_count: 52
      inventory_item_count: 0
      last_updated: '2020-12-22T02:11:12.454000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-stamford-sw01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 10.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 10
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/10/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Access Switch
        id: 4
        name: Access Switch
        slug: access-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/4/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Stamford
        id: 11
        name: DM-Stamford
        slug: dm-stamford
        url: https://demo.netbox.dev/api/dcim/sites/11/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/23/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: AP7901
        id: 8
        manufacturer:
          description: ''
          display: APC
          id: 11
          name: APC
          slug: apc
          url: https://demo.netbox.dev/api/dcim/manufacturers/11/
        model: AP7901
        slug: ap7901
        url: https://demo.netbox.dev/api/dcim/device-types/8/
      display: dmi01-syracuse-pdu01
      display_url: https://demo.netbox.dev/dcim/devices/43/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 43
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2020-12-30T19:02:56.870000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-syracuse-pdu01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 1.0
      power_outlet_count: 8
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 11
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/11/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: PDU
        id: 5
        name: PDU
        slug: pdu
        url: https://demo.netbox.dev/api/dcim/device-roles/5/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Syracuse
        id: 12
        name: DM-Syracuse
        slug: dm-syracuse
        url: https://demo.netbox.dev/api/dcim/sites/12/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/43/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context:
        syslog-servers:
        - 192.168.1.100
      config_template: null
      console_port_count: 2
      console_server_port_count: 0
      created: '2020-12-20T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: ISR 1111-8P
        id: 6
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: ISR 1111-8P
        slug: isr1111
        url: https://demo.netbox.dev/api/dcim/device-types/6/
      display: dmi01-syracuse-rtr01
      display_url: https://demo.netbox.dev/dcim/devices/11/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 11
      interface_count: 14
      inventory_item_count: 0
      last_updated: '2020-12-20T02:56:24.173000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-syracuse-rtr01
      oob_ip: null
      owner: null
      parent_device: null
      platform:
        _depth: 0
        description: ''
        device_count: 0
        display: Cisco IOS
        id: 1
        name: Cisco IOS
        slug: cisco-ios
        url: https://demo.netbox.dev/api/dcim/platforms/1/
        virtualmachine_count: 0
      position: 4.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 11
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/11/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Router
        id: 1
        name: Router
        slug: router
        url: https://demo.netbox.dev/api/dcim/device-roles/1/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Syracuse
        id: 12
        name: DM-Syracuse
        slug: dm-syracuse
        url: https://demo.netbox.dev/api/dcim/sites/12/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/11/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 16
        display: C9200-48P
        id: 7
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: C9200-48P
        slug: c9200-48p
        url: https://demo.netbox.dev/api/dcim/device-types/7/
      display: dmi01-syracuse-sw01
      display_url: https://demo.netbox.dev/dcim/devices/24/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 24
      interface_count: 52
      inventory_item_count: 0
      last_updated: '2020-12-22T02:11:12.540000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-syracuse-sw01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 10.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 11
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/11/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Access Switch
        id: 4
        name: Access Switch
        slug: access-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/4/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Syracuse
        id: 12
        name: DM-Syracuse
        slug: dm-syracuse
        url: https://demo.netbox.dev/api/dcim/sites/12/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/24/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: AP7901
        id: 8
        manufacturer:
          description: ''
          display: APC
          id: 11
          name: APC
          slug: apc
          url: https://demo.netbox.dev/api/dcim/manufacturers/11/
        model: AP7901
        slug: ap7901
        url: https://demo.netbox.dev/api/dcim/device-types/8/
      display: dmi01-utica-pdu01
      display_url: https://demo.netbox.dev/dcim/devices/44/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 44
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2020-12-30T19:02:56.973000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-utica-pdu01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 1.0
      power_outlet_count: 8
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 12
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/12/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: PDU
        id: 5
        name: PDU
        slug: pdu
        url: https://demo.netbox.dev/api/dcim/device-roles/5/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Utica
        id: 13
        name: DM-Utica
        slug: dm-utica
        url: https://demo.netbox.dev/api/dcim/sites/13/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/44/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context:
        syslog-servers:
        - 192.168.1.100
      config_template: null
      console_port_count: 2
      console_server_port_count: 0
      created: '2020-12-20T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: ISR 1111-8P
        id: 6
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: ISR 1111-8P
        slug: isr1111
        url: https://demo.netbox.dev/api/dcim/device-types/6/
      display: dmi01-utica-rtr01
      display_url: https://demo.netbox.dev/dcim/devices/12/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 12
      interface_count: 14
      inventory_item_count: 0
      last_updated: '2020-12-20T02:56:38.212000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-utica-rtr01
      oob_ip: null
      owner: null
      parent_device: null
      platform:
        _depth: 0
        description: ''
        device_count: 0
        display: Cisco IOS
        id: 1
        name: Cisco IOS
        slug: cisco-ios
        url: https://demo.netbox.dev/api/dcim/platforms/1/
        virtualmachine_count: 0
      position: 4.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 12
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/12/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Router
        id: 1
        name: Router
        slug: router
        url: https://demo.netbox.dev/api/dcim/device-roles/1/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Utica
        id: 13
        name: DM-Utica
        slug: dm-utica
        url: https://demo.netbox.dev/api/dcim/sites/13/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/12/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 16
        display: C9200-48P
        id: 7
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: C9200-48P
        slug: c9200-48p
        url: https://demo.netbox.dev/api/dcim/device-types/7/
      display: dmi01-utica-sw01
      display_url: https://demo.netbox.dev/dcim/devices/25/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 25
      interface_count: 52
      inventory_item_count: 0
      last_updated: '2020-12-22T02:11:12.622000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-utica-sw01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 10.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 12
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/12/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Access Switch
        id: 4
        name: Access Switch
        slug: access-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/4/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Utica
        id: 13
        name: DM-Utica
        slug: dm-utica
        url: https://demo.netbox.dev/api/dcim/sites/13/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/25/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: AP7901
        id: 8
        manufacturer:
          description: ''
          display: APC
          id: 11
          name: APC
          slug: apc
          url: https://demo.netbox.dev/api/dcim/manufacturers/11/
        model: AP7901
        slug: ap7901
        url: https://demo.netbox.dev/api/dcim/device-types/8/
      display: dmi01-yonkers-pdu01
      display_url: https://demo.netbox.dev/dcim/devices/45/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 45
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2020-12-30T19:02:57.075000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-yonkers-pdu01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 1.0
      power_outlet_count: 8
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 13
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/13/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: PDU
        id: 5
        name: PDU
        slug: pdu
        url: https://demo.netbox.dev/api/dcim/device-roles/5/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Yonkers
        id: 14
        name: DM-Yonkers
        slug: dm-yonkers
        url: https://demo.netbox.dev/api/dcim/sites/14/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/45/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context:
        syslog-servers:
        - 192.168.1.100
      config_template: null
      console_port_count: 2
      console_server_port_count: 0
      created: '2020-12-20T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 13
        display: ISR 1111-8P
        id: 6
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: ISR 1111-8P
        slug: isr1111
        url: https://demo.netbox.dev/api/dcim/device-types/6/
      display: dmi01-yonkers-rtr01
      display_url: https://demo.netbox.dev/dcim/devices/13/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 13
      interface_count: 14
      inventory_item_count: 0
      last_updated: '2020-12-20T02:56:52.908000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-yonkers-rtr01
      oob_ip: null
      owner: null
      parent_device: null
      platform:
        _depth: 0
        description: ''
        device_count: 0
        display: Cisco IOS
        id: 1
        name: Cisco IOS
        slug: cisco-ios
        url: https://demo.netbox.dev/api/dcim/platforms/1/
        virtualmachine_count: 0
      position: 4.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 13
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/13/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Router
        id: 1
        name: Router
        slug: router
        url: https://demo.netbox.dev/api/dcim/device-roles/1/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Yonkers
        id: 14
        name: DM-Yonkers
        slug: dm-yonkers
        url: https://demo.netbox.dev/api/dcim/sites/14/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/13/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2020-12-22T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 16
        display: C9200-48P
        id: 7
        manufacturer:
          description: ''
          display: Cisco
          id: 3
          name: Cisco
          slug: cisco
          url: https://demo.netbox.dev/api/dcim/manufacturers/3/
        model: C9200-48P
        slug: c9200-48p
        url: https://demo.netbox.dev/api/dcim/device-types/7/
      display: dmi01-yonkers-sw01
      display_url: https://demo.netbox.dev/dcim/devices/26/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 26
      interface_count: 52
      inventory_item_count: 0
      last_updated: '2020-12-22T02:11:12.705000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: dmi01-yonkers-sw01
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 10.0
      power_outlet_count: 0
      power_port_count: 1
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Comms closet
        id: 13
        name: Comms closet
        url: https://demo.netbox.dev/api/dcim/racks/13/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Access Switch
        id: 4
        name: Access Switch
        slug: access-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/4/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: DM-Yonkers
        id: 14
        name: DM-Yonkers
        slug: dm-yonkers
        url: https://demo.netbox.dev/api/dcim/sites/14/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/dcim/devices/26/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 2
      console_server_port_count: 0
      created: '2021-04-02T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 2
        display: EX9214
        id: 3
        manufacturer:
          description: ''
          display: Juniper
          id: 7
          name: Juniper
          slug: juniper
          url: https://demo.netbox.dev/api/dcim/manufacturers/7/
        model: EX9214
        slug: ex9214
        url: https://demo.netbox.dev/api/dcim/device-types/3/
      display: ncsu-coreswitch1
      display_url: https://demo.netbox.dev/dcim/devices/96/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 96
      interface_count: 64
      inventory_item_count: 0
      last_updated: '2021-04-02T17:31:41.398000Z'
      latitude: null
      local_context_data: null
      location:
        _depth: 0
        description: ''
        display: Row 1
        id: 1
        name: Row 1
        rack_count: 0
        slug: row-1
        url: https://demo.netbox.dev/api/dcim/locations/1/
      longitude: null
      module_bay_count: 14
      name: ncsu-coreswitch1
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 6.0
      power_outlet_count: 0
      power_port_count: 4
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: R103
        id: 16
        name: R103
        url: https://demo.netbox.dev/api/dcim/racks/16/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Core Switch
        id: 2
        name: Core Switch
        slug: core-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/2/
        virtualmachine_count: 0
      serial: ''
      site:
        description: Main Distribution Frame
        display: MDF
        id: 21
        name: MDF
        slug: ncsu-065
        url: https://demo.netbox.dev/api/dcim/sites/21/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: NC State University
        id: 13
        name: NC State University
        slug: nc-state
        url: https://demo.netbox.dev/api/tenancy/tenants/13/
      url: https://demo.netbox.dev/api/dcim/devices/96/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 2
      console_server_port_count: 0
      created: '2021-04-02T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 2
        display: EX9214
        id: 3
        manufacturer:
          description: ''
          display: Juniper
          id: 7
          name: Juniper
          slug: juniper
          url: https://demo.netbox.dev/api/dcim/manufacturers/7/
        model: EX9214
        slug: ex9214
        url: https://demo.netbox.dev/api/dcim/device-types/3/
      display: ncsu-coreswitch2
      display_url: https://demo.netbox.dev/dcim/devices/97/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 97
      interface_count: 64
      inventory_item_count: 0
      last_updated: '2021-04-02T17:31:56.519000Z'
      latitude: null
      local_context_data: null
      location:
        _depth: 0
        description: ''
        display: Row 1
        id: 1
        name: Row 1
        rack_count: 0
        slug: row-1
        url: https://demo.netbox.dev/api/dcim/locations/1/
      longitude: null
      module_bay_count: 14
      name: ncsu-coreswitch2
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 6.0
      power_outlet_count: 0
      power_port_count: 4
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: R104
        id: 17
        name: R104
        url: https://demo.netbox.dev/api/dcim/racks/17/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Core Switch
        id: 2
        name: Core Switch
        slug: core-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/2/
        virtualmachine_count: 0
      serial: ''
      site:
        description: Main Distribution Frame
        display: MDF
        id: 21
        name: MDF
        slug: ncsu-065
        url: https://demo.netbox.dev/api/dcim/sites/21/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: NC State University
        id: 13
        name: NC State University
        slug: nc-state
        url: https://demo.netbox.dev/api/tenancy/tenants/13/
      url: https://demo.netbox.dev/api/dcim/devices/97/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 1
      console_server_port_count: 0
      created: '2021-04-02T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 3
        display: QFX5110-48S-4C
        id: 12
        manufacturer:
          description: ''
          display: Juniper
          id: 7
          name: Juniper
          slug: juniper
          url: https://demo.netbox.dev/api/dcim/manufacturers/7/
        model: QFX5110-48S-4C
        slug: qfx5110-48s-4c
        url: https://demo.netbox.dev/api/dcim/device-types/12/
      display: ncsu117-distswitch1
      display_url: https://demo.netbox.dev/dcim/devices/94/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 94
      interface_count: 53
      inventory_item_count: 0
      last_updated: '2021-04-02T17:29:22.719000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: ncsu117-distswitch1
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 36.0
      power_outlet_count: 0
      power_port_count: 2
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: IDF117
        id: 40
        name: IDF117
        url: https://demo.netbox.dev/api/dcim/racks/40/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Distribution Switch
        id: 3
        name: Distribution Switch
        slug: distribution-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/3/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: D. S. Weaver Labs
        id: 22
        name: D. S. Weaver Labs
        slug: ncsu-117
        url: https://demo.netbox.dev/api/dcim/sites/22/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: NC State University
        id: 13
        name: NC State University
        slug: nc-state
        url: https://demo.netbox.dev/api/tenancy/tenants/13/
      url: https://demo.netbox.dev/api/dcim/devices/94/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 1
      console_server_port_count: 0
      created: '2021-04-02T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 3
        display: QFX5110-48S-4C
        id: 12
        manufacturer:
          description: ''
          display: Juniper
          id: 7
          name: Juniper
          slug: juniper
          url: https://demo.netbox.dev/api/dcim/manufacturers/7/
        model: QFX5110-48S-4C
        slug: qfx5110-48s-4c
        url: https://demo.netbox.dev/api/dcim/device-types/12/
      display: ncsu118-distswitch1
      display_url: https://demo.netbox.dev/dcim/devices/95/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 95
      interface_count: 53
      inventory_item_count: 0
      last_updated: '2021-04-02T17:29:56.066000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: ncsu118-distswitch1
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 36.0
      power_outlet_count: 0
      power_port_count: 2
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: IDF118
        id: 38
        name: IDF118
        url: https://demo.netbox.dev/api/dcim/racks/38/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Distribution Switch
        id: 3
        name: Distribution Switch
        slug: distribution-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/3/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: Grinnells Lab
        id: 23
        name: Grinnells Lab
        slug: ncsu-118
        url: https://demo.netbox.dev/api/dcim/sites/23/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: NC State University
        id: 13
        name: NC State University
        slug: nc-state
        url: https://demo.netbox.dev/api/tenancy/tenants/13/
      url: https://demo.netbox.dev/api/dcim/devices/95/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 1
      console_server_port_count: 0
      created: '2021-04-02T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 3
        display: QFX5110-48S-4C
        id: 12
        manufacturer:
          description: ''
          display: Juniper
          id: 7
          name: Juniper
          slug: juniper
          url: https://demo.netbox.dev/api/dcim/manufacturers/7/
        model: QFX5110-48S-4C
        slug: qfx5110-48s-4c
        url: https://demo.netbox.dev/api/dcim/device-types/12/
      display: ncsu128-distswitch1
      display_url: https://demo.netbox.dev/dcim/devices/93/
      face:
        label: Front
        value: front
      front_port_count: 0
      id: 93
      interface_count: 53
      inventory_item_count: 0
      last_updated: '2021-04-02T17:28:42.498000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: ncsu128-distswitch1
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 32.0
      power_outlet_count: 0
      power_port_count: 2
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: IDF128
        id: 39
        name: IDF128
        url: https://demo.netbox.dev/api/dcim/racks/39/
      rear_port_count: 0
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Distribution Switch
        id: 3
        name: Distribution Switch
        slug: distribution-switch
        url: https://demo.netbox.dev/api/dcim/device-roles/3/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: Butler Communications
        id: 24
        name: Butler Communications
        slug: ncsu-128
        url: https://demo.netbox.dev/api/dcim/sites/24/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: NC State University
        id: 13
        name: NC State University
        slug: nc-state
        url: https://demo.netbox.dev/api/tenancy/tenants/13/
      url: https://demo.netbox.dev/api/dcim/devices/93/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow:
        label: Rear to side
        value: rear-to-side
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2026-03-23T15:19:02.851159Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: lk
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 7
        display: 48-Pair Fiber Panel
        id: 11
        manufacturer:
          description: ''
          display: Generic
          id: 13
          name: Generic
          slug: generic
          url: https://demo.netbox.dev/api/dcim/manufacturers/13/
        model: 48-Pair Fiber Panel
        slug: 48-pair-fiber-panel
        url: https://demo.netbox.dev/api/dcim/device-types/11/
      display: Patch Panel 1
      display_url: https://demo.netbox.dev/dcim/devices/113/
      face: null
      front_port_count: 48
      id: 113
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2026-03-23T15:19:02.851175Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: Patch Panel 1
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: null
      power_outlet_count: 0
      power_port_count: 0
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack: null
      rear_port_count: 1
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Patch Panel
        id: 6
        name: Patch Panel
        slug: patch-panel
        url: https://demo.netbox.dev/api/dcim/device-roles/6/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: Butler Communications
        id: 24
        name: Butler Communications
        slug: ncsu-128
        url: https://demo.netbox.dev/api/dcim/sites/24/
      status:
        label: Active
        value: active
      tags: []
      tenant: null
      url: https://demo.netbox.dev/api/dcim/devices/113/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2021-04-02T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 7
        display: 48-Pair Fiber Panel
        id: 11
        manufacturer:
          description: ''
          display: Generic
          id: 13
          name: Generic
          slug: generic
          url: https://demo.netbox.dev/api/dcim/manufacturers/13/
        model: 48-Pair Fiber Panel
        slug: 48-pair-fiber-panel
        url: https://demo.netbox.dev/api/dcim/device-types/11/
      display: PP:B117
      display_url: https://demo.netbox.dev/dcim/devices/88/
      face:
        label: Front
        value: front
      front_port_count: 48
      id: 88
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2021-04-02T17:17:28.425000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: PP:B117
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 37.0
      power_outlet_count: 0
      power_port_count: 0
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Plant 1
        id: 41
        name: Plant 1
        url: https://demo.netbox.dev/api/dcim/racks/41/
      rear_port_count: 1
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Patch Panel
        id: 6
        name: Patch Panel
        slug: patch-panel
        url: https://demo.netbox.dev/api/dcim/device-roles/6/
        virtualmachine_count: 0
      serial: ''
      site:
        description: Main Distribution Frame
        display: MDF
        id: 21
        name: MDF
        slug: ncsu-065
        url: https://demo.netbox.dev/api/dcim/sites/21/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: NC State University
        id: 13
        name: NC State University
        slug: nc-state
        url: https://demo.netbox.dev/api/tenancy/tenants/13/
      url: https://demo.netbox.dev/api/dcim/devices/88/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2021-04-02T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 7
        display: 48-Pair Fiber Panel
        id: 11
        manufacturer:
          description: ''
          display: Generic
          id: 13
          name: Generic
          slug: generic
          url: https://demo.netbox.dev/api/dcim/manufacturers/13/
        model: 48-Pair Fiber Panel
        slug: 48-pair-fiber-panel
        url: https://demo.netbox.dev/api/dcim/device-types/11/
      display: PP:B118
      display_url: https://demo.netbox.dev/dcim/devices/89/
      face:
        label: Front
        value: front
      front_port_count: 48
      id: 89
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2021-04-02T17:17:57.268000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: PP:B118
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 35.0
      power_outlet_count: 0
      power_port_count: 0
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Plant 1
        id: 41
        name: Plant 1
        url: https://demo.netbox.dev/api/dcim/racks/41/
      rear_port_count: 1
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Patch Panel
        id: 6
        name: Patch Panel
        slug: patch-panel
        url: https://demo.netbox.dev/api/dcim/device-roles/6/
        virtualmachine_count: 0
      serial: ''
      site:
        description: Main Distribution Frame
        display: MDF
        id: 21
        name: MDF
        slug: ncsu-065
        url: https://demo.netbox.dev/api/dcim/sites/21/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: NC State University
        id: 13
        name: NC State University
        slug: nc-state
        url: https://demo.netbox.dev/api/tenancy/tenants/13/
      url: https://demo.netbox.dev/api/dcim/devices/89/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2021-04-02T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 7
        display: 48-Pair Fiber Panel
        id: 11
        manufacturer:
          description: ''
          display: Generic
          id: 13
          name: Generic
          slug: generic
          url: https://demo.netbox.dev/api/dcim/manufacturers/13/
        model: 48-Pair Fiber Panel
        slug: 48-pair-fiber-panel
        url: https://demo.netbox.dev/api/dcim/device-types/11/
      display: PP:B128
      display_url: https://demo.netbox.dev/dcim/devices/87/
      face:
        label: Front
        value: front
      front_port_count: 48
      id: 87
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2021-04-02T17:16:58.069000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: PP:B128
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 39.0
      power_outlet_count: 0
      power_port_count: 0
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: Plant 1
        id: 41
        name: Plant 1
        url: https://demo.netbox.dev/api/dcim/racks/41/
      rear_port_count: 1
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Patch Panel
        id: 6
        name: Patch Panel
        slug: patch-panel
        url: https://demo.netbox.dev/api/dcim/device-roles/6/
        virtualmachine_count: 0
      serial: ''
      site:
        description: Main Distribution Frame
        display: MDF
        id: 21
        name: MDF
        slug: ncsu-065
        url: https://demo.netbox.dev/api/dcim/sites/21/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: NC State University
        id: 13
        name: NC State University
        slug: nc-state
        url: https://demo.netbox.dev/api/tenancy/tenants/13/
      url: https://demo.netbox.dev/api/dcim/devices/87/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2021-04-02T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 7
        display: 48-Pair Fiber Panel
        id: 11
        manufacturer:
          description: ''
          display: Generic
          id: 13
          name: Generic
          slug: generic
          url: https://demo.netbox.dev/api/dcim/manufacturers/13/
        model: 48-Pair Fiber Panel
        slug: 48-pair-fiber-panel
        url: https://demo.netbox.dev/api/dcim/device-types/11/
      display: PP:MDF
      display_url: https://demo.netbox.dev/dcim/devices/90/
      face:
        label: Front
        value: front
      front_port_count: 48
      id: 90
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2021-04-02T17:19:12.870000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: PP:MDF
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 39.0
      power_outlet_count: 0
      power_port_count: 0
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: IDF128
        id: 39
        name: IDF128
        url: https://demo.netbox.dev/api/dcim/racks/39/
      rear_port_count: 1
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Patch Panel
        id: 6
        name: Patch Panel
        slug: patch-panel
        url: https://demo.netbox.dev/api/dcim/device-roles/6/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: Butler Communications
        id: 24
        name: Butler Communications
        slug: ncsu-128
        url: https://demo.netbox.dev/api/dcim/sites/24/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: NC State University
        id: 13
        name: NC State University
        slug: nc-state
        url: https://demo.netbox.dev/api/tenancy/tenants/13/
      url: https://demo.netbox.dev/api/dcim/devices/90/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    - airflow: null
      asset_tag: null
      cluster: null
      comments: ''
      config_context: {}
      config_template: null
      console_port_count: 0
      console_server_port_count: 0
      created: '2021-04-02T00:00:00Z'
      custom_fields:
        Exposure: null
        Test2: null
        cpe: null
        environment: null
      description: ''
      device_bay_count: 0
      device_type:
        description: ''
        device_count: 7
        display: 48-Pair Fiber Panel
        id: 11
        manufacturer:
          description: ''
          display: Generic
          id: 13
          name: Generic
          slug: generic
          url: https://demo.netbox.dev/api/dcim/manufacturers/13/
        model: 48-Pair Fiber Panel
        slug: 48-pair-fiber-panel
        url: https://demo.netbox.dev/api/dcim/device-types/11/
      display: PP:MDF
      display_url: https://demo.netbox.dev/dcim/devices/91/
      face:
        label: Front
        value: front
      front_port_count: 48
      id: 91
      interface_count: 0
      inventory_item_count: 0
      last_updated: '2021-04-02T17:19:41.498000Z'
      latitude: null
      local_context_data: null
      location: null
      longitude: null
      module_bay_count: 0
      name: PP:MDF
      oob_ip: null
      owner: null
      parent_device: null
      platform: null
      position: 39.0
      power_outlet_count: 0
      power_port_count: 0
      primary_ip: null
      primary_ip4: null
      primary_ip6: null
      rack:
        description: ''
        display: IDF117
        id: 40
        name: IDF117
        url: https://demo.netbox.dev/api/dcim/racks/40/
      rear_port_count: 1
      role:
        _depth: 0
        description: ''
        device_count: 0
        display: Patch Panel
        id: 6
        name: Patch Panel
        slug: patch-panel
        url: https://demo.netbox.dev/api/dcim/device-roles/6/
        virtualmachine_count: 0
      serial: ''
      site:
        description: ''
        display: D. S. Weaver Labs
        id: 22
        name: D. S. Weaver Labs
        slug: ncsu-117
        url: https://demo.netbox.dev/api/dcim/sites/22/
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: NC State University
        id: 13
        name: NC State University
        slug: nc-state
        url: https://demo.netbox.dev/api/tenancy/tenants/13/
      url: https://demo.netbox.dev/api/dcim/devices/91/
      vc_position: null
      vc_priority: null
      virtual_chassis: null
    ```

=== ":material-language-markdown: Markdown Output"

    | ID | Name | Display | Status | Role | Site | Location | Tenant |
    | --- | --- | --- | --- | --- | --- | --- | --- |
    | 27 | dmi01-akron-pdu01 | dmi01-akron-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"PDU","id":5,"name":"PDU","slug":"pdu","url":"https://demo.netbox.dev/api/dcim/device-roles/5/","virtualmachine_count":0} | {"description":"","display":"DM-Akron","id":2,"name":"DM-Akron","slug":"dm-akron","url":"https://demo.netbox.dev/api/dcim/sites/2/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 1 | dmi01-akron-rtr01 | dmi01-akron-rtr01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Router","id":1,"name":"Router","slug":"router","url":"https://demo.netbox.dev/api/dcim/device-roles/1/","virtualmachine_count":0} | {"description":"","display":"DM-Akron","id":2,"name":"DM-Akron","slug":"dm-akron","url":"https://demo.netbox.dev/api/dcim/sites/2/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 14 | dmi01-akron-sw01 | dmi01-akron-sw01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Access Switch","id":4,"name":"Access Switch","slug":"access-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/4/","virtualmachine_count":0} | {"description":"","display":"DM-Akron","id":2,"name":"DM-Akron","slug":"dm-akron","url":"https://demo.netbox.dev/api/dcim/sites/2/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 34 | dmi01-albany-pdu01 | dmi01-albany-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"PDU","id":5,"name":"PDU","slug":"pdu","url":"https://demo.netbox.dev/api/dcim/device-roles/5/","virtualmachine_count":0} | {"description":"","display":"DM-Albany","id":3,"name":"DM-Albany","slug":"dm-albany","url":"https://demo.netbox.dev/api/dcim/sites/3/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 2 | dmi01-albany-rtr01 | dmi01-albany-rtr01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Router","id":1,"name":"Router","slug":"router","url":"https://demo.netbox.dev/api/dcim/device-roles/1/","virtualmachine_count":0} | {"description":"","display":"DM-Albany","id":3,"name":"DM-Albany","slug":"dm-albany","url":"https://demo.netbox.dev/api/dcim/sites/3/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 15 | dmi01-albany-sw01 | dmi01-albany-sw01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Access Switch","id":4,"name":"Access Switch","slug":"access-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/4/","virtualmachine_count":0} | {"description":"","display":"DM-Albany","id":3,"name":"DM-Albany","slug":"dm-albany","url":"https://demo.netbox.dev/api/dcim/sites/3/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 35 | dmi01-binghamton-pdu01 | dmi01-binghamton-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"PDU","id":5,"name":"PDU","slug":"pdu","url":"https://demo.netbox.dev/api/dcim/device-roles/5/","virtualmachine_count":0} | {"description":"","display":"DM-Binghamton","id":4,"name":"DM-Binghamton","slug":"dm-binghamton","url":"https://demo.netbox.dev/api/dcim/sites/4/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 3 | dmi01-binghamton-rtr01 | dmi01-binghamton-rtr01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Router","id":1,"name":"Router","slug":"router","url":"https://demo.netbox.dev/api/dcim/device-roles/1/","virtualmachine_count":0} | {"description":"","display":"DM-Binghamton","id":4,"name":"DM-Binghamton","slug":"dm-binghamton","url":"https://demo.netbox.dev/api/dcim/sites/4/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 16 | dmi01-binghamton-sw01 | dmi01-binghamton-sw01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Access Switch","id":4,"name":"Access Switch","slug":"access-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/4/","virtualmachine_count":0} | {"description":"","display":"DM-Binghamton","id":4,"name":"DM-Binghamton","slug":"dm-binghamton","url":"https://demo.netbox.dev/api/dcim/sites/4/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 36 | dmi01-buffalo-pdu01 | dmi01-buffalo-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"PDU","id":5,"name":"PDU","slug":"pdu","url":"https://demo.netbox.dev/api/dcim/device-roles/5/","virtualmachine_count":0} | {"description":"","display":"DM-Buffalo","id":5,"name":"DM-Buffalo","slug":"dm-buffalo","url":"https://demo.netbox.dev/api/dcim/sites/5/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 4 | dmi01-buffalo-rtr01 | dmi01-buffalo-rtr01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Router","id":1,"name":"Router","slug":"router","url":"https://demo.netbox.dev/api/dcim/device-roles/1/","virtualmachine_count":0} | {"description":"","display":"DM-Buffalo","id":5,"name":"DM-Buffalo","slug":"dm-buffalo","url":"https://demo.netbox.dev/api/dcim/sites/5/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 17 | dmi01-buffalo-sw01 | dmi01-buffalo-sw01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Access Switch","id":4,"name":"Access Switch","slug":"access-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/4/","virtualmachine_count":0} | {"description":"","display":"DM-Buffalo","id":5,"name":"DM-Buffalo","slug":"dm-buffalo","url":"https://demo.netbox.dev/api/dcim/sites/5/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 37 | dmi01-camden-pdu01 | dmi01-camden-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"PDU","id":5,"name":"PDU","slug":"pdu","url":"https://demo.netbox.dev/api/dcim/device-roles/5/","virtualmachine_count":0} | {"description":"","display":"DM-Camden","id":6,"name":"DM-Camden","slug":"dm-camden","url":"https://demo.netbox.dev/api/dcim/sites/6/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 5 | dmi01-camden-rtr01 | dmi01-camden-rtr01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Router","id":1,"name":"Router","slug":"router","url":"https://demo.netbox.dev/api/dcim/device-roles/1/","virtualmachine_count":0} | {"description":"","display":"DM-Camden","id":6,"name":"DM-Camden","slug":"dm-camden","url":"https://demo.netbox.dev/api/dcim/sites/6/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 18 | dmi01-camden-sw01 | dmi01-camden-sw01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Access Switch","id":4,"name":"Access Switch","slug":"access-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/4/","virtualmachine_count":0} | {"description":"","display":"DM-Camden","id":6,"name":"DM-Camden","slug":"dm-camden","url":"https://demo.netbox.dev/api/dcim/sites/6/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 38 | dmi01-nashua-pdu01 | dmi01-nashua-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"PDU","id":5,"name":"PDU","slug":"pdu","url":"https://demo.netbox.dev/api/dcim/device-roles/5/","virtualmachine_count":0} | {"description":"","display":"DM-Nashua","id":7,"name":"DM-Nashua","slug":"dm-nashua","url":"https://demo.netbox.dev/api/dcim/sites/7/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 6 | dmi01-nashua-rtr01 | dmi01-nashua-rtr01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Router","id":1,"name":"Router","slug":"router","url":"https://demo.netbox.dev/api/dcim/device-roles/1/","virtualmachine_count":0} | {"description":"","display":"DM-Nashua","id":7,"name":"DM-Nashua","slug":"dm-nashua","url":"https://demo.netbox.dev/api/dcim/sites/7/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 19 | dmi01-nashua-sw01 | dmi01-nashua-sw01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Access Switch","id":4,"name":"Access Switch","slug":"access-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/4/","virtualmachine_count":0} | {"description":"","display":"DM-Nashua","id":7,"name":"DM-Nashua","slug":"dm-nashua","url":"https://demo.netbox.dev/api/dcim/sites/7/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 39 | dmi01-pittsfield-pdu01 | dmi01-pittsfield-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"PDU","id":5,"name":"PDU","slug":"pdu","url":"https://demo.netbox.dev/api/dcim/device-roles/5/","virtualmachine_count":0} | {"description":"","display":"DM-Pittsfield","id":8,"name":"DM-Pittsfield","slug":"dm-pittsfield","url":"https://demo.netbox.dev/api/dcim/sites/8/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 7 | dmi01-pittsfield-rtr01 | dmi01-pittsfield-rtr01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Router","id":1,"name":"Router","slug":"router","url":"https://demo.netbox.dev/api/dcim/device-roles/1/","virtualmachine_count":0} | {"description":"","display":"DM-Pittsfield","id":8,"name":"DM-Pittsfield","slug":"dm-pittsfield","url":"https://demo.netbox.dev/api/dcim/sites/8/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 20 | dmi01-pittsfield-sw01 | dmi01-pittsfield-sw01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Access Switch","id":4,"name":"Access Switch","slug":"access-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/4/","virtualmachine_count":0} | {"description":"","display":"DM-Pittsfield","id":8,"name":"DM-Pittsfield","slug":"dm-pittsfield","url":"https://demo.netbox.dev/api/dcim/sites/8/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 40 | dmi01-rochester-pdu01 | dmi01-rochester-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"PDU","id":5,"name":"PDU","slug":"pdu","url":"https://demo.netbox.dev/api/dcim/device-roles/5/","virtualmachine_count":0} | {"description":"","display":"DM-Rochester","id":9,"name":"DM-Rochester","slug":"dm-rochester","url":"https://demo.netbox.dev/api/dcim/sites/9/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 8 | dmi01-rochester-rtr01 | dmi01-rochester-rtr01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Router","id":1,"name":"Router","slug":"router","url":"https://demo.netbox.dev/api/dcim/device-roles/1/","virtualmachine_count":0} | {"description":"","display":"DM-Rochester","id":9,"name":"DM-Rochester","slug":"dm-rochester","url":"https://demo.netbox.dev/api/dcim/sites/9/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 21 | dmi01-rochster-sw01 | dmi01-rochster-sw01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Access Switch","id":4,"name":"Access Switch","slug":"access-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/4/","virtualmachine_count":0} | {"description":"","display":"DM-Rochester","id":9,"name":"DM-Rochester","slug":"dm-rochester","url":"https://demo.netbox.dev/api/dcim/sites/9/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 41 | dmi01-scranton-pdu01 | dmi01-scranton-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"PDU","id":5,"name":"PDU","slug":"pdu","url":"https://demo.netbox.dev/api/dcim/device-roles/5/","virtualmachine_count":0} | {"description":"","display":"DM-Scranton","id":10,"name":"DM-Scranton","slug":"dm-scranton","url":"https://demo.netbox.dev/api/dcim/sites/10/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 9 | dmi01-scranton-rtr01 | dmi01-scranton-rtr01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Router","id":1,"name":"Router","slug":"router","url":"https://demo.netbox.dev/api/dcim/device-roles/1/","virtualmachine_count":0} | {"description":"","display":"DM-Scranton","id":10,"name":"DM-Scranton","slug":"dm-scranton","url":"https://demo.netbox.dev/api/dcim/sites/10/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 22 | dmi01-scranton-sw01 | dmi01-scranton-sw01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Access Switch","id":4,"name":"Access Switch","slug":"access-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/4/","virtualmachine_count":0} | {"description":"","display":"DM-Scranton","id":10,"name":"DM-Scranton","slug":"dm-scranton","url":"https://demo.netbox.dev/api/dcim/sites/10/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 42 | dmi01-stamford-pdu01 | dmi01-stamford-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"PDU","id":5,"name":"PDU","slug":"pdu","url":"https://demo.netbox.dev/api/dcim/device-roles/5/","virtualmachine_count":0} | {"description":"","display":"DM-Stamford","id":11,"name":"DM-Stamford","slug":"dm-stamford","url":"https://demo.netbox.dev/api/dcim/sites/11/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 10 | dmi01-stamford-rtr01 | dmi01-stamford-rtr01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Router","id":1,"name":"Router","slug":"router","url":"https://demo.netbox.dev/api/dcim/device-roles/1/","virtualmachine_count":0} | {"description":"","display":"DM-Stamford","id":11,"name":"DM-Stamford","slug":"dm-stamford","url":"https://demo.netbox.dev/api/dcim/sites/11/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 23 | dmi01-stamford-sw01 | dmi01-stamford-sw01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Access Switch","id":4,"name":"Access Switch","slug":"access-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/4/","virtualmachine_count":0} | {"description":"","display":"DM-Stamford","id":11,"name":"DM-Stamford","slug":"dm-stamford","url":"https://demo.netbox.dev/api/dcim/sites/11/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 43 | dmi01-syracuse-pdu01 | dmi01-syracuse-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"PDU","id":5,"name":"PDU","slug":"pdu","url":"https://demo.netbox.dev/api/dcim/device-roles/5/","virtualmachine_count":0} | {"description":"","display":"DM-Syracuse","id":12,"name":"DM-Syracuse","slug":"dm-syracuse","url":"https://demo.netbox.dev/api/dcim/sites/12/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 11 | dmi01-syracuse-rtr01 | dmi01-syracuse-rtr01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Router","id":1,"name":"Router","slug":"router","url":"https://demo.netbox.dev/api/dcim/device-roles/1/","virtualmachine_count":0} | {"description":"","display":"DM-Syracuse","id":12,"name":"DM-Syracuse","slug":"dm-syracuse","url":"https://demo.netbox.dev/api/dcim/sites/12/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 24 | dmi01-syracuse-sw01 | dmi01-syracuse-sw01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Access Switch","id":4,"name":"Access Switch","slug":"access-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/4/","virtualmachine_count":0} | {"description":"","display":"DM-Syracuse","id":12,"name":"DM-Syracuse","slug":"dm-syracuse","url":"https://demo.netbox.dev/api/dcim/sites/12/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 44 | dmi01-utica-pdu01 | dmi01-utica-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"PDU","id":5,"name":"PDU","slug":"pdu","url":"https://demo.netbox.dev/api/dcim/device-roles/5/","virtualmachine_count":0} | {"description":"","display":"DM-Utica","id":13,"name":"DM-Utica","slug":"dm-utica","url":"https://demo.netbox.dev/api/dcim/sites/13/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 12 | dmi01-utica-rtr01 | dmi01-utica-rtr01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Router","id":1,"name":"Router","slug":"router","url":"https://demo.netbox.dev/api/dcim/device-roles/1/","virtualmachine_count":0} | {"description":"","display":"DM-Utica","id":13,"name":"DM-Utica","slug":"dm-utica","url":"https://demo.netbox.dev/api/dcim/sites/13/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 25 | dmi01-utica-sw01 | dmi01-utica-sw01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Access Switch","id":4,"name":"Access Switch","slug":"access-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/4/","virtualmachine_count":0} | {"description":"","display":"DM-Utica","id":13,"name":"DM-Utica","slug":"dm-utica","url":"https://demo.netbox.dev/api/dcim/sites/13/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 45 | dmi01-yonkers-pdu01 | dmi01-yonkers-pdu01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"PDU","id":5,"name":"PDU","slug":"pdu","url":"https://demo.netbox.dev/api/dcim/device-roles/5/","virtualmachine_count":0} | {"description":"","display":"DM-Yonkers","id":14,"name":"DM-Yonkers","slug":"dm-yonkers","url":"https://demo.netbox.dev/api/dcim/sites/14/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 13 | dmi01-yonkers-rtr01 | dmi01-yonkers-rtr01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Router","id":1,"name":"Router","slug":"router","url":"https://demo.netbox.dev/api/dcim/device-roles/1/","virtualmachine_count":0} | {"description":"","display":"DM-Yonkers","id":14,"name":"DM-Yonkers","slug":"dm-yonkers","url":"https://demo.netbox.dev/api/dcim/sites/14/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 26 | dmi01-yonkers-sw01 | dmi01-yonkers-sw01 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Access Switch","id":4,"name":"Access Switch","slug":"access-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/4/","virtualmachine_count":0} | {"description":"","display":"DM-Yonkers","id":14,"name":"DM-Yonkers","slug":"dm-yonkers","url":"https://demo.netbox.dev/api/dcim/sites/14/"} | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 96 | ncsu-coreswitch1 | ncsu-coreswitch1 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Core Switch","id":2,"name":"Core Switch","slug":"core-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/2/","virtualmachine_count":0} | {"description":"Main Distribution Frame","display":"MDF","id":21,"name":"MDF","slug":"ncsu-065","url":"https://demo.netbox.dev/api/dcim/sites/21/"} | {"_depth":0,"description":"","display":"Row 1","id":1,"name":"Row 1","rack_count":0,"slug":"row-1","url":"https://demo.netbox.dev/api/dcim/locations/1/"} | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
    | 97 | ncsu-coreswitch2 | ncsu-coreswitch2 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Core Switch","id":2,"name":"Core Switch","slug":"core-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/2/","virtualmachine_count":0} | {"description":"Main Distribution Frame","display":"MDF","id":21,"name":"MDF","slug":"ncsu-065","url":"https://demo.netbox.dev/api/dcim/sites/21/"} | {"_depth":0,"description":"","display":"Row 1","id":1,"name":"Row 1","rack_count":0,"slug":"row-1","url":"https://demo.netbox.dev/api/dcim/locations/1/"} | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
    | 94 | ncsu117-distswitch1 | ncsu117-distswitch1 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Distribution Switch","id":3,"name":"Distribution Switch","slug":"distribution-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/3/","virtualmachine_count":0} | {"description":"","display":"D. S. Weaver Labs","id":22,"name":"D. S. Weaver Labs","slug":"ncsu-117","url":"https://demo.netbox.dev/api/dcim/sites/22/"} | - | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
    | 95 | ncsu118-distswitch1 | ncsu118-distswitch1 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Distribution Switch","id":3,"name":"Distribution Switch","slug":"distribution-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/3/","virtualmachine_count":0} | {"description":"","display":"Grinnells Lab","id":23,"name":"Grinnells Lab","slug":"ncsu-118","url":"https://demo.netbox.dev/api/dcim/sites/23/"} | - | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
    | 93 | ncsu128-distswitch1 | ncsu128-distswitch1 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Distribution Switch","id":3,"name":"Distribution Switch","slug":"distribution-switch","url":"https://demo.netbox.dev/api/dcim/device-roles/3/","virtualmachine_count":0} | {"description":"","display":"Butler Communications","id":24,"name":"Butler Communications","slug":"ncsu-128","url":"https://demo.netbox.dev/api/dcim/sites/24/"} | - | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
    | 113 | Patch Panel 1 | Patch Panel 1 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Patch Panel","id":6,"name":"Patch Panel","slug":"patch-panel","url":"https://demo.netbox.dev/api/dcim/device-roles/6/","virtualmachine_count":0} | {"description":"","display":"Butler Communications","id":24,"name":"Butler Communications","slug":"ncsu-128","url":"https://demo.netbox.dev/api/dcim/sites/24/"} | - | - |
    | 88 | PP:B117 | PP:B117 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Patch Panel","id":6,"name":"Patch Panel","slug":"patch-panel","url":"https://demo.netbox.dev/api/dcim/device-roles/6/","virtualmachine_count":0} | {"description":"Main Distribution Frame","display":"MDF","id":21,"name":"MDF","slug":"ncsu-065","url":"https://demo.netbox.dev/api/dcim/sites/21/"} | - | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
    | 89 | PP:B118 | PP:B118 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Patch Panel","id":6,"name":"Patch Panel","slug":"patch-panel","url":"https://demo.netbox.dev/api/dcim/device-roles/6/","virtualmachine_count":0} | {"description":"Main Distribution Frame","display":"MDF","id":21,"name":"MDF","slug":"ncsu-065","url":"https://demo.netbox.dev/api/dcim/sites/21/"} | - | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
    | 87 | PP:B128 | PP:B128 | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Patch Panel","id":6,"name":"Patch Panel","slug":"patch-panel","url":"https://demo.netbox.dev/api/dcim/device-roles/6/","virtualmachine_count":0} | {"description":"Main Distribution Frame","display":"MDF","id":21,"name":"MDF","slug":"ncsu-065","url":"https://demo.netbox.dev/api/dcim/sites/21/"} | - | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
    | 90 | PP:MDF | PP:MDF | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Patch Panel","id":6,"name":"Patch Panel","slug":"patch-panel","url":"https://demo.netbox.dev/api/dcim/device-roles/6/","virtualmachine_count":0} | {"description":"","display":"Butler Communications","id":24,"name":"Butler Communications","slug":"ncsu-128","url":"https://demo.netbox.dev/api/dcim/sites/24/"} | - | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
    | 91 | PP:MDF | PP:MDF | {"label":"Active","value":"active"} | {"_depth":0,"description":"","device_count":0,"display":"Patch Panel","id":6,"name":"Patch Panel","slug":"patch-panel","url":"https://demo.netbox.dev/api/dcim/device-roles/6/","virtualmachine_count":0} | {"description":"","display":"D. S. Weaver Labs","id":22,"name":"D. S. Weaver Labs","slug":"ncsu-117","url":"https://demo.netbox.dev/api/dcim/sites/22/"} | - | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">3.459s</span>

!!! warning "Truncated"
    Output was truncated. Full text is in `docs/generated/raw/`.

---

### `nbx demo ipam prefixes list`

=== ":material-console: Command"

    ```bash
    nbx demo ipam prefixes list --markdown
    ```

=== ":material-text-box-outline: Output"

    ```text
    Status: 200
    | ID | Display | Status | Role | Prefix | VLAN | Tenant |
    | --- | --- | --- | --- | --- | --- | --- |
    | 1 | 10.112.0.0/15 | {"label":"Container","value":"container"} | - | 10.112.0.0/15 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 2 | 10.112.0.0/17 | {"label":"Container","value":"container"} | - | 10.112.0.0/17 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 3 | 10.112.128.0/17 | {"label":"Container","value":"container"} | - | 10.112.128.0/17 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 60 | 10.112.128.0/22 | {"label":"Container","value":"container"} | - | 10.112.128.0/22 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 7 | 10.112.128.0/28 | {"label":"Active","value":"active"} | {"description":"","display":"Management","id":4,"name":"Management","slug":"management","url":"https://demo.netbox.dev/api/ipam/roles/4/"} | 10.112.128.0/28 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 8 | 10.112.129.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Data","id":1,"name":"Access - Data","slug":"access-data","url":"https://demo.netbox.dev/api/ipam/roles/1/"} | 10.112.129.0/24 | {"description":"","display":"Data (100)","id":1,"name":"Data","url":"https://demo.netbox.dev/api/ipam/vlans/1/","vid":100} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","
    
    … (truncated by character limit)
    ```

=== ":material-code-json: JSON Output"

    ```json
    {
      "count": 93,
      "next": "https://demo.netbox.dev/api/ipam/prefixes/?limit=50&offset=50",
      "previous": null,
      "results": [
        {
          "_depth": 0,
          "children": 67,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.0.0/15",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/1/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 1,
          "is_pool": false,
          "last_updated": "2020-12-30T20:00:17.126000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.0.0/15",
          "role": null,
          "scope": null,
          "scope_id": null,
          "scope_type": null,
          "status": {
            "label": "Container",
            "value": "container"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/1/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 1,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "DM HQ",
          "display": "10.112.0.0/17",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/2/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 2,
          "is_pool": false,
          "last_updated": "2020-12-30T20:00:02.450000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.0.0/17",
          "role": null,
          "scope": null,
          "scope_id": null,
          "scope_type": null,
          "status": {
            "label": "Container",
            "value": "container"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/2/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 1,
          "children": 65,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "DM branch offices",
          "display": "10.112.128.0/17",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/3/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 3,
          "is_pool": false,
          "last_updated": "2020-12-30T20:01:26.618000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.128.0/17",
          "role": null,
          "scope": null,
          "scope_id": null,
          "scope_type": null,
          "status": {
            "label": "Container",
            "value": "container"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/3/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 2,
          "children": 4,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.128.0/22",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/60/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 60,
          "is_pool": false,
          "last_updated": "2020-12-30T20:19:10.958000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.128.0/22",
          "role": null,
          "scope": {
            "description": "",
            "display": "DM-Akron",
            "id": 2,
            "name": "DM-Akron",
            "slug": "dm-akron",
            "url": "https://demo.netbox.dev/api/dcim/sites/2/"
          },
          "scope_id": 2,
          "scope_type": "dcim.site",
          "status": {
            "label": "Container",
            "value": "container"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/60/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.128.0/28",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/7/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 7,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:41.316000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.128.0/28",
          "role": {
            "description": "",
            "display": "Management",
            "id": 4,
            "name": "Management",
            "slug": "management",
            "url": "https://demo.netbox.dev/api/ipam/roles/4/"
          },
          "scope": {
            "description": "",
            "display": "DM-Akron",
            "id": 2,
            "name": "DM-Akron",
            "slug": "dm-akron",
            "url": "https://demo.netbox.dev/api/dcim/sites/2/"
          },
          "scope_id": 2,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/7/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.129.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/8/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 8,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:41.429000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.129.0/24",
          "role": {
            "description": "",
            "display": "Access - Data",
            "id": 1,
            "name": "Access - Data",
            "slug": "access-data",
            "url": "https://demo.netbox.dev/api/ipam/roles/1/"
          },
          "scope": {
            "description": "",
            "display": "DM-Akron",
            "id": 2,
            "name": "DM-Akron",
            "slug": "dm-akron",
            "url": "https://demo.netbox.dev/api/dcim/sites/2/"
          },
          "scope_id": 2,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/8/",
          "vlan": {
            "description": "",
            "display": "Data (100)",
            "id": 1,
            "name": "Data",
            "url": "https://demo.netbox.dev/api/ipam/vlans/1/",
            "vid": 100
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.130.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/9/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 9,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:41.551000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.130.0/24",
          "role": {
            "description": "",
            "display": "Access - Voice",
            "id": 2,
            "name": "Access - Voice",
            "slug": "access-voice",
            "url": "https://demo.netbox.dev/api/ipam/roles/2/"
          },
          "scope": {
            "description": "",
            "display": "DM-Akron",
            "id": 2,
            "name": "DM-Akron",
            "slug": "dm-akron",
            "url": "https://demo.netbox.dev/api/dcim/sites/2/"
          },
          "scope_id": 2,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/9/",
          "vlan": {
            "description": "",
            "display": "Voice (200)",
            "id": 2,
            "name": "Voice",
            "url": "https://demo.netbox.dev/api/ipam/vlans/2/",
            "vid": 200
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.131.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/10/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 10,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:41.639000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.131.0/24",
          "role": {
            "description": "",
            "display": "Access - Wireless",
            "id": 3,
            "name": "Access - Wireless",
            "slug": "access-wireless",
            "url": "https://demo.netbox.dev/api/ipam/roles/3/"
          },
          "scope": {
            "description": "",
            "display": "DM-Akron",
            "id": 2,
            "name": "DM-Akron",
            "slug": "dm-akron",
            "url": "https://demo.netbox.dev/api/dcim/sites/2/"
          },
          "scope_id": 2,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/10/",
          "vlan": {
            "description": "",
            "display": "Wireless (300)",
            "id": 27,
            "name": "Wireless",
            "url": "https://demo.netbox.dev/api/ipam/vlans/27/",
            "vid": 300
          },
          "vrf": null
        },
        {
          "_depth": 2,
          "children": 4,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.132.0/22",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/61/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 61,
          "is_pool": false,
          "last_updated": "2020-12-30T20:19:11.024000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.132.0/22",
          "role": null,
          "scope": {
            "description": "",
            "display": "DM-Albany",
            "id": 3,
            "name": "DM-Albany",
            "slug": "dm-albany",
            "url": "https://demo.netbox.dev/api/dcim/sites/3/"
          },
          "scope_id": 3,
          "scope_type": "dcim.site",
          "status": {
            "label": "Container",
            "value": "container"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/61/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.132.0/28",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/11/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 11,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:41.714000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.132.0/28",
          "role": {
            "description": "",
            "display": "Management",
            "id": 4,
            "name": "Management",
            "slug": "management",
            "url": "https://demo.netbox.dev/api/ipam/roles/4/"
          },
          "scope": {
            "description": "",
            "display": "DM-Albany",
            "id": 3,
            "name": "DM-Albany",
            "slug": "dm-albany",
            "url": "https://demo.netbox.dev/api/dcim/sites/3/"
          },
          "scope_id": 3,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/11/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.133.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/12/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 12,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:41.801000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.133.0/24",
          "role": {
            "description": "",
            "display": "Access - Data",
            "id": 1,
            "name": "Access - Data",
            "slug": "access-data",
            "url": "https://demo.netbox.dev/api/ipam/roles/1/"
          },
          "scope": {
            "description": "",
            "display": "DM-Albany",
            "id": 3,
            "name": "DM-Albany",
            "slug": "dm-albany",
            "url": "https://demo.netbox.dev/api/dcim/sites/3/"
          },
          "scope_id": 3,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/12/",
          "vlan": {
            "description": "",
            "display": "Data (100)",
            "id": 3,
            "name": "Data",
            "url": "https://demo.netbox.dev/api/ipam/vlans/3/",
            "vid": 100
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.134.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/13/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 13,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:41.891000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.134.0/24",
          "role": {
            "description": "",
            "display": "Access - Voice",
            "id": 2,
            "name": "Access - Voice",
            "slug": "access-voice",
            "url": "https://demo.netbox.dev/api/ipam/roles/2/"
          },
          "scope": {
            "description": "",
            "display": "DM-Albany",
            "id": 3,
            "name": "DM-Albany",
            "slug": "dm-albany",
            "url": "https://demo.netbox.dev/api/dcim/sites/3/"
          },
          "scope_id": 3,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/13/",
          "vlan": {
            "description": "",
            "display": "Voice (200)",
            "id": 4,
            "name": "Voice",
            "url": "https://demo.netbox.dev/api/ipam/vlans/4/",
            "vid": 200
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.135.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/14/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 14,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:41.975000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.135.0/24",
          "role": {
            "description": "",
            "display": "Access - Wireless",
            "id": 3,
            "name": "Access - Wireless",
            "slug": "access-wireless",
            "url": "https://demo.netbox.dev/api/ipam/roles/3/"
          },
          "scope": {
            "description": "",
            "display": "DM-Albany",
            "id": 3,
            "name": "DM-Albany",
            "slug": "dm-albany",
            "url": "https://demo.netbox.dev/api/dcim/sites/3/"
          },
          "scope_id": 3,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/14/",
          "vlan": {
            "description": "",
            "display": "Wireless (300)",
            "id": 28,
            "name": "Wireless",
            "url": "https://demo.netbox.dev/api/ipam/vlans/28/",
            "vid": 300
          },
          "vrf": null
        },
        {
          "_depth": 2,
          "children": 4,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.136.0/22",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/62/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 62,
          "is_pool": false,
          "last_updated": "2020-12-30T20:19:11.089000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.136.0/22",
          "role": null,
          "scope": {
            "description": "",
            "display": "DM-Binghamton",
            "id": 4,
            "name": "DM-Binghamton",
            "slug": "dm-binghamton",
            "url": "https://demo.netbox.dev/api/dcim/sites/4/"
          },
          "scope_id": 4,
          "scope_type": "dcim.site",
          "status": {
            "label": "Container",
            "value": "container"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/62/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.136.0/28",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/15/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 15,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:42.049000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.136.0/28",
          "role": {
            "description": "",
            "display": "Management",
            "id": 4,
            "name": "Management",
            "slug": "management",
            "url": "https://demo.netbox.dev/api/ipam/roles/4/"
          },
          "scope": {
            "description": "",
            "display": "DM-Binghamton",
            "id": 4,
            "name": "DM-Binghamton",
            "slug": "dm-binghamton",
            "url": "https://demo.netbox.dev/api/dcim/sites/4/"
          },
          "scope_id": 4,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/15/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.137.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/16/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 16,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:42.134000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.137.0/24",
          "role": {
            "description": "",
            "display": "Access - Data",
            "id": 1,
            "name": "Access - Data",
            "slug": "access-data",
            "url": "https://demo.netbox.dev/api/ipam/roles/1/"
          },
          "scope": {
            "description": "",
            "display": "DM-Binghamton",
            "id": 4,
            "name": "DM-Binghamton",
            "slug": "dm-binghamton",
            "url": "https://demo.netbox.dev/api/dcim/sites/4/"
          },
          "scope_id": 4,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/16/",
          "vlan": {
            "description": "",
            "display": "Data (100)",
            "id": 5,
            "name": "Data",
            "url": "https://demo.netbox.dev/api/ipam/vlans/5/",
            "vid": 100
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.138.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/17/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 17,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:42.220000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.138.0/24",
          "role": {
            "description": "",
            "display": "Access - Voice",
            "id": 2,
            "name": "Access - Voice",
            "slug": "access-voice",
            "url": "https://demo.netbox.dev/api/ipam/roles/2/"
          },
          "scope": {
            "description": "",
            "display": "DM-Binghamton",
            "id": 4,
            "name": "DM-Binghamton",
            "slug": "dm-binghamton",
            "url": "https://demo.netbox.dev/api/dcim/sites/4/"
          },
          "scope_id": 4,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/17/",
          "vlan": {
            "description": "",
            "display": "Voice (200)",
            "id": 6,
            "name": "Voice",
            "url": "https://demo.netbox.dev/api/ipam/vlans/6/",
            "vid": 200
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.139.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/18/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 18,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:42.307000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.139.0/24",
          "role": {
            "description": "",
            "display": "Access - Wireless",
            "id": 3,
            "name": "Access - Wireless",
            "slug": "access-wireless",
            "url": "https://demo.netbox.dev/api/ipam/roles/3/"
          },
          "scope": {
            "description": "",
            "display": "DM-Binghamton",
            "id": 4,
            "name": "DM-Binghamton",
            "slug": "dm-binghamton",
            "url": "https://demo.netbox.dev/api/dcim/sites/4/"
          },
          "scope_id": 4,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/18/",
          "vlan": {
            "description": "",
            "display": "Wireless (300)",
            "id": 29,
            "name": "Wireless",
            "url": "https://demo.netbox.dev/api/ipam/vlans/29/",
            "vid": 300
          },
          "vrf": null
        },
        {
          "_depth": 2,
          "children": 4,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.140.0/22",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/63/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 63,
          "is_pool": false,
          "last_updated": "2020-12-30T20:19:11.154000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.140.0/22",
          "role": null,
          "scope": {
            "description": "",
            "display": "DM-Buffalo",
            "id": 5,
            "name": "DM-Buffalo",
            "slug": "dm-buffalo",
            "url": "https://demo.netbox.dev/api/dcim/sites/5/"
          },
          "scope_id": 5,
          "scope_type": "dcim.site",
          "status": {
            "label": "Container",
            "value": "container"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/63/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.140.0/28",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/19/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 19,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:42.382000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.140.0/28",
          "role": {
            "description": "",
            "display": "Management",
            "id": 4,
            "name": "Management",
            "slug": "management",
            "url": "https://demo.netbox.dev/api/ipam/roles/4/"
          },
          "scope": {
            "description": "",
            "display": "DM-Buffalo",
            "id": 5,
            "name": "DM-Buffalo",
            "slug": "dm-buffalo",
            "url": "https://demo.netbox.dev/api/dcim/sites/5/"
          },
          "scope_id": 5,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/19/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.141.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/20/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 20,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:42.467000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.141.0/24",
          "role": {
            "description": "",
            "display": "Access - Data",
            "id": 1,
            "name": "Access - Data",
            "slug": "access-data",
            "url": "https://demo.netbox.dev/api/ipam/roles/1/"
          },
          "scope": {
            "description": "",
            "display": "DM-Buffalo",
            "id": 5,
            "name": "DM-Buffalo",
            "slug": "dm-buffalo",
            "url": "https://demo.netbox.dev/api/dcim/sites/5/"
          },
          "scope_id": 5,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/20/",
          "vlan": {
            "description": "",
            "display": "Data (100)",
            "id": 7,
            "name": "Data",
            "url": "https://demo.netbox.dev/api/ipam/vlans/7/",
            "vid": 100
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.142.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/21/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 21,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:42.610000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.142.0/24",
          "role": {
            "description": "",
            "display": "Access - Voice",
            "id": 2,
            "name": "Access - Voice",
            "slug": "access-voice",
            "url": "https://demo.netbox.dev/api/ipam/roles/2/"
          },
          "scope": {
            "description": "",
            "display": "DM-Buffalo",
            "id": 5,
            "name": "DM-Buffalo",
            "slug": "dm-buffalo",
            "url": "https://demo.netbox.dev/api/dcim/sites/5/"
          },
          "scope_id": 5,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/21/",
          "vlan": {
            "description": "",
            "display": "Voice (200)",
            "id": 8,
            "name": "Voice",
            "url": "https://demo.netbox.dev/api/ipam/vlans/8/",
            "vid": 200
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.143.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/22/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 22,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:42.696000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.143.0/24",
          "role": {
            "description": "",
            "display": "Access - Wireless",
            "id": 3,
            "name": "Access - Wireless",
            "slug": "access-wireless",
            "url": "https://demo.netbox.dev/api/ipam/roles/3/"
          },
          "scope": {
            "description": "",
            "display": "DM-Buffalo",
            "id": 5,
            "name": "DM-Buffalo",
            "slug": "dm-buffalo",
            "url": "https://demo.netbox.dev/api/dcim/sites/5/"
          },
          "scope_id": 5,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/22/",
          "vlan": {
            "description": "",
            "display": "Wireless (300)",
            "id": 30,
            "name": "Wireless",
            "url": "https://demo.netbox.dev/api/ipam/vlans/30/",
            "vid": 300
          },
          "vrf": null
        },
        {
          "_depth": 2,
          "children": 4,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.144.0/22",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/64/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 64,
          "is_pool": false,
          "last_updated": "2020-12-30T20:19:11.221000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.144.0/22",
          "role": null,
          "scope": {
            "description": "",
            "display": "DM-Camden",
            "id": 6,
            "name": "DM-Camden",
            "slug": "dm-camden",
            "url": "https://demo.netbox.dev/api/dcim/sites/6/"
          },
          "scope_id": 6,
          "scope_type": "dcim.site",
          "status": {
            "label": "Container",
            "value": "container"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/64/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.144.0/28",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/23/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 23,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:42.776000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.144.0/28",
          "role": {
            "description": "",
            "display": "Management",
            "id": 4,
            "name": "Management",
            "slug": "management",
            "url": "https://demo.netbox.dev/api/ipam/roles/4/"
          },
          "scope": {
            "description": "",
            "display": "DM-Camden",
            "id": 6,
            "name": "DM-Camden",
            "slug": "dm-camden",
            "url": "https://demo.netbox.dev/api/dcim/sites/6/"
          },
          "scope_id": 6,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/23/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.145.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/24/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 24,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:42.863000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.145.0/24",
          "role": {
            "description": "",
            "display": "Access - Data",
            "id": 1,
            "name": "Access - Data",
            "slug": "access-data",
            "url": "https://demo.netbox.dev/api/ipam/roles/1/"
          },
          "scope": {
            "description": "",
            "display": "DM-Camden",
            "id": 6,
            "name": "DM-Camden",
            "slug": "dm-camden",
            "url": "https://demo.netbox.dev/api/dcim/sites/6/"
          },
          "scope_id": 6,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/24/",
          "vlan": {
            "description": "",
            "display": "Data (100)",
            "id": 9,
            "name": "Data",
            "url": "https://demo.netbox.dev/api/ipam/vlans/9/",
            "vid": 100
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.146.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/25/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 25,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:42.950000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.146.0/24",
          "role": {
            "description": "",
            "display": "Access - Voice",
            "id": 2,
            "name": "Access - Voice",
            "slug": "access-voice",
            "url": "https://demo.netbox.dev/api/ipam/roles/2/"
          },
          "scope": {
            "description": "",
            "display": "DM-Camden",
            "id": 6,
            "name": "DM-Camden",
            "slug": "dm-camden",
            "url": "https://demo.netbox.dev/api/dcim/sites/6/"
          },
          "scope_id": 6,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/25/",
          "vlan": {
            "description": "",
            "display": "Voice (200)",
            "id": 10,
            "name": "Voice",
            "url": "https://demo.netbox.dev/api/ipam/vlans/10/",
            "vid": 200
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.147.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/26/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 26,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:43.037000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.147.0/24",
          "role": {
            "description": "",
            "display": "Access - Wireless",
            "id": 3,
            "name": "Access - Wireless",
            "slug": "access-wireless",
            "url": "https://demo.netbox.dev/api/ipam/roles/3/"
          },
          "scope": {
            "description": "",
            "display": "DM-Camden",
            "id": 6,
            "name": "DM-Camden",
            "slug": "dm-camden",
            "url": "https://demo.netbox.dev/api/dcim/sites/6/"
          },
          "scope_id": 6,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/26/",
          "vlan": {
            "description": "",
            "display": "Wireless (300)",
            "id": 31,
            "name": "Wireless",
            "url": "https://demo.netbox.dev/api/ipam/vlans/31/",
            "vid": 300
          },
          "vrf": null
        },
        {
          "_depth": 2,
          "children": 4,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.148.0/22",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/65/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 65,
          "is_pool": false,
          "last_updated": "2020-12-30T20:19:11.288000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.148.0/22",
          "role": null,
          "scope": {
            "description": "",
            "display": "DM-Nashua",
            "id": 7,
            "name": "DM-Nashua",
            "slug": "dm-nashua",
            "url": "https://demo.netbox.dev/api/dcim/sites/7/"
          },
          "scope_id": 7,
          "scope_type": "dcim.site",
          "status": {
            "label": "Container",
            "value": "container"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/65/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.148.0/28",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/27/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 27,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:43.111000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.148.0/28",
          "role": {
            "description": "",
            "display": "Management",
            "id": 4,
            "name": "Management",
            "slug": "management",
            "url": "https://demo.netbox.dev/api/ipam/roles/4/"
          },
          "scope": {
            "description": "",
            "display": "DM-Nashua",
            "id": 7,
            "name": "DM-Nashua",
            "slug": "dm-nashua",
            "url": "https://demo.netbox.dev/api/dcim/sites/7/"
          },
          "scope_id": 7,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/27/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.149.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/28/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 28,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:43.196000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.149.0/24",
          "role": {
            "description": "",
            "display": "Access - Data",
            "id": 1,
            "name": "Access - Data",
            "slug": "access-data",
            "url": "https://demo.netbox.dev/api/ipam/roles/1/"
          },
          "scope": {
            "description": "",
            "display": "DM-Nashua",
            "id": 7,
            "name": "DM-Nashua",
            "slug": "dm-nashua",
            "url": "https://demo.netbox.dev/api/dcim/sites/7/"
          },
          "scope_id": 7,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/28/",
          "vlan": {
            "description": "",
            "display": "Data (100)",
            "id": 11,
            "name": "Data",
            "url": "https://demo.netbox.dev/api/ipam/vlans/11/",
            "vid": 100
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.150.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/29/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 29,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:43.282000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.150.0/24",
          "role": {
            "description": "",
            "display": "Access - Voice",
            "id": 2,
            "name": "Access - Voice",
            "slug": "access-voice",
            "url": "https://demo.netbox.dev/api/ipam/roles/2/"
          },
          "scope": {
            "description": "",
            "display": "DM-Nashua",
            "id": 7,
            "name": "DM-Nashua",
            "slug": "dm-nashua",
            "url": "https://demo.netbox.dev/api/dcim/sites/7/"
          },
          "scope_id": 7,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/29/",
          "vlan": {
            "description": "",
            "display": "Voice (200)",
            "id": 12,
            "name": "Voice",
            "url": "https://demo.netbox.dev/api/ipam/vlans/12/",
            "vid": 200
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.151.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/30/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 30,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:43.368000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.151.0/24",
          "role": {
            "description": "",
            "display": "Access - Wireless",
            "id": 3,
            "name": "Access - Wireless",
            "slug": "access-wireless",
            "url": "https://demo.netbox.dev/api/ipam/roles/3/"
          },
          "scope": {
            "description": "",
            "display": "DM-Nashua",
            "id": 7,
            "name": "DM-Nashua",
            "slug": "dm-nashua",
            "url": "https://demo.netbox.dev/api/dcim/sites/7/"
          },
          "scope_id": 7,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/30/",
          "vlan": {
            "description": "",
            "display": "Wireless (300)",
            "id": 32,
            "name": "Wireless",
            "url": "https://demo.netbox.dev/api/ipam/vlans/32/",
            "vid": 300
          },
          "vrf": null
        },
        {
          "_depth": 2,
          "children": 4,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.152.0/22",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/66/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 66,
          "is_pool": false,
          "last_updated": "2020-12-30T20:19:11.355000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.152.0/22",
          "role": null,
          "scope": {
            "description": "",
            "display": "DM-Pittsfield",
            "id": 8,
            "name": "DM-Pittsfield",
            "slug": "dm-pittsfield",
            "url": "https://demo.netbox.dev/api/dcim/sites/8/"
          },
          "scope_id": 8,
          "scope_type": "dcim.site",
          "status": {
            "label": "Container",
            "value": "container"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/66/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.152.0/28",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/31/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 31,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:43.441000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.152.0/28",
          "role": {
            "description": "",
            "display": "Management",
            "id": 4,
            "name": "Management",
            "slug": "management",
            "url": "https://demo.netbox.dev/api/ipam/roles/4/"
          },
          "scope": {
            "description": "",
            "display": "DM-Pittsfield",
            "id": 8,
            "name": "DM-Pittsfield",
            "slug": "dm-pittsfield",
            "url": "https://demo.netbox.dev/api/dcim/sites/8/"
          },
          "scope_id": 8,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/31/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.153.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/32/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 32,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:43.527000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.153.0/24",
          "role": {
            "description": "",
            "display": "Access - Data",
            "id": 1,
            "name": "Access - Data",
            "slug": "access-data",
            "url": "https://demo.netbox.dev/api/ipam/roles/1/"
          },
          "scope": {
            "description": "",
            "display": "DM-Pittsfield",
            "id": 8,
            "name": "DM-Pittsfield",
            "slug": "dm-pittsfield",
            "url": "https://demo.netbox.dev/api/dcim/sites/8/"
          },
          "scope_id": 8,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/32/",
          "vlan": {
            "description": "",
            "display": "Data (100)",
            "id": 13,
            "name": "Data",
            "url": "https://demo.netbox.dev/api/ipam/vlans/13/",
            "vid": 100
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.154.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/33/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 33,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:43.637000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.154.0/24",
          "role": {
            "description": "",
            "display": "Access - Voice",
            "id": 2,
            "name": "Access - Voice",
            "slug": "access-voice",
            "url": "https://demo.netbox.dev/api/ipam/roles/2/"
          },
          "scope": {
            "description": "",
            "display": "DM-Pittsfield",
            "id": 8,
            "name": "DM-Pittsfield",
            "slug": "dm-pittsfield",
            "url": "https://demo.netbox.dev/api/dcim/sites/8/"
          },
          "scope_id": 8,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/33/",
          "vlan": {
            "description": "",
            "display": "Voice (200)",
            "id": 14,
            "name": "Voice",
            "url": "https://demo.netbox.dev/api/ipam/vlans/14/",
            "vid": 200
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.155.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/34/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 34,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:43.760000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.155.0/24",
          "role": {
            "description": "",
            "display": "Access - Wireless",
            "id": 3,
            "name": "Access - Wireless",
            "slug": "access-wireless",
            "url": "https://demo.netbox.dev/api/ipam/roles/3/"
          },
          "scope": {
            "description": "",
            "display": "DM-Pittsfield",
            "id": 8,
            "name": "DM-Pittsfield",
            "slug": "dm-pittsfield",
            "url": "https://demo.netbox.dev/api/dcim/sites/8/"
          },
          "scope_id": 8,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/34/",
          "vlan": {
            "description": "",
            "display": "Wireless (300)",
            "id": 33,
            "name": "Wireless",
            "url": "https://demo.netbox.dev/api/ipam/vlans/33/",
            "vid": 300
          },
          "vrf": null
        },
        {
          "_depth": 2,
          "children": 4,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.156.0/22",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/67/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 67,
          "is_pool": false,
          "last_updated": "2020-12-30T20:19:11.419000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.156.0/22",
          "role": null,
          "scope": {
            "description": "",
            "display": "DM-Rochester",
            "id": 9,
            "name": "DM-Rochester",
            "slug": "dm-rochester",
            "url": "https://demo.netbox.dev/api/dcim/sites/9/"
          },
          "scope_id": 9,
          "scope_type": "dcim.site",
          "status": {
            "label": "Container",
            "value": "container"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/67/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.156.0/28",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/35/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 35,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:43.834000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.156.0/28",
          "role": {
            "description": "",
            "display": "Management",
            "id": 4,
            "name": "Management",
            "slug": "management",
            "url": "https://demo.netbox.dev/api/ipam/roles/4/"
          },
          "scope": {
            "description": "",
            "display": "DM-Rochester",
            "id": 9,
            "name": "DM-Rochester",
            "slug": "dm-rochester",
            "url": "https://demo.netbox.dev/api/dcim/sites/9/"
          },
          "scope_id": 9,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/35/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.157.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/36/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 36,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:43.926000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.157.0/24",
          "role": {
            "description": "",
            "display": "Access - Data",
            "id": 1,
            "name": "Access - Data",
            "slug": "access-data",
            "url": "https://demo.netbox.dev/api/ipam/roles/1/"
          },
          "scope": {
            "description": "",
            "display": "DM-Rochester",
            "id": 9,
            "name": "DM-Rochester",
            "slug": "dm-rochester",
            "url": "https://demo.netbox.dev/api/dcim/sites/9/"
          },
          "scope_id": 9,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/36/",
          "vlan": {
            "description": "",
            "display": "Data (100)",
            "id": 15,
            "name": "Data",
            "url": "https://demo.netbox.dev/api/ipam/vlans/15/",
            "vid": 100
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.158.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/37/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 37,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:44.013000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.158.0/24",
          "role": {
            "description": "",
            "display": "Access - Voice",
            "id": 2,
            "name": "Access - Voice",
            "slug": "access-voice",
            "url": "https://demo.netbox.dev/api/ipam/roles/2/"
          },
          "scope": {
            "description": "",
            "display": "DM-Rochester",
            "id": 9,
            "name": "DM-Rochester",
            "slug": "dm-rochester",
            "url": "https://demo.netbox.dev/api/dcim/sites/9/"
          },
          "scope_id": 9,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/37/",
          "vlan": {
            "description": "",
            "display": "Voice (200)",
            "id": 16,
            "name": "Voice",
            "url": "https://demo.netbox.dev/api/ipam/vlans/16/",
            "vid": 200
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.159.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/38/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 38,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:44.099000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.159.0/24",
          "role": {
            "description": "",
            "display": "Access - Wireless",
            "id": 3,
            "name": "Access - Wireless",
            "slug": "access-wireless",
            "url": "https://demo.netbox.dev/api/ipam/roles/3/"
          },
          "scope": {
            "description": "",
            "display": "DM-Rochester",
            "id": 9,
            "name": "DM-Rochester",
            "slug": "dm-rochester",
            "url": "https://demo.netbox.dev/api/dcim/sites/9/"
          },
          "scope_id": 9,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/38/",
          "vlan": {
            "description": "",
            "display": "Wireless (300)",
            "id": 34,
            "name": "Wireless",
            "url": "https://demo.netbox.dev/api/ipam/vlans/34/",
            "vid": 300
          },
          "vrf": null
        },
        {
          "_depth": 2,
          "children": 4,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.160.0/22",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/68/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 68,
          "is_pool": false,
          "last_updated": "2020-12-30T20:19:11.481000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.160.0/22",
          "role": null,
          "scope": {
            "description": "",
            "display": "DM-Scranton",
            "id": 10,
            "name": "DM-Scranton",
            "slug": "dm-scranton",
            "url": "https://demo.netbox.dev/api/dcim/sites/10/"
          },
          "scope_id": 10,
          "scope_type": "dcim.site",
          "status": {
            "label": "Container",
            "value": "container"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/68/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.160.0/28",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/39/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 39,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:44.173000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.160.0/28",
          "role": {
            "description": "",
            "display": "Management",
            "id": 4,
            "name": "Management",
            "slug": "management",
            "url": "https://demo.netbox.dev/api/ipam/roles/4/"
          },
          "scope": {
            "description": "",
            "display": "DM-Scranton",
            "id": 10,
            "name": "DM-Scranton",
            "slug": "dm-scranton",
            "url": "https://demo.netbox.dev/api/dcim/sites/10/"
          },
          "scope_id": 10,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/39/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.161.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/40/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 40,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:44.259000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.161.0/24",
          "role": {
            "description": "",
            "display": "Access - Data",
            "id": 1,
            "name": "Access - Data",
            "slug": "access-data",
            "url": "https://demo.netbox.dev/api/ipam/roles/1/"
          },
          "scope": {
            "description": "",
            "display": "DM-Scranton",
            "id": 10,
            "name": "DM-Scranton",
            "slug": "dm-scranton",
            "url": "https://demo.netbox.dev/api/dcim/sites/10/"
          },
          "scope_id": 10,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/40/",
          "vlan": {
            "description": "",
            "display": "Data (100)",
            "id": 17,
            "name": "Data",
            "url": "https://demo.netbox.dev/api/ipam/vlans/17/",
            "vid": 100
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.162.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/41/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 41,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:44.345000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.162.0/24",
          "role": {
            "description": "",
            "display": "Access - Voice",
            "id": 2,
            "name": "Access - Voice",
            "slug": "access-voice",
            "url": "https://demo.netbox.dev/api/ipam/roles/2/"
          },
          "scope": {
            "description": "",
            "display": "DM-Scranton",
            "id": 10,
            "name": "DM-Scranton",
            "slug": "dm-scranton",
            "url": "https://demo.netbox.dev/api/dcim/sites/10/"
          },
          "scope_id": 10,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/41/",
          "vlan": {
            "description": "",
            "display": "Voice (200)",
            "id": 18,
            "name": "Voice",
            "url": "https://demo.netbox.dev/api/ipam/vlans/18/",
            "vid": 200
          },
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.163.0/24",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/42/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 42,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:44.431000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.163.0/24",
          "role": {
            "description": "",
            "display": "Access - Wireless",
            "id": 3,
            "name": "Access - Wireless",
            "slug": "access-wireless",
            "url": "https://demo.netbox.dev/api/ipam/roles/3/"
          },
          "scope": {
            "description": "",
            "display": "DM-Scranton",
            "id": 10,
            "name": "DM-Scranton",
            "slug": "dm-scranton",
            "url": "https://demo.netbox.dev/api/dcim/sites/10/"
          },
          "scope_id": 10,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/42/",
          "vlan": {
            "description": "",
            "display": "Wireless (300)",
            "id": 35,
            "name": "Wireless",
            "url": "https://demo.netbox.dev/api/ipam/vlans/35/",
            "vid": 300
          },
          "vrf": null
        },
        {
          "_depth": 2,
          "children": 4,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.164.0/22",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/69/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 69,
          "is_pool": false,
          "last_updated": "2020-12-30T20:19:11.543000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.164.0/22",
          "role": null,
          "scope": {
            "description": "",
            "display": "DM-Stamford",
            "id": 11,
            "name": "DM-Stamford",
            "slug": "dm-stamford",
            "url": "https://demo.netbox.dev/api/dcim/sites/11/"
          },
          "scope_id": 11,
          "scope_type": "dcim.site",
          "status": {
            "label": "Container",
            "value": "container"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/69/",
          "vlan": null,
          "vrf": null
        },
        {
          "_depth": 3,
          "children": 0,
          "comments": "",
          "created": "2020-12-30T00:00:00Z",
          "custom_fields": {
            "cluster": null
          },
          "description": "",
          "display": "10.112.164.0/28",
          "display_url": "https://demo.netbox.dev/ipam/prefixes/43/",
          "family": {
            "label": "IPv4",
            "value": 4
          },
          "id": 43,
          "is_pool": false,
          "last_updated": "2020-12-30T20:13:44.504000Z",
          "mark_utilized": false,
          "owner": null,
          "prefix": "10.112.164.0/28",
          "role": {
            "description": "",
            "display": "Management",
            "id": 4,
            "name": "Management",
            "slug": "management",
            "url": "https://demo.netbox.dev/api/ipam/roles/4/"
          },
          "scope": {
            "description": "",
            "display": "DM-Stamford",
            "id": 11,
            "name": "DM-Stamford",
            "slug": "dm-stamford",
            "url": "https://demo.netbox.dev/api/dcim/sites/11/"
          },
          "scope_id": 11,
          "scope_type": "dcim.site",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "url": "https://demo.netbox.dev/api/ipam/prefixes/43/",
          "vlan": null,
          "vrf": null
        }
      ]
    }
    ```

=== ":material-file-document-outline: YAML Output"

    ```yaml
    count: 93
    next: https://demo.netbox.dev/api/ipam/prefixes/?limit=50&offset=50
    previous: null
    results:
    - _depth: 0
      children: 67
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.0.0/15
      display_url: https://demo.netbox.dev/ipam/prefixes/1/
      family:
        label: IPv4
        value: 4
      id: 1
      is_pool: false
      last_updated: '2020-12-30T20:00:17.126000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.0.0/15
      role: null
      scope: null
      scope_id: null
      scope_type: null
      status:
        label: Container
        value: container
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/1/
      vlan: null
      vrf: null
    - _depth: 1
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: DM HQ
      display: 10.112.0.0/17
      display_url: https://demo.netbox.dev/ipam/prefixes/2/
      family:
        label: IPv4
        value: 4
      id: 2
      is_pool: false
      last_updated: '2020-12-30T20:00:02.450000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.0.0/17
      role: null
      scope: null
      scope_id: null
      scope_type: null
      status:
        label: Container
        value: container
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/2/
      vlan: null
      vrf: null
    - _depth: 1
      children: 65
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: DM branch offices
      display: 10.112.128.0/17
      display_url: https://demo.netbox.dev/ipam/prefixes/3/
      family:
        label: IPv4
        value: 4
      id: 3
      is_pool: false
      last_updated: '2020-12-30T20:01:26.618000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.128.0/17
      role: null
      scope: null
      scope_id: null
      scope_type: null
      status:
        label: Container
        value: container
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/3/
      vlan: null
      vrf: null
    - _depth: 2
      children: 4
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.128.0/22
      display_url: https://demo.netbox.dev/ipam/prefixes/60/
      family:
        label: IPv4
        value: 4
      id: 60
      is_pool: false
      last_updated: '2020-12-30T20:19:10.958000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.128.0/22
      role: null
      scope:
        description: ''
        display: DM-Akron
        id: 2
        name: DM-Akron
        slug: dm-akron
        url: https://demo.netbox.dev/api/dcim/sites/2/
      scope_id: 2
      scope_type: dcim.site
      status:
        label: Container
        value: container
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/60/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.128.0/28
      display_url: https://demo.netbox.dev/ipam/prefixes/7/
      family:
        label: IPv4
        value: 4
      id: 7
      is_pool: false
      last_updated: '2020-12-30T20:13:41.316000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.128.0/28
      role:
        description: ''
        display: Management
        id: 4
        name: Management
        slug: management
        url: https://demo.netbox.dev/api/ipam/roles/4/
      scope:
        description: ''
        display: DM-Akron
        id: 2
        name: DM-Akron
        slug: dm-akron
        url: https://demo.netbox.dev/api/dcim/sites/2/
      scope_id: 2
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/7/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.129.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/8/
      family:
        label: IPv4
        value: 4
      id: 8
      is_pool: false
      last_updated: '2020-12-30T20:13:41.429000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.129.0/24
      role:
        description: ''
        display: Access - Data
        id: 1
        name: Access - Data
        slug: access-data
        url: https://demo.netbox.dev/api/ipam/roles/1/
      scope:
        description: ''
        display: DM-Akron
        id: 2
        name: DM-Akron
        slug: dm-akron
        url: https://demo.netbox.dev/api/dcim/sites/2/
      scope_id: 2
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/8/
      vlan:
        description: ''
        display: Data (100)
        id: 1
        name: Data
        url: https://demo.netbox.dev/api/ipam/vlans/1/
        vid: 100
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.130.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/9/
      family:
        label: IPv4
        value: 4
      id: 9
      is_pool: false
      last_updated: '2020-12-30T20:13:41.551000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.130.0/24
      role:
        description: ''
        display: Access - Voice
        id: 2
        name: Access - Voice
        slug: access-voice
        url: https://demo.netbox.dev/api/ipam/roles/2/
      scope:
        description: ''
        display: DM-Akron
        id: 2
        name: DM-Akron
        slug: dm-akron
        url: https://demo.netbox.dev/api/dcim/sites/2/
      scope_id: 2
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/9/
      vlan:
        description: ''
        display: Voice (200)
        id: 2
        name: Voice
        url: https://demo.netbox.dev/api/ipam/vlans/2/
        vid: 200
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.131.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/10/
      family:
        label: IPv4
        value: 4
      id: 10
      is_pool: false
      last_updated: '2020-12-30T20:13:41.639000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.131.0/24
      role:
        description: ''
        display: Access - Wireless
        id: 3
        name: Access - Wireless
        slug: access-wireless
        url: https://demo.netbox.dev/api/ipam/roles/3/
      scope:
        description: ''
        display: DM-Akron
        id: 2
        name: DM-Akron
        slug: dm-akron
        url: https://demo.netbox.dev/api/dcim/sites/2/
      scope_id: 2
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/10/
      vlan:
        description: ''
        display: Wireless (300)
        id: 27
        name: Wireless
        url: https://demo.netbox.dev/api/ipam/vlans/27/
        vid: 300
      vrf: null
    - _depth: 2
      children: 4
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.132.0/22
      display_url: https://demo.netbox.dev/ipam/prefixes/61/
      family:
        label: IPv4
        value: 4
      id: 61
      is_pool: false
      last_updated: '2020-12-30T20:19:11.024000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.132.0/22
      role: null
      scope:
        description: ''
        display: DM-Albany
        id: 3
        name: DM-Albany
        slug: dm-albany
        url: https://demo.netbox.dev/api/dcim/sites/3/
      scope_id: 3
      scope_type: dcim.site
      status:
        label: Container
        value: container
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/61/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.132.0/28
      display_url: https://demo.netbox.dev/ipam/prefixes/11/
      family:
        label: IPv4
        value: 4
      id: 11
      is_pool: false
      last_updated: '2020-12-30T20:13:41.714000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.132.0/28
      role:
        description: ''
        display: Management
        id: 4
        name: Management
        slug: management
        url: https://demo.netbox.dev/api/ipam/roles/4/
      scope:
        description: ''
        display: DM-Albany
        id: 3
        name: DM-Albany
        slug: dm-albany
        url: https://demo.netbox.dev/api/dcim/sites/3/
      scope_id: 3
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/11/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.133.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/12/
      family:
        label: IPv4
        value: 4
      id: 12
      is_pool: false
      last_updated: '2020-12-30T20:13:41.801000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.133.0/24
      role:
        description: ''
        display: Access - Data
        id: 1
        name: Access - Data
        slug: access-data
        url: https://demo.netbox.dev/api/ipam/roles/1/
      scope:
        description: ''
        display: DM-Albany
        id: 3
        name: DM-Albany
        slug: dm-albany
        url: https://demo.netbox.dev/api/dcim/sites/3/
      scope_id: 3
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/12/
      vlan:
        description: ''
        display: Data (100)
        id: 3
        name: Data
        url: https://demo.netbox.dev/api/ipam/vlans/3/
        vid: 100
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.134.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/13/
      family:
        label: IPv4
        value: 4
      id: 13
      is_pool: false
      last_updated: '2020-12-30T20:13:41.891000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.134.0/24
      role:
        description: ''
        display: Access - Voice
        id: 2
        name: Access - Voice
        slug: access-voice
        url: https://demo.netbox.dev/api/ipam/roles/2/
      scope:
        description: ''
        display: DM-Albany
        id: 3
        name: DM-Albany
        slug: dm-albany
        url: https://demo.netbox.dev/api/dcim/sites/3/
      scope_id: 3
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/13/
      vlan:
        description: ''
        display: Voice (200)
        id: 4
        name: Voice
        url: https://demo.netbox.dev/api/ipam/vlans/4/
        vid: 200
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.135.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/14/
      family:
        label: IPv4
        value: 4
      id: 14
      is_pool: false
      last_updated: '2020-12-30T20:13:41.975000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.135.0/24
      role:
        description: ''
        display: Access - Wireless
        id: 3
        name: Access - Wireless
        slug: access-wireless
        url: https://demo.netbox.dev/api/ipam/roles/3/
      scope:
        description: ''
        display: DM-Albany
        id: 3
        name: DM-Albany
        slug: dm-albany
        url: https://demo.netbox.dev/api/dcim/sites/3/
      scope_id: 3
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/14/
      vlan:
        description: ''
        display: Wireless (300)
        id: 28
        name: Wireless
        url: https://demo.netbox.dev/api/ipam/vlans/28/
        vid: 300
      vrf: null
    - _depth: 2
      children: 4
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.136.0/22
      display_url: https://demo.netbox.dev/ipam/prefixes/62/
      family:
        label: IPv4
        value: 4
      id: 62
      is_pool: false
      last_updated: '2020-12-30T20:19:11.089000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.136.0/22
      role: null
      scope:
        description: ''
        display: DM-Binghamton
        id: 4
        name: DM-Binghamton
        slug: dm-binghamton
        url: https://demo.netbox.dev/api/dcim/sites/4/
      scope_id: 4
      scope_type: dcim.site
      status:
        label: Container
        value: container
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/62/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.136.0/28
      display_url: https://demo.netbox.dev/ipam/prefixes/15/
      family:
        label: IPv4
        value: 4
      id: 15
      is_pool: false
      last_updated: '2020-12-30T20:13:42.049000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.136.0/28
      role:
        description: ''
        display: Management
        id: 4
        name: Management
        slug: management
        url: https://demo.netbox.dev/api/ipam/roles/4/
      scope:
        description: ''
        display: DM-Binghamton
        id: 4
        name: DM-Binghamton
        slug: dm-binghamton
        url: https://demo.netbox.dev/api/dcim/sites/4/
      scope_id: 4
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/15/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.137.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/16/
      family:
        label: IPv4
        value: 4
      id: 16
      is_pool: false
      last_updated: '2020-12-30T20:13:42.134000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.137.0/24
      role:
        description: ''
        display: Access - Data
        id: 1
        name: Access - Data
        slug: access-data
        url: https://demo.netbox.dev/api/ipam/roles/1/
      scope:
        description: ''
        display: DM-Binghamton
        id: 4
        name: DM-Binghamton
        slug: dm-binghamton
        url: https://demo.netbox.dev/api/dcim/sites/4/
      scope_id: 4
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/16/
      vlan:
        description: ''
        display: Data (100)
        id: 5
        name: Data
        url: https://demo.netbox.dev/api/ipam/vlans/5/
        vid: 100
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.138.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/17/
      family:
        label: IPv4
        value: 4
      id: 17
      is_pool: false
      last_updated: '2020-12-30T20:13:42.220000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.138.0/24
      role:
        description: ''
        display: Access - Voice
        id: 2
        name: Access - Voice
        slug: access-voice
        url: https://demo.netbox.dev/api/ipam/roles/2/
      scope:
        description: ''
        display: DM-Binghamton
        id: 4
        name: DM-Binghamton
        slug: dm-binghamton
        url: https://demo.netbox.dev/api/dcim/sites/4/
      scope_id: 4
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/17/
      vlan:
        description: ''
        display: Voice (200)
        id: 6
        name: Voice
        url: https://demo.netbox.dev/api/ipam/vlans/6/
        vid: 200
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.139.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/18/
      family:
        label: IPv4
        value: 4
      id: 18
      is_pool: false
      last_updated: '2020-12-30T20:13:42.307000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.139.0/24
      role:
        description: ''
        display: Access - Wireless
        id: 3
        name: Access - Wireless
        slug: access-wireless
        url: https://demo.netbox.dev/api/ipam/roles/3/
      scope:
        description: ''
        display: DM-Binghamton
        id: 4
        name: DM-Binghamton
        slug: dm-binghamton
        url: https://demo.netbox.dev/api/dcim/sites/4/
      scope_id: 4
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/18/
      vlan:
        description: ''
        display: Wireless (300)
        id: 29
        name: Wireless
        url: https://demo.netbox.dev/api/ipam/vlans/29/
        vid: 300
      vrf: null
    - _depth: 2
      children: 4
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.140.0/22
      display_url: https://demo.netbox.dev/ipam/prefixes/63/
      family:
        label: IPv4
        value: 4
      id: 63
      is_pool: false
      last_updated: '2020-12-30T20:19:11.154000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.140.0/22
      role: null
      scope:
        description: ''
        display: DM-Buffalo
        id: 5
        name: DM-Buffalo
        slug: dm-buffalo
        url: https://demo.netbox.dev/api/dcim/sites/5/
      scope_id: 5
      scope_type: dcim.site
      status:
        label: Container
        value: container
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/63/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.140.0/28
      display_url: https://demo.netbox.dev/ipam/prefixes/19/
      family:
        label: IPv4
        value: 4
      id: 19
      is_pool: false
      last_updated: '2020-12-30T20:13:42.382000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.140.0/28
      role:
        description: ''
        display: Management
        id: 4
        name: Management
        slug: management
        url: https://demo.netbox.dev/api/ipam/roles/4/
      scope:
        description: ''
        display: DM-Buffalo
        id: 5
        name: DM-Buffalo
        slug: dm-buffalo
        url: https://demo.netbox.dev/api/dcim/sites/5/
      scope_id: 5
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/19/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.141.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/20/
      family:
        label: IPv4
        value: 4
      id: 20
      is_pool: false
      last_updated: '2020-12-30T20:13:42.467000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.141.0/24
      role:
        description: ''
        display: Access - Data
        id: 1
        name: Access - Data
        slug: access-data
        url: https://demo.netbox.dev/api/ipam/roles/1/
      scope:
        description: ''
        display: DM-Buffalo
        id: 5
        name: DM-Buffalo
        slug: dm-buffalo
        url: https://demo.netbox.dev/api/dcim/sites/5/
      scope_id: 5
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/20/
      vlan:
        description: ''
        display: Data (100)
        id: 7
        name: Data
        url: https://demo.netbox.dev/api/ipam/vlans/7/
        vid: 100
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.142.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/21/
      family:
        label: IPv4
        value: 4
      id: 21
      is_pool: false
      last_updated: '2020-12-30T20:13:42.610000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.142.0/24
      role:
        description: ''
        display: Access - Voice
        id: 2
        name: Access - Voice
        slug: access-voice
        url: https://demo.netbox.dev/api/ipam/roles/2/
      scope:
        description: ''
        display: DM-Buffalo
        id: 5
        name: DM-Buffalo
        slug: dm-buffalo
        url: https://demo.netbox.dev/api/dcim/sites/5/
      scope_id: 5
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/21/
      vlan:
        description: ''
        display: Voice (200)
        id: 8
        name: Voice
        url: https://demo.netbox.dev/api/ipam/vlans/8/
        vid: 200
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.143.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/22/
      family:
        label: IPv4
        value: 4
      id: 22
      is_pool: false
      last_updated: '2020-12-30T20:13:42.696000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.143.0/24
      role:
        description: ''
        display: Access - Wireless
        id: 3
        name: Access - Wireless
        slug: access-wireless
        url: https://demo.netbox.dev/api/ipam/roles/3/
      scope:
        description: ''
        display: DM-Buffalo
        id: 5
        name: DM-Buffalo
        slug: dm-buffalo
        url: https://demo.netbox.dev/api/dcim/sites/5/
      scope_id: 5
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/22/
      vlan:
        description: ''
        display: Wireless (300)
        id: 30
        name: Wireless
        url: https://demo.netbox.dev/api/ipam/vlans/30/
        vid: 300
      vrf: null
    - _depth: 2
      children: 4
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.144.0/22
      display_url: https://demo.netbox.dev/ipam/prefixes/64/
      family:
        label: IPv4
        value: 4
      id: 64
      is_pool: false
      last_updated: '2020-12-30T20:19:11.221000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.144.0/22
      role: null
      scope:
        description: ''
        display: DM-Camden
        id: 6
        name: DM-Camden
        slug: dm-camden
        url: https://demo.netbox.dev/api/dcim/sites/6/
      scope_id: 6
      scope_type: dcim.site
      status:
        label: Container
        value: container
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/64/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.144.0/28
      display_url: https://demo.netbox.dev/ipam/prefixes/23/
      family:
        label: IPv4
        value: 4
      id: 23
      is_pool: false
      last_updated: '2020-12-30T20:13:42.776000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.144.0/28
      role:
        description: ''
        display: Management
        id: 4
        name: Management
        slug: management
        url: https://demo.netbox.dev/api/ipam/roles/4/
      scope:
        description: ''
        display: DM-Camden
        id: 6
        name: DM-Camden
        slug: dm-camden
        url: https://demo.netbox.dev/api/dcim/sites/6/
      scope_id: 6
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/23/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.145.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/24/
      family:
        label: IPv4
        value: 4
      id: 24
      is_pool: false
      last_updated: '2020-12-30T20:13:42.863000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.145.0/24
      role:
        description: ''
        display: Access - Data
        id: 1
        name: Access - Data
        slug: access-data
        url: https://demo.netbox.dev/api/ipam/roles/1/
      scope:
        description: ''
        display: DM-Camden
        id: 6
        name: DM-Camden
        slug: dm-camden
        url: https://demo.netbox.dev/api/dcim/sites/6/
      scope_id: 6
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/24/
      vlan:
        description: ''
        display: Data (100)
        id: 9
        name: Data
        url: https://demo.netbox.dev/api/ipam/vlans/9/
        vid: 100
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.146.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/25/
      family:
        label: IPv4
        value: 4
      id: 25
      is_pool: false
      last_updated: '2020-12-30T20:13:42.950000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.146.0/24
      role:
        description: ''
        display: Access - Voice
        id: 2
        name: Access - Voice
        slug: access-voice
        url: https://demo.netbox.dev/api/ipam/roles/2/
      scope:
        description: ''
        display: DM-Camden
        id: 6
        name: DM-Camden
        slug: dm-camden
        url: https://demo.netbox.dev/api/dcim/sites/6/
      scope_id: 6
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/25/
      vlan:
        description: ''
        display: Voice (200)
        id: 10
        name: Voice
        url: https://demo.netbox.dev/api/ipam/vlans/10/
        vid: 200
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.147.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/26/
      family:
        label: IPv4
        value: 4
      id: 26
      is_pool: false
      last_updated: '2020-12-30T20:13:43.037000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.147.0/24
      role:
        description: ''
        display: Access - Wireless
        id: 3
        name: Access - Wireless
        slug: access-wireless
        url: https://demo.netbox.dev/api/ipam/roles/3/
      scope:
        description: ''
        display: DM-Camden
        id: 6
        name: DM-Camden
        slug: dm-camden
        url: https://demo.netbox.dev/api/dcim/sites/6/
      scope_id: 6
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/26/
      vlan:
        description: ''
        display: Wireless (300)
        id: 31
        name: Wireless
        url: https://demo.netbox.dev/api/ipam/vlans/31/
        vid: 300
      vrf: null
    - _depth: 2
      children: 4
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.148.0/22
      display_url: https://demo.netbox.dev/ipam/prefixes/65/
      family:
        label: IPv4
        value: 4
      id: 65
      is_pool: false
      last_updated: '2020-12-30T20:19:11.288000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.148.0/22
      role: null
      scope:
        description: ''
        display: DM-Nashua
        id: 7
        name: DM-Nashua
        slug: dm-nashua
        url: https://demo.netbox.dev/api/dcim/sites/7/
      scope_id: 7
      scope_type: dcim.site
      status:
        label: Container
        value: container
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/65/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.148.0/28
      display_url: https://demo.netbox.dev/ipam/prefixes/27/
      family:
        label: IPv4
        value: 4
      id: 27
      is_pool: false
      last_updated: '2020-12-30T20:13:43.111000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.148.0/28
      role:
        description: ''
        display: Management
        id: 4
        name: Management
        slug: management
        url: https://demo.netbox.dev/api/ipam/roles/4/
      scope:
        description: ''
        display: DM-Nashua
        id: 7
        name: DM-Nashua
        slug: dm-nashua
        url: https://demo.netbox.dev/api/dcim/sites/7/
      scope_id: 7
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/27/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.149.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/28/
      family:
        label: IPv4
        value: 4
      id: 28
      is_pool: false
      last_updated: '2020-12-30T20:13:43.196000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.149.0/24
      role:
        description: ''
        display: Access - Data
        id: 1
        name: Access - Data
        slug: access-data
        url: https://demo.netbox.dev/api/ipam/roles/1/
      scope:
        description: ''
        display: DM-Nashua
        id: 7
        name: DM-Nashua
        slug: dm-nashua
        url: https://demo.netbox.dev/api/dcim/sites/7/
      scope_id: 7
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/28/
      vlan:
        description: ''
        display: Data (100)
        id: 11
        name: Data
        url: https://demo.netbox.dev/api/ipam/vlans/11/
        vid: 100
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.150.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/29/
      family:
        label: IPv4
        value: 4
      id: 29
      is_pool: false
      last_updated: '2020-12-30T20:13:43.282000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.150.0/24
      role:
        description: ''
        display: Access - Voice
        id: 2
        name: Access - Voice
        slug: access-voice
        url: https://demo.netbox.dev/api/ipam/roles/2/
      scope:
        description: ''
        display: DM-Nashua
        id: 7
        name: DM-Nashua
        slug: dm-nashua
        url: https://demo.netbox.dev/api/dcim/sites/7/
      scope_id: 7
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/29/
      vlan:
        description: ''
        display: Voice (200)
        id: 12
        name: Voice
        url: https://demo.netbox.dev/api/ipam/vlans/12/
        vid: 200
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.151.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/30/
      family:
        label: IPv4
        value: 4
      id: 30
      is_pool: false
      last_updated: '2020-12-30T20:13:43.368000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.151.0/24
      role:
        description: ''
        display: Access - Wireless
        id: 3
        name: Access - Wireless
        slug: access-wireless
        url: https://demo.netbox.dev/api/ipam/roles/3/
      scope:
        description: ''
        display: DM-Nashua
        id: 7
        name: DM-Nashua
        slug: dm-nashua
        url: https://demo.netbox.dev/api/dcim/sites/7/
      scope_id: 7
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/30/
      vlan:
        description: ''
        display: Wireless (300)
        id: 32
        name: Wireless
        url: https://demo.netbox.dev/api/ipam/vlans/32/
        vid: 300
      vrf: null
    - _depth: 2
      children: 4
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.152.0/22
      display_url: https://demo.netbox.dev/ipam/prefixes/66/
      family:
        label: IPv4
        value: 4
      id: 66
      is_pool: false
      last_updated: '2020-12-30T20:19:11.355000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.152.0/22
      role: null
      scope:
        description: ''
        display: DM-Pittsfield
        id: 8
        name: DM-Pittsfield
        slug: dm-pittsfield
        url: https://demo.netbox.dev/api/dcim/sites/8/
      scope_id: 8
      scope_type: dcim.site
      status:
        label: Container
        value: container
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/66/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.152.0/28
      display_url: https://demo.netbox.dev/ipam/prefixes/31/
      family:
        label: IPv4
        value: 4
      id: 31
      is_pool: false
      last_updated: '2020-12-30T20:13:43.441000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.152.0/28
      role:
        description: ''
        display: Management
        id: 4
        name: Management
        slug: management
        url: https://demo.netbox.dev/api/ipam/roles/4/
      scope:
        description: ''
        display: DM-Pittsfield
        id: 8
        name: DM-Pittsfield
        slug: dm-pittsfield
        url: https://demo.netbox.dev/api/dcim/sites/8/
      scope_id: 8
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/31/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.153.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/32/
      family:
        label: IPv4
        value: 4
      id: 32
      is_pool: false
      last_updated: '2020-12-30T20:13:43.527000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.153.0/24
      role:
        description: ''
        display: Access - Data
        id: 1
        name: Access - Data
        slug: access-data
        url: https://demo.netbox.dev/api/ipam/roles/1/
      scope:
        description: ''
        display: DM-Pittsfield
        id: 8
        name: DM-Pittsfield
        slug: dm-pittsfield
        url: https://demo.netbox.dev/api/dcim/sites/8/
      scope_id: 8
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/32/
      vlan:
        description: ''
        display: Data (100)
        id: 13
        name: Data
        url: https://demo.netbox.dev/api/ipam/vlans/13/
        vid: 100
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.154.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/33/
      family:
        label: IPv4
        value: 4
      id: 33
      is_pool: false
      last_updated: '2020-12-30T20:13:43.637000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.154.0/24
      role:
        description: ''
        display: Access - Voice
        id: 2
        name: Access - Voice
        slug: access-voice
        url: https://demo.netbox.dev/api/ipam/roles/2/
      scope:
        description: ''
        display: DM-Pittsfield
        id: 8
        name: DM-Pittsfield
        slug: dm-pittsfield
        url: https://demo.netbox.dev/api/dcim/sites/8/
      scope_id: 8
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/33/
      vlan:
        description: ''
        display: Voice (200)
        id: 14
        name: Voice
        url: https://demo.netbox.dev/api/ipam/vlans/14/
        vid: 200
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.155.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/34/
      family:
        label: IPv4
        value: 4
      id: 34
      is_pool: false
      last_updated: '2020-12-30T20:13:43.760000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.155.0/24
      role:
        description: ''
        display: Access - Wireless
        id: 3
        name: Access - Wireless
        slug: access-wireless
        url: https://demo.netbox.dev/api/ipam/roles/3/
      scope:
        description: ''
        display: DM-Pittsfield
        id: 8
        name: DM-Pittsfield
        slug: dm-pittsfield
        url: https://demo.netbox.dev/api/dcim/sites/8/
      scope_id: 8
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/34/
      vlan:
        description: ''
        display: Wireless (300)
        id: 33
        name: Wireless
        url: https://demo.netbox.dev/api/ipam/vlans/33/
        vid: 300
      vrf: null
    - _depth: 2
      children: 4
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.156.0/22
      display_url: https://demo.netbox.dev/ipam/prefixes/67/
      family:
        label: IPv4
        value: 4
      id: 67
      is_pool: false
      last_updated: '2020-12-30T20:19:11.419000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.156.0/22
      role: null
      scope:
        description: ''
        display: DM-Rochester
        id: 9
        name: DM-Rochester
        slug: dm-rochester
        url: https://demo.netbox.dev/api/dcim/sites/9/
      scope_id: 9
      scope_type: dcim.site
      status:
        label: Container
        value: container
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/67/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.156.0/28
      display_url: https://demo.netbox.dev/ipam/prefixes/35/
      family:
        label: IPv4
        value: 4
      id: 35
      is_pool: false
      last_updated: '2020-12-30T20:13:43.834000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.156.0/28
      role:
        description: ''
        display: Management
        id: 4
        name: Management
        slug: management
        url: https://demo.netbox.dev/api/ipam/roles/4/
      scope:
        description: ''
        display: DM-Rochester
        id: 9
        name: DM-Rochester
        slug: dm-rochester
        url: https://demo.netbox.dev/api/dcim/sites/9/
      scope_id: 9
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/35/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.157.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/36/
      family:
        label: IPv4
        value: 4
      id: 36
      is_pool: false
      last_updated: '2020-12-30T20:13:43.926000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.157.0/24
      role:
        description: ''
        display: Access - Data
        id: 1
        name: Access - Data
        slug: access-data
        url: https://demo.netbox.dev/api/ipam/roles/1/
      scope:
        description: ''
        display: DM-Rochester
        id: 9
        name: DM-Rochester
        slug: dm-rochester
        url: https://demo.netbox.dev/api/dcim/sites/9/
      scope_id: 9
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/36/
      vlan:
        description: ''
        display: Data (100)
        id: 15
        name: Data
        url: https://demo.netbox.dev/api/ipam/vlans/15/
        vid: 100
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.158.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/37/
      family:
        label: IPv4
        value: 4
      id: 37
      is_pool: false
      last_updated: '2020-12-30T20:13:44.013000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.158.0/24
      role:
        description: ''
        display: Access - Voice
        id: 2
        name: Access - Voice
        slug: access-voice
        url: https://demo.netbox.dev/api/ipam/roles/2/
      scope:
        description: ''
        display: DM-Rochester
        id: 9
        name: DM-Rochester
        slug: dm-rochester
        url: https://demo.netbox.dev/api/dcim/sites/9/
      scope_id: 9
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/37/
      vlan:
        description: ''
        display: Voice (200)
        id: 16
        name: Voice
        url: https://demo.netbox.dev/api/ipam/vlans/16/
        vid: 200
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.159.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/38/
      family:
        label: IPv4
        value: 4
      id: 38
      is_pool: false
      last_updated: '2020-12-30T20:13:44.099000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.159.0/24
      role:
        description: ''
        display: Access - Wireless
        id: 3
        name: Access - Wireless
        slug: access-wireless
        url: https://demo.netbox.dev/api/ipam/roles/3/
      scope:
        description: ''
        display: DM-Rochester
        id: 9
        name: DM-Rochester
        slug: dm-rochester
        url: https://demo.netbox.dev/api/dcim/sites/9/
      scope_id: 9
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/38/
      vlan:
        description: ''
        display: Wireless (300)
        id: 34
        name: Wireless
        url: https://demo.netbox.dev/api/ipam/vlans/34/
        vid: 300
      vrf: null
    - _depth: 2
      children: 4
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.160.0/22
      display_url: https://demo.netbox.dev/ipam/prefixes/68/
      family:
        label: IPv4
        value: 4
      id: 68
      is_pool: false
      last_updated: '2020-12-30T20:19:11.481000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.160.0/22
      role: null
      scope:
        description: ''
        display: DM-Scranton
        id: 10
        name: DM-Scranton
        slug: dm-scranton
        url: https://demo.netbox.dev/api/dcim/sites/10/
      scope_id: 10
      scope_type: dcim.site
      status:
        label: Container
        value: container
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/68/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.160.0/28
      display_url: https://demo.netbox.dev/ipam/prefixes/39/
      family:
        label: IPv4
        value: 4
      id: 39
      is_pool: false
      last_updated: '2020-12-30T20:13:44.173000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.160.0/28
      role:
        description: ''
        display: Management
        id: 4
        name: Management
        slug: management
        url: https://demo.netbox.dev/api/ipam/roles/4/
      scope:
        description: ''
        display: DM-Scranton
        id: 10
        name: DM-Scranton
        slug: dm-scranton
        url: https://demo.netbox.dev/api/dcim/sites/10/
      scope_id: 10
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/39/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.161.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/40/
      family:
        label: IPv4
        value: 4
      id: 40
      is_pool: false
      last_updated: '2020-12-30T20:13:44.259000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.161.0/24
      role:
        description: ''
        display: Access - Data
        id: 1
        name: Access - Data
        slug: access-data
        url: https://demo.netbox.dev/api/ipam/roles/1/
      scope:
        description: ''
        display: DM-Scranton
        id: 10
        name: DM-Scranton
        slug: dm-scranton
        url: https://demo.netbox.dev/api/dcim/sites/10/
      scope_id: 10
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/40/
      vlan:
        description: ''
        display: Data (100)
        id: 17
        name: Data
        url: https://demo.netbox.dev/api/ipam/vlans/17/
        vid: 100
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.162.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/41/
      family:
        label: IPv4
        value: 4
      id: 41
      is_pool: false
      last_updated: '2020-12-30T20:13:44.345000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.162.0/24
      role:
        description: ''
        display: Access - Voice
        id: 2
        name: Access - Voice
        slug: access-voice
        url: https://demo.netbox.dev/api/ipam/roles/2/
      scope:
        description: ''
        display: DM-Scranton
        id: 10
        name: DM-Scranton
        slug: dm-scranton
        url: https://demo.netbox.dev/api/dcim/sites/10/
      scope_id: 10
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/41/
      vlan:
        description: ''
        display: Voice (200)
        id: 18
        name: Voice
        url: https://demo.netbox.dev/api/ipam/vlans/18/
        vid: 200
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.163.0/24
      display_url: https://demo.netbox.dev/ipam/prefixes/42/
      family:
        label: IPv4
        value: 4
      id: 42
      is_pool: false
      last_updated: '2020-12-30T20:13:44.431000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.163.0/24
      role:
        description: ''
        display: Access - Wireless
        id: 3
        name: Access - Wireless
        slug: access-wireless
        url: https://demo.netbox.dev/api/ipam/roles/3/
      scope:
        description: ''
        display: DM-Scranton
        id: 10
        name: DM-Scranton
        slug: dm-scranton
        url: https://demo.netbox.dev/api/dcim/sites/10/
      scope_id: 10
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/42/
      vlan:
        description: ''
        display: Wireless (300)
        id: 35
        name: Wireless
        url: https://demo.netbox.dev/api/ipam/vlans/35/
        vid: 300
      vrf: null
    - _depth: 2
      children: 4
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.164.0/22
      display_url: https://demo.netbox.dev/ipam/prefixes/69/
      family:
        label: IPv4
        value: 4
      id: 69
      is_pool: false
      last_updated: '2020-12-30T20:19:11.543000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.164.0/22
      role: null
      scope:
        description: ''
        display: DM-Stamford
        id: 11
        name: DM-Stamford
        slug: dm-stamford
        url: https://demo.netbox.dev/api/dcim/sites/11/
      scope_id: 11
      scope_type: dcim.site
      status:
        label: Container
        value: container
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/69/
      vlan: null
      vrf: null
    - _depth: 3
      children: 0
      comments: ''
      created: '2020-12-30T00:00:00Z'
      custom_fields:
        cluster: null
      description: ''
      display: 10.112.164.0/28
      display_url: https://demo.netbox.dev/ipam/prefixes/43/
      family:
        label: IPv4
        value: 4
      id: 43
      is_pool: false
      last_updated: '2020-12-30T20:13:44.504000Z'
      mark_utilized: false
      owner: null
      prefix: 10.112.164.0/28
      role:
        description: ''
        display: Management
        id: 4
        name: Management
        slug: management
        url: https://demo.netbox.dev/api/ipam/roles/4/
      scope:
        description: ''
        display: DM-Stamford
        id: 11
        name: DM-Stamford
        slug: dm-stamford
        url: https://demo.netbox.dev/api/dcim/sites/11/
      scope_id: 11
      scope_type: dcim.site
      status:
        label: Active
        value: active
      tags: []
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      url: https://demo.netbox.dev/api/ipam/prefixes/43/
      vlan: null
      vrf: null
    ```

=== ":material-language-markdown: Markdown Output"

    | ID | Display | Status | Role | Prefix | VLAN | Tenant |
    | --- | --- | --- | --- | --- | --- | --- |
    | 1 | 10.112.0.0/15 | {"label":"Container","value":"container"} | - | 10.112.0.0/15 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 2 | 10.112.0.0/17 | {"label":"Container","value":"container"} | - | 10.112.0.0/17 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 3 | 10.112.128.0/17 | {"label":"Container","value":"container"} | - | 10.112.128.0/17 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 60 | 10.112.128.0/22 | {"label":"Container","value":"container"} | - | 10.112.128.0/22 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 7 | 10.112.128.0/28 | {"label":"Active","value":"active"} | {"description":"","display":"Management","id":4,"name":"Management","slug":"management","url":"https://demo.netbox.dev/api/ipam/roles/4/"} | 10.112.128.0/28 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 8 | 10.112.129.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Data","id":1,"name":"Access - Data","slug":"access-data","url":"https://demo.netbox.dev/api/ipam/roles/1/"} | 10.112.129.0/24 | {"description":"","display":"Data (100)","id":1,"name":"Data","url":"https://demo.netbox.dev/api/ipam/vlans/1/","vid":100} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 9 | 10.112.130.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Voice","id":2,"name":"Access - Voice","slug":"access-voice","url":"https://demo.netbox.dev/api/ipam/roles/2/"} | 10.112.130.0/24 | {"description":"","display":"Voice (200)","id":2,"name":"Voice","url":"https://demo.netbox.dev/api/ipam/vlans/2/","vid":200} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 10 | 10.112.131.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Wireless","id":3,"name":"Access - Wireless","slug":"access-wireless","url":"https://demo.netbox.dev/api/ipam/roles/3/"} | 10.112.131.0/24 | {"description":"","display":"Wireless (300)","id":27,"name":"Wireless","url":"https://demo.netbox.dev/api/ipam/vlans/27/","vid":300} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 61 | 10.112.132.0/22 | {"label":"Container","value":"container"} | - | 10.112.132.0/22 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 11 | 10.112.132.0/28 | {"label":"Active","value":"active"} | {"description":"","display":"Management","id":4,"name":"Management","slug":"management","url":"https://demo.netbox.dev/api/ipam/roles/4/"} | 10.112.132.0/28 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 12 | 10.112.133.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Data","id":1,"name":"Access - Data","slug":"access-data","url":"https://demo.netbox.dev/api/ipam/roles/1/"} | 10.112.133.0/24 | {"description":"","display":"Data (100)","id":3,"name":"Data","url":"https://demo.netbox.dev/api/ipam/vlans/3/","vid":100} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 13 | 10.112.134.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Voice","id":2,"name":"Access - Voice","slug":"access-voice","url":"https://demo.netbox.dev/api/ipam/roles/2/"} | 10.112.134.0/24 | {"description":"","display":"Voice (200)","id":4,"name":"Voice","url":"https://demo.netbox.dev/api/ipam/vlans/4/","vid":200} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 14 | 10.112.135.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Wireless","id":3,"name":"Access - Wireless","slug":"access-wireless","url":"https://demo.netbox.dev/api/ipam/roles/3/"} | 10.112.135.0/24 | {"description":"","display":"Wireless (300)","id":28,"name":"Wireless","url":"https://demo.netbox.dev/api/ipam/vlans/28/","vid":300} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 62 | 10.112.136.0/22 | {"label":"Container","value":"container"} | - | 10.112.136.0/22 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 15 | 10.112.136.0/28 | {"label":"Active","value":"active"} | {"description":"","display":"Management","id":4,"name":"Management","slug":"management","url":"https://demo.netbox.dev/api/ipam/roles/4/"} | 10.112.136.0/28 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 16 | 10.112.137.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Data","id":1,"name":"Access - Data","slug":"access-data","url":"https://demo.netbox.dev/api/ipam/roles/1/"} | 10.112.137.0/24 | {"description":"","display":"Data (100)","id":5,"name":"Data","url":"https://demo.netbox.dev/api/ipam/vlans/5/","vid":100} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 17 | 10.112.138.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Voice","id":2,"name":"Access - Voice","slug":"access-voice","url":"https://demo.netbox.dev/api/ipam/roles/2/"} | 10.112.138.0/24 | {"description":"","display":"Voice (200)","id":6,"name":"Voice","url":"https://demo.netbox.dev/api/ipam/vlans/6/","vid":200} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 18 | 10.112.139.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Wireless","id":3,"name":"Access - Wireless","slug":"access-wireless","url":"https://demo.netbox.dev/api/ipam/roles/3/"} | 10.112.139.0/24 | {"description":"","display":"Wireless (300)","id":29,"name":"Wireless","url":"https://demo.netbox.dev/api/ipam/vlans/29/","vid":300} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 63 | 10.112.140.0/22 | {"label":"Container","value":"container"} | - | 10.112.140.0/22 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 19 | 10.112.140.0/28 | {"label":"Active","value":"active"} | {"description":"","display":"Management","id":4,"name":"Management","slug":"management","url":"https://demo.netbox.dev/api/ipam/roles/4/"} | 10.112.140.0/28 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 20 | 10.112.141.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Data","id":1,"name":"Access - Data","slug":"access-data","url":"https://demo.netbox.dev/api/ipam/roles/1/"} | 10.112.141.0/24 | {"description":"","display":"Data (100)","id":7,"name":"Data","url":"https://demo.netbox.dev/api/ipam/vlans/7/","vid":100} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 21 | 10.112.142.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Voice","id":2,"name":"Access - Voice","slug":"access-voice","url":"https://demo.netbox.dev/api/ipam/roles/2/"} | 10.112.142.0/24 | {"description":"","display":"Voice (200)","id":8,"name":"Voice","url":"https://demo.netbox.dev/api/ipam/vlans/8/","vid":200} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 22 | 10.112.143.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Wireless","id":3,"name":"Access - Wireless","slug":"access-wireless","url":"https://demo.netbox.dev/api/ipam/roles/3/"} | 10.112.143.0/24 | {"description":"","display":"Wireless (300)","id":30,"name":"Wireless","url":"https://demo.netbox.dev/api/ipam/vlans/30/","vid":300} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 64 | 10.112.144.0/22 | {"label":"Container","value":"container"} | - | 10.112.144.0/22 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 23 | 10.112.144.0/28 | {"label":"Active","value":"active"} | {"description":"","display":"Management","id":4,"name":"Management","slug":"management","url":"https://demo.netbox.dev/api/ipam/roles/4/"} | 10.112.144.0/28 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 24 | 10.112.145.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Data","id":1,"name":"Access - Data","slug":"access-data","url":"https://demo.netbox.dev/api/ipam/roles/1/"} | 10.112.145.0/24 | {"description":"","display":"Data (100)","id":9,"name":"Data","url":"https://demo.netbox.dev/api/ipam/vlans/9/","vid":100} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 25 | 10.112.146.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Voice","id":2,"name":"Access - Voice","slug":"access-voice","url":"https://demo.netbox.dev/api/ipam/roles/2/"} | 10.112.146.0/24 | {"description":"","display":"Voice (200)","id":10,"name":"Voice","url":"https://demo.netbox.dev/api/ipam/vlans/10/","vid":200} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 26 | 10.112.147.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Wireless","id":3,"name":"Access - Wireless","slug":"access-wireless","url":"https://demo.netbox.dev/api/ipam/roles/3/"} | 10.112.147.0/24 | {"description":"","display":"Wireless (300)","id":31,"name":"Wireless","url":"https://demo.netbox.dev/api/ipam/vlans/31/","vid":300} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 65 | 10.112.148.0/22 | {"label":"Container","value":"container"} | - | 10.112.148.0/22 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 27 | 10.112.148.0/28 | {"label":"Active","value":"active"} | {"description":"","display":"Management","id":4,"name":"Management","slug":"management","url":"https://demo.netbox.dev/api/ipam/roles/4/"} | 10.112.148.0/28 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 28 | 10.112.149.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Data","id":1,"name":"Access - Data","slug":"access-data","url":"https://demo.netbox.dev/api/ipam/roles/1/"} | 10.112.149.0/24 | {"description":"","display":"Data (100)","id":11,"name":"Data","url":"https://demo.netbox.dev/api/ipam/vlans/11/","vid":100} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 29 | 10.112.150.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Voice","id":2,"name":"Access - Voice","slug":"access-voice","url":"https://demo.netbox.dev/api/ipam/roles/2/"} | 10.112.150.0/24 | {"description":"","display":"Voice (200)","id":12,"name":"Voice","url":"https://demo.netbox.dev/api/ipam/vlans/12/","vid":200} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 30 | 10.112.151.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Wireless","id":3,"name":"Access - Wireless","slug":"access-wireless","url":"https://demo.netbox.dev/api/ipam/roles/3/"} | 10.112.151.0/24 | {"description":"","display":"Wireless (300)","id":32,"name":"Wireless","url":"https://demo.netbox.dev/api/ipam/vlans/32/","vid":300} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 66 | 10.112.152.0/22 | {"label":"Container","value":"container"} | - | 10.112.152.0/22 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 31 | 10.112.152.0/28 | {"label":"Active","value":"active"} | {"description":"","display":"Management","id":4,"name":"Management","slug":"management","url":"https://demo.netbox.dev/api/ipam/roles/4/"} | 10.112.152.0/28 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 32 | 10.112.153.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Data","id":1,"name":"Access - Data","slug":"access-data","url":"https://demo.netbox.dev/api/ipam/roles/1/"} | 10.112.153.0/24 | {"description":"","display":"Data (100)","id":13,"name":"Data","url":"https://demo.netbox.dev/api/ipam/vlans/13/","vid":100} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 33 | 10.112.154.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Voice","id":2,"name":"Access - Voice","slug":"access-voice","url":"https://demo.netbox.dev/api/ipam/roles/2/"} | 10.112.154.0/24 | {"description":"","display":"Voice (200)","id":14,"name":"Voice","url":"https://demo.netbox.dev/api/ipam/vlans/14/","vid":200} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 34 | 10.112.155.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Wireless","id":3,"name":"Access - Wireless","slug":"access-wireless","url":"https://demo.netbox.dev/api/ipam/roles/3/"} | 10.112.155.0/24 | {"description":"","display":"Wireless (300)","id":33,"name":"Wireless","url":"https://demo.netbox.dev/api/ipam/vlans/33/","vid":300} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 67 | 10.112.156.0/22 | {"label":"Container","value":"container"} | - | 10.112.156.0/22 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 35 | 10.112.156.0/28 | {"label":"Active","value":"active"} | {"description":"","display":"Management","id":4,"name":"Management","slug":"management","url":"https://demo.netbox.dev/api/ipam/roles/4/"} | 10.112.156.0/28 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 36 | 10.112.157.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Data","id":1,"name":"Access - Data","slug":"access-data","url":"https://demo.netbox.dev/api/ipam/roles/1/"} | 10.112.157.0/24 | {"description":"","display":"Data (100)","id":15,"name":"Data","url":"https://demo.netbox.dev/api/ipam/vlans/15/","vid":100} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 37 | 10.112.158.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Voice","id":2,"name":"Access - Voice","slug":"access-voice","url":"https://demo.netbox.dev/api/ipam/roles/2/"} | 10.112.158.0/24 | {"description":"","display":"Voice (200)","id":16,"name":"Voice","url":"https://demo.netbox.dev/api/ipam/vlans/16/","vid":200} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 38 | 10.112.159.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Wireless","id":3,"name":"Access - Wireless","slug":"access-wireless","url":"https://demo.netbox.dev/api/ipam/roles/3/"} | 10.112.159.0/24 | {"description":"","display":"Wireless (300)","id":34,"name":"Wireless","url":"https://demo.netbox.dev/api/ipam/vlans/34/","vid":300} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 68 | 10.112.160.0/22 | {"label":"Container","value":"container"} | - | 10.112.160.0/22 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 39 | 10.112.160.0/28 | {"label":"Active","value":"active"} | {"description":"","display":"Management","id":4,"name":"Management","slug":"management","url":"https://demo.netbox.dev/api/ipam/roles/4/"} | 10.112.160.0/28 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 40 | 10.112.161.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Data","id":1,"name":"Access - Data","slug":"access-data","url":"https://demo.netbox.dev/api/ipam/roles/1/"} | 10.112.161.0/24 | {"description":"","display":"Data (100)","id":17,"name":"Data","url":"https://demo.netbox.dev/api/ipam/vlans/17/","vid":100} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 41 | 10.112.162.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Voice","id":2,"name":"Access - Voice","slug":"access-voice","url":"https://demo.netbox.dev/api/ipam/roles/2/"} | 10.112.162.0/24 | {"description":"","display":"Voice (200)","id":18,"name":"Voice","url":"https://demo.netbox.dev/api/ipam/vlans/18/","vid":200} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 42 | 10.112.163.0/24 | {"label":"Active","value":"active"} | {"description":"","display":"Access - Wireless","id":3,"name":"Access - Wireless","slug":"access-wireless","url":"https://demo.netbox.dev/api/ipam/roles/3/"} | 10.112.163.0/24 | {"description":"","display":"Wireless (300)","id":35,"name":"Wireless","url":"https://demo.netbox.dev/api/ipam/vlans/35/","vid":300} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 69 | 10.112.164.0/22 | {"label":"Container","value":"container"} | - | 10.112.164.0/22 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 43 | 10.112.164.0/28 | {"label":"Active","value":"active"} | {"description":"","display":"Management","id":4,"name":"Management","slug":"management","url":"https://demo.netbox.dev/api/ipam/roles/4/"} | 10.112.164.0/28 | - | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">2.995s</span>

!!! warning "Truncated"
    Output was truncated. Full text is in `docs/generated/raw/`.

---

### `nbx demo dcim sites list`

=== ":material-console: Command"

    ```bash
    nbx demo dcim sites list --markdown
    ```

=== ":material-text-box-outline: Output"

    ```text
    Status: 200
    | ID | Name | Display | Status | Tenant |
    | --- | --- | --- | --- | --- |
    | 26 | Amsterdam-DC | Amsterdam-DC | {"label":"Active","value":"active"} | - |
    | 24 | Butler Communications | Butler Communications | {"label":"Active","value":"active"} | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
    | 22 | D. S. Weaver Labs | D. S. Weaver Labs | {"label":"Active","value":"active"} | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
    | 27 | Demo site with contact | Demo site with contact | {"label":"Active","value":"active"} | - |
    | 2 | DM-Akron | DM-Akron | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 3 | DM-Albany | DM-Albany | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 4 | DM-Binghamton | DM-Binghamton | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 5 | DM-Buffalo | DM-Buffalo | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 6 | DM-Camden | DM-Camden | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 7 | DM-Nashua | DM-Nashua | {"
    
    … (truncated by character limit)
    ```

=== ":material-code-json: JSON Output"

    ```json
    {
      "count": 28,
      "next": null,
      "previous": null,
      "results": [
        {
          "asns": [],
          "circuit_count": 0,
          "comments": "",
          "created": "2026-03-23T12:17:40.257743Z",
          "custom_fields": {},
          "description": "",
          "device_count": 3,
          "display": "Amsterdam-DC",
          "display_url": "https://demo.netbox.dev/dcim/sites/26/",
          "facility": "",
          "group": null,
          "id": 26,
          "last_updated": "2026-03-23T12:17:40.257756Z",
          "latitude": null,
          "longitude": null,
          "name": "Amsterdam-DC",
          "owner": null,
          "physical_address": "",
          "prefix_count": 0,
          "rack_count": 1,
          "region": null,
          "shipping_address": "",
          "slug": "amsterdam-dc",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": null,
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/26/",
          "virtualmachine_count": 0,
          "vlan_count": 0
        },
        {
          "asns": [],
          "circuit_count": 1,
          "comments": "",
          "created": "2021-04-02T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 4,
          "display": "Butler Communications",
          "display_url": "https://demo.netbox.dev/dcim/sites/24/",
          "facility": "BUT",
          "group": null,
          "id": 24,
          "last_updated": "2021-12-30T15:45:37.371000Z",
          "latitude": null,
          "longitude": null,
          "name": "Butler Communications",
          "owner": null,
          "physical_address": "3210 Faucette Dr., Raleigh, NC 27607",
          "prefix_count": 0,
          "rack_count": 1,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "North Carolina",
            "id": 40,
            "name": "North Carolina",
            "site_count": 0,
            "slug": "us-nc",
            "url": "https://demo.netbox.dev/api/dcim/regions/40/"
          },
          "shipping_address": "",
          "slug": "ncsu-128",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "673ab7",
              "display": "Golf",
              "display_url": "https://demo.netbox.dev/extras/tags/7/",
              "id": 7,
              "name": "Golf",
              "slug": "golf",
              "url": "https://demo.netbox.dev/api/extras/tags/7/"
            },
            {
              "color": "009688",
              "display": "Lima",
              "display_url": "https://demo.netbox.dev/extras/tags/12/",
              "id": 12,
              "name": "Lima",
              "slug": "lima",
              "url": "https://demo.netbox.dev/api/extras/tags/12/"
            },
            {
              "color": "9e9e9e",
              "display": "X-ray",
              "display_url": "https://demo.netbox.dev/extras/tags/24/",
              "id": 24,
              "name": "X-ray",
              "slug": "x-ray",
              "url": "https://demo.netbox.dev/api/extras/tags/24/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "NC State University",
            "id": 13,
            "name": "NC State University",
            "slug": "nc-state",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/13/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/24/",
          "virtualmachine_count": 0,
          "vlan_count": 0
        },
        {
          "asns": [],
          "circuit_count": 1,
          "comments": "",
          "created": "2021-04-02T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 2,
          "display": "D. S. Weaver Labs",
          "display_url": "https://demo.netbox.dev/dcim/sites/22/",
          "facility": "DSW",
          "group": null,
          "id": 22,
          "last_updated": "2021-12-30T15:45:37.549000Z",
          "latitude": null,
          "longitude": null,
          "name": "D. S. Weaver Labs",
          "owner": null,
          "physical_address": "3110 Faucette Dr., Raleigh, NC 27607",
          "prefix_count": 0,
          "rack_count": 1,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "North Carolina",
            "id": 40,
            "name": "North Carolina",
            "site_count": 0,
            "slug": "us-nc",
            "url": "https://demo.netbox.dev/api/dcim/regions/40/"
          },
          "shipping_address": "",
          "slug": "ncsu-117",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "cddc39",
              "display": "Quebec",
              "display_url": "https://demo.netbox.dev/extras/tags/17/",
              "id": 17,
              "name": "Quebec",
              "slug": "quebec",
              "url": "https://demo.netbox.dev/api/extras/tags/17/"
            },
            {
              "color": "ff9800",
              "display": "Tango",
              "display_url": "https://demo.netbox.dev/extras/tags/20/",
              "id": 20,
              "name": "Tango",
              "slug": "tango",
              "url": "https://demo.netbox.dev/api/extras/tags/20/"
            },
            {
              "color": "9e9e9e",
              "display": "X-ray",
              "display_url": "https://demo.netbox.dev/extras/tags/24/",
              "id": 24,
              "name": "X-ray",
              "slug": "x-ray",
              "url": "https://demo.netbox.dev/api/extras/tags/24/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "NC State University",
            "id": 13,
            "name": "NC State University",
            "slug": "nc-state",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/13/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/22/",
          "virtualmachine_count": 0,
          "vlan_count": 0
        },
        {
          "asns": [],
          "circuit_count": 0,
          "comments": "Lab contact: John Doe, john.doe@telekom.de",
          "created": "2026-03-23T12:52:33.147332Z",
          "custom_fields": {},
          "description": "",
          "device_count": 0,
          "display": "Demo site with contact",
          "display_url": "https://demo.netbox.dev/dcim/sites/27/",
          "facility": "",
          "group": null,
          "id": 27,
          "last_updated": "2026-03-23T12:52:33.147344Z",
          "latitude": null,
          "longitude": null,
          "name": "Demo site with contact",
          "owner": null,
          "physical_address": "",
          "prefix_count": 0,
          "rack_count": 0,
          "region": null,
          "shipping_address": "",
          "slug": "demo-site-with-contact",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "ffe4e1",
              "display": "Delta",
              "display_url": "https://demo.netbox.dev/extras/tags/4/",
              "id": 4,
              "name": "Delta",
              "slug": "delta",
              "url": "https://demo.netbox.dev/api/extras/tags/4/"
            }
          ],
          "tenant": null,
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/27/",
          "virtualmachine_count": 0,
          "vlan_count": 0
        },
        {
          "asns": [],
          "circuit_count": 2,
          "comments": "",
          "created": "2020-12-19T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 5,
          "display": "DM-Akron",
          "display_url": "https://demo.netbox.dev/dcim/sites/2/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 2,
          "last_updated": "2021-12-30T15:45:37.384000Z",
          "latitude": null,
          "longitude": null,
          "name": "DM-Akron",
          "owner": null,
          "physical_address": "",
          "prefix_count": 5,
          "rack_count": 2,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "Ohio",
            "id": 51,
            "name": "Ohio",
            "site_count": 0,
            "slug": "us-oh",
            "url": "https://demo.netbox.dev/api/dcim/regions/51/"
          },
          "shipping_address": "",
          "slug": "dm-akron",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "aa1409",
              "display": "Alpha",
              "display_url": "https://demo.netbox.dev/extras/tags/1/",
              "id": 1,
              "name": "Alpha",
              "slug": "alpha",
              "url": "https://demo.netbox.dev/api/extras/tags/1/"
            },
            {
              "color": "f44336",
              "display": "Bravo",
              "display_url": "https://demo.netbox.dev/extras/tags/2/",
              "id": 2,
              "name": "Bravo",
              "slug": "bravo",
              "url": "https://demo.netbox.dev/api/extras/tags/2/"
            },
            {
              "color": "673ab7",
              "display": "Golf",
              "display_url": "https://demo.netbox.dev/extras/tags/7/",
              "id": 7,
              "name": "Golf",
              "slug": "golf",
              "url": "https://demo.netbox.dev/api/extras/tags/7/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/2/",
          "virtualmachine_count": 0,
          "vlan_count": 3
        },
        {
          "asns": [],
          "circuit_count": 2,
          "comments": "",
          "created": "2020-12-19T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 4,
          "display": "DM-Albany",
          "display_url": "https://demo.netbox.dev/dcim/sites/3/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 3,
          "last_updated": "2021-12-30T15:45:37.397000Z",
          "latitude": null,
          "longitude": null,
          "name": "DM-Albany",
          "owner": null,
          "physical_address": "",
          "prefix_count": 5,
          "rack_count": 1,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "New York",
            "id": 43,
            "name": "New York",
            "site_count": 0,
            "slug": "us-ny",
            "url": "https://demo.netbox.dev/api/dcim/regions/43/"
          },
          "shipping_address": "",
          "slug": "dm-albany",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "e91e63",
              "display": "Charlie",
              "display_url": "https://demo.netbox.dev/extras/tags/3/",
              "id": 3,
              "name": "Charlie",
              "slug": "charlie",
              "url": "https://demo.netbox.dev/api/extras/tags/3/"
            },
            {
              "color": "2f6a31",
              "display": "November",
              "display_url": "https://demo.netbox.dev/extras/tags/14/",
              "id": 14,
              "name": "November",
              "slug": "november",
              "url": "https://demo.netbox.dev/api/extras/tags/14/"
            },
            {
              "color": "8bc34a",
              "display": "Papa",
              "display_url": "https://demo.netbox.dev/extras/tags/16/",
              "id": 16,
              "name": "Papa",
              "slug": "papa",
              "url": "https://demo.netbox.dev/api/extras/tags/16/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/3/",
          "virtualmachine_count": 0,
          "vlan_count": 3
        },
        {
          "asns": [],
          "circuit_count": 2,
          "comments": "",
          "created": "2020-12-19T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 4,
          "display": "DM-Binghamton",
          "display_url": "https://demo.netbox.dev/dcim/sites/4/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 4,
          "last_updated": "2021-12-30T15:45:37.409000Z",
          "latitude": null,
          "longitude": null,
          "name": "DM-Binghamton",
          "owner": null,
          "physical_address": "",
          "prefix_count": 5,
          "rack_count": 1,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "New York",
            "id": 43,
            "name": "New York",
            "site_count": 0,
            "slug": "us-ny",
            "url": "https://demo.netbox.dev/api/dcim/regions/43/"
          },
          "shipping_address": "",
          "slug": "dm-binghamton",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "673ab7",
              "display": "Golf",
              "display_url": "https://demo.netbox.dev/extras/tags/7/",
              "id": 7,
              "name": "Golf",
              "slug": "golf",
              "url": "https://demo.netbox.dev/api/extras/tags/7/"
            },
            {
              "color": "cddc39",
              "display": "Quebec",
              "display_url": "https://demo.netbox.dev/extras/tags/17/",
              "id": 17,
              "name": "Quebec",
              "slug": "quebec",
              "url": "https://demo.netbox.dev/api/extras/tags/17/"
            },
            {
              "color": "ffeb3b",
              "display": "Romeo",
              "display_url": "https://demo.netbox.dev/extras/tags/18/",
              "id": 18,
              "name": "Romeo",
              "slug": "romeo",
              "url": "https://demo.netbox.dev/api/extras/tags/18/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/4/",
          "virtualmachine_count": 0,
          "vlan_count": 3
        },
        {
          "asns": [],
          "circuit_count": 2,
          "comments": "",
          "created": "2020-12-19T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 4,
          "display": "DM-Buffalo",
          "display_url": "https://demo.netbox.dev/dcim/sites/5/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 5,
          "last_updated": "2021-12-30T15:45:37.422000Z",
          "latitude": null,
          "longitude": null,
          "name": "DM-Buffalo",
          "owner": null,
          "physical_address": "",
          "prefix_count": 5,
          "rack_count": 1,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "New York",
            "id": 43,
            "name": "New York",
            "site_count": 0,
            "slug": "us-ny",
            "url": "https://demo.netbox.dev/api/dcim/regions/43/"
          },
          "shipping_address": "",
          "slug": "dm-buffalo",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "ffe4e1",
              "display": "Delta",
              "display_url": "https://demo.netbox.dev/extras/tags/4/",
              "id": 4,
              "name": "Delta",
              "slug": "delta",
              "url": "https://demo.netbox.dev/api/extras/tags/4/"
            },
            {
              "color": "ff66ff",
              "display": "Echo",
              "display_url": "https://demo.netbox.dev/extras/tags/5/",
              "id": 5,
              "name": "Echo",
              "slug": "echo",
              "url": "https://demo.netbox.dev/api/extras/tags/5/"
            },
            {
              "color": "111111",
              "display": "Zulu",
              "display_url": "https://demo.netbox.dev/extras/tags/26/",
              "id": 26,
              "name": "Zulu",
              "slug": "zulu",
              "url": "https://demo.netbox.dev/api/extras/tags/26/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/5/",
          "virtualmachine_count": 0,
          "vlan_count": 3
        },
        {
          "asns": [],
          "circuit_count": 2,
          "comments": "",
          "created": "2020-12-19T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 4,
          "display": "DM-Camden",
          "display_url": "https://demo.netbox.dev/dcim/sites/6/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 6,
          "last_updated": "2021-12-30T15:45:37.434000Z",
          "latitude": null,
          "longitude": null,
          "name": "DM-Camden",
          "owner": null,
          "physical_address": "",
          "prefix_count": 5,
          "rack_count": 1,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "New Jersey",
            "id": 38,
            "name": "New Jersey",
            "site_count": 0,
            "slug": "us-nj",
            "url": "https://demo.netbox.dev/api/dcim/regions/38/"
          },
          "shipping_address": "",
          "slug": "dm-camden",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "03a9f4",
              "display": "Juliett",
              "display_url": "https://demo.netbox.dev/extras/tags/10/",
              "id": 10,
              "name": "Juliett",
              "slug": "juliett",
              "url": "https://demo.netbox.dev/api/extras/tags/10/"
            },
            {
              "color": "00bcd4",
              "display": "Kilo",
              "display_url": "https://demo.netbox.dev/extras/tags/11/",
              "id": 11,
              "name": "Kilo",
              "slug": "kilo",
              "url": "https://demo.netbox.dev/api/extras/tags/11/"
            },
            {
              "color": "111111",
              "display": "Zulu",
              "display_url": "https://demo.netbox.dev/extras/tags/26/",
              "id": 26,
              "name": "Zulu",
              "slug": "zulu",
              "url": "https://demo.netbox.dev/api/extras/tags/26/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/6/",
          "virtualmachine_count": 0,
          "vlan_count": 3
        },
        {
          "asns": [],
          "circuit_count": 2,
          "comments": "",
          "created": "2020-12-19T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 4,
          "display": "DM-Nashua",
          "display_url": "https://demo.netbox.dev/dcim/sites/7/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 7,
          "last_updated": "2021-12-30T15:45:37.445000Z",
          "latitude": null,
          "longitude": null,
          "name": "DM-Nashua",
          "owner": null,
          "physical_address": "",
          "prefix_count": 5,
          "rack_count": 1,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "New Hampshire",
            "id": 37,
            "name": "New Hampshire",
            "site_count": 0,
            "slug": "us-nh",
            "url": "https://demo.netbox.dev/api/dcim/regions/37/"
          },
          "shipping_address": "",
          "slug": "dm-nashua",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "ff66ff",
              "display": "Echo",
              "display_url": "https://demo.netbox.dev/extras/tags/5/",
              "id": 5,
              "name": "Echo",
              "slug": "echo",
              "url": "https://demo.netbox.dev/api/extras/tags/5/"
            },
            {
              "color": "2f6a31",
              "display": "November",
              "display_url": "https://demo.netbox.dev/extras/tags/14/",
              "id": 14,
              "name": "November",
              "slug": "november",
              "url": "https://demo.netbox.dev/api/extras/tags/14/"
            },
            {
              "color": "111111",
              "display": "Zulu",
              "display_url": "https://demo.netbox.dev/extras/tags/26/",
              "id": 26,
              "name": "Zulu",
              "slug": "zulu",
              "url": "https://demo.netbox.dev/api/extras/tags/26/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/7/",
          "virtualmachine_count": 0,
          "vlan_count": 3
        },
        {
          "asns": [],
          "circuit_count": 0,
          "comments": "",
          "created": "2020-12-19T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 0,
          "display": "DM-NYC",
          "display_url": "https://demo.netbox.dev/dcim/sites/1/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Headquarters",
            "id": 3,
            "name": "Headquarters",
            "site_count": 0,
            "slug": "headquarters",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/3/"
          },
          "id": 1,
          "last_updated": "2021-12-30T15:45:37.458000Z",
          "latitude": null,
          "longitude": null,
          "name": "DM-NYC",
          "owner": null,
          "physical_address": "",
          "prefix_count": 0,
          "rack_count": 0,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "New York",
            "id": 43,
            "name": "New York",
            "site_count": 0,
            "slug": "us-ny",
            "url": "https://demo.netbox.dev/api/dcim/regions/43/"
          },
          "shipping_address": "",
          "slug": "dm-nyc",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "4caf50",
              "display": "Oscar",
              "display_url": "https://demo.netbox.dev/extras/tags/15/",
              "id": 15,
              "name": "Oscar",
              "slug": "oscar",
              "url": "https://demo.netbox.dev/api/extras/tags/15/"
            },
            {
              "color": "cddc39",
              "display": "Quebec",
              "display_url": "https://demo.netbox.dev/extras/tags/17/",
              "id": 17,
              "name": "Quebec",
              "slug": "quebec",
              "url": "https://demo.netbox.dev/api/extras/tags/17/"
            },
            {
              "color": "795548",
              "display": "Victor",
              "display_url": "https://demo.netbox.dev/extras/tags/22/",
              "id": 22,
              "name": "Victor",
              "slug": "victor",
              "url": "https://demo.netbox.dev/api/extras/tags/22/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/1/",
          "virtualmachine_count": 0,
          "vlan_count": 0
        },
        {
          "asns": [],
          "circuit_count": 2,
          "comments": "",
          "created": "2020-12-19T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 4,
          "display": "DM-Pittsfield",
          "display_url": "https://demo.netbox.dev/dcim/sites/8/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 8,
          "last_updated": "2021-12-30T15:46:40.331000Z",
          "latitude": null,
          "longitude": null,
          "name": "DM-Pittsfield",
          "owner": null,
          "physical_address": "",
          "prefix_count": 5,
          "rack_count": 1,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "Massachusetts",
            "id": 76,
            "name": "Massachusetts",
            "site_count": 0,
            "slug": "us-ma",
            "url": "https://demo.netbox.dev/api/dcim/regions/76/"
          },
          "shipping_address": "",
          "slug": "dm-pittsfield",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "ff66ff",
              "display": "Echo",
              "display_url": "https://demo.netbox.dev/extras/tags/5/",
              "id": 5,
              "name": "Echo",
              "slug": "echo",
              "url": "https://demo.netbox.dev/api/extras/tags/5/"
            },
            {
              "color": "03a9f4",
              "display": "Juliett",
              "display_url": "https://demo.netbox.dev/extras/tags/10/",
              "id": 10,
              "name": "Juliett",
              "slug": "juliett",
              "url": "https://demo.netbox.dev/api/extras/tags/10/"
            },
            {
              "color": "ff9800",
              "display": "Tango",
              "display_url": "https://demo.netbox.dev/extras/tags/20/",
              "id": 20,
              "name": "Tango",
              "slug": "tango",
              "url": "https://demo.netbox.dev/api/extras/tags/20/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/8/",
          "virtualmachine_count": 0,
          "vlan_count": 3
        },
        {
          "asns": [],
          "circuit_count": 2,
          "comments": "",
          "created": "2020-12-19T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 4,
          "display": "DM-Rochester",
          "display_url": "https://demo.netbox.dev/dcim/sites/9/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 9,
          "last_updated": "2021-12-30T15:45:37.477000Z",
          "latitude": null,
          "longitude": null,
          "name": "DM-Rochester",
          "owner": null,
          "physical_address": "",
          "prefix_count": 5,
          "rack_count": 1,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "New York",
            "id": 43,
            "name": "New York",
            "site_count": 0,
            "slug": "us-ny",
            "url": "https://demo.netbox.dev/api/dcim/regions/43/"
          },
          "shipping_address": "",
          "slug": "dm-rochester",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "ff66ff",
              "display": "Echo",
              "display_url": "https://demo.netbox.dev/extras/tags/5/",
              "id": 5,
              "name": "Echo",
              "slug": "echo",
              "url": "https://demo.netbox.dev/api/extras/tags/5/"
            },
            {
              "color": "9c27b0",
              "display": "Foxtrot",
              "display_url": "https://demo.netbox.dev/extras/tags/6/",
              "id": 6,
              "name": "Foxtrot",
              "slug": "foxtrot",
              "url": "https://demo.netbox.dev/api/extras/tags/6/"
            },
            {
              "color": "cddc39",
              "display": "Quebec",
              "display_url": "https://demo.netbox.dev/extras/tags/17/",
              "id": 17,
              "name": "Quebec",
              "slug": "quebec",
              "url": "https://demo.netbox.dev/api/extras/tags/17/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/9/",
          "virtualmachine_count": 0,
          "vlan_count": 3
        },
        {
          "asns": [],
          "circuit_count": 2,
          "comments": "",
          "created": "2020-12-19T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 4,
          "display": "DM-Scranton",
          "display_url": "https://demo.netbox.dev/dcim/sites/10/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 10,
          "last_updated": "2021-12-30T15:45:37.489000Z",
          "latitude": null,
          "longitude": null,
          "name": "DM-Scranton",
          "owner": null,
          "physical_address": "",
          "prefix_count": 5,
          "rack_count": 1,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "Pennsylvania",
            "id": 63,
            "name": "Pennsylvania",
            "site_count": 0,
            "slug": "us-pa",
            "url": "https://demo.netbox.dev/api/dcim/regions/63/"
          },
          "shipping_address": "",
          "slug": "dm-scranton",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "673ab7",
              "display": "Golf",
              "display_url": "https://demo.netbox.dev/extras/tags/7/",
              "id": 7,
              "name": "Golf",
              "slug": "golf",
              "url": "https://demo.netbox.dev/api/extras/tags/7/"
            },
            {
              "color": "03a9f4",
              "display": "Juliett",
              "display_url": "https://demo.netbox.dev/extras/tags/10/",
              "id": 10,
              "name": "Juliett",
              "slug": "juliett",
              "url": "https://demo.netbox.dev/api/extras/tags/10/"
            },
            {
              "color": "9e9e9e",
              "display": "X-ray",
              "display_url": "https://demo.netbox.dev/extras/tags/24/",
              "id": 24,
              "name": "X-ray",
              "slug": "x-ray",
              "url": "https://demo.netbox.dev/api/extras/tags/24/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/10/",
          "virtualmachine_count": 0,
          "vlan_count": 3
        },
        {
          "asns": [],
          "circuit_count": 2,
          "comments": "",
          "created": "2020-12-19T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 4,
          "display": "DM-Stamford",
          "display_url": "https://demo.netbox.dev/dcim/sites/11/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 11,
          "last_updated": "2021-12-30T15:45:37.501000Z",
          "latitude": null,
          "longitude": null,
          "name": "DM-Stamford",
          "owner": null,
          "physical_address": "",
          "prefix_count": 5,
          "rack_count": 1,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "Connecticut",
            "id": 49,
            "name": "Connecticut",
            "site_count": 0,
            "slug": "us-ct",
            "url": "https://demo.netbox.dev/api/dcim/regions/49/"
          },
          "shipping_address": "",
          "slug": "dm-stamford",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "03a9f4",
              "display": "Juliett",
              "display_url": "https://demo.netbox.dev/extras/tags/10/",
              "id": 10,
              "name": "Juliett",
              "slug": "juliett",
              "url": "https://demo.netbox.dev/api/extras/tags/10/"
            },
            {
              "color": "8bc34a",
              "display": "Papa",
              "display_url": "https://demo.netbox.dev/extras/tags/16/",
              "id": 16,
              "name": "Papa",
              "slug": "papa",
              "url": "https://demo.netbox.dev/api/extras/tags/16/"
            },
            {
              "color": "9e9e9e",
              "display": "X-ray",
              "display_url": "https://demo.netbox.dev/extras/tags/24/",
              "id": 24,
              "name": "X-ray",
              "slug": "x-ray",
              "url": "https://demo.netbox.dev/api/extras/tags/24/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/11/",
          "virtualmachine_count": 0,
          "vlan_count": 3
        },
        {
          "asns": [],
          "circuit_count": 2,
          "comments": "",
          "created": "2020-12-19T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 4,
          "display": "DM-Syracuse",
          "display_url": "https://demo.netbox.dev/dcim/sites/12/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 12,
          "last_updated": "2021-12-30T15:45:37.513000Z",
          "latitude": null,
          "longitude": null,
          "name": "DM-Syracuse",
          "owner": null,
          "physical_address": "",
          "prefix_count": 5,
          "rack_count": 1,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "New York",
            "id": 43,
            "name": "New York",
            "site_count": 0,
            "slug": "us-ny",
            "url": "https://demo.netbox.dev/api/dcim/regions/43/"
          },
          "shipping_address": "",
          "slug": "dm-syracuse",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "2f6a31",
              "display": "November",
              "display_url": "https://demo.netbox.dev/extras/tags/14/",
              "id": 14,
              "name": "November",
              "slug": "november",
              "url": "https://demo.netbox.dev/api/extras/tags/14/"
            },
            {
              "color": "ff9800",
              "display": "Tango",
              "display_url": "https://demo.netbox.dev/extras/tags/20/",
              "id": 20,
              "name": "Tango",
              "slug": "tango",
              "url": "https://demo.netbox.dev/api/extras/tags/20/"
            },
            {
              "color": "607d8b",
              "display": "Yankee",
              "display_url": "https://demo.netbox.dev/extras/tags/25/",
              "id": 25,
              "name": "Yankee",
              "slug": "yankee",
              "url": "https://demo.netbox.dev/api/extras/tags/25/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/12/",
          "virtualmachine_count": 0,
          "vlan_count": 3
        },
        {
          "asns": [],
          "circuit_count": 2,
          "comments": "",
          "created": "2020-12-19T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 4,
          "display": "DM-Utica",
          "display_url": "https://demo.netbox.dev/dcim/sites/13/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 13,
          "last_updated": "2021-12-30T15:45:37.525000Z",
          "latitude": null,
          "longitude": null,
          "name": "DM-Utica",
          "owner": null,
          "physical_address": "",
          "prefix_count": 5,
          "rack_count": 1,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "New York",
            "id": 43,
            "name": "New York",
            "site_count": 0,
            "slug": "us-ny",
            "url": "https://demo.netbox.dev/api/dcim/regions/43/"
          },
          "shipping_address": "",
          "slug": "dm-utica",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "e91e63",
              "display": "Charlie",
              "display_url": "https://demo.netbox.dev/extras/tags/3/",
              "id": 3,
              "name": "Charlie",
              "slug": "charlie",
              "url": "https://demo.netbox.dev/api/extras/tags/3/"
            },
            {
              "color": "00ffff",
              "display": "Mike",
              "display_url": "https://demo.netbox.dev/extras/tags/13/",
              "id": 13,
              "name": "Mike",
              "slug": "mike",
              "url": "https://demo.netbox.dev/api/extras/tags/13/"
            },
            {
              "color": "8bc34a",
              "display": "Papa",
              "display_url": "https://demo.netbox.dev/extras/tags/16/",
              "id": 16,
              "name": "Papa",
              "slug": "papa",
              "url": "https://demo.netbox.dev/api/extras/tags/16/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/13/",
          "virtualmachine_count": 0,
          "vlan_count": 3
        },
        {
          "asns": [],
          "circuit_count": 2,
          "comments": "",
          "created": "2020-12-19T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 4,
          "display": "DM-Yonkers",
          "display_url": "https://demo.netbox.dev/dcim/sites/14/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 14,
          "last_updated": "2021-12-30T15:45:37.537000Z",
          "latitude": null,
          "longitude": null,
          "name": "DM-Yonkers",
          "owner": null,
          "physical_address": "",
          "prefix_count": 5,
          "rack_count": 1,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "New York",
            "id": 43,
            "name": "New York",
            "site_count": 0,
            "slug": "us-ny",
            "url": "https://demo.netbox.dev/api/dcim/regions/43/"
          },
          "shipping_address": "",
          "slug": "dm-yonkers",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "2196f3",
              "display": "India",
              "display_url": "https://demo.netbox.dev/extras/tags/9/",
              "id": 9,
              "name": "India",
              "slug": "india",
              "url": "https://demo.netbox.dev/api/extras/tags/9/"
            },
            {
              "color": "8bc34a",
              "display": "Papa",
              "display_url": "https://demo.netbox.dev/extras/tags/16/",
              "id": 16,
              "name": "Papa",
              "slug": "papa",
              "url": "https://demo.netbox.dev/api/extras/tags/16/"
            },
            {
              "color": "cddc39",
              "display": "Quebec",
              "display_url": "https://demo.netbox.dev/extras/tags/17/",
              "id": 17,
              "name": "Quebec",
              "slug": "quebec",
              "url": "https://demo.netbox.dev/api/extras/tags/17/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Dunder-Mifflin, Inc.",
            "id": 5,
            "name": "Dunder-Mifflin, Inc.",
            "slug": "dunder-mifflin",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/5/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/14/",
          "virtualmachine_count": 0,
          "vlan_count": 3
        },
        {
          "asns": [],
          "circuit_count": 0,
          "comments": "",
          "created": "2026-03-23T06:27:16.757174Z",
          "custom_fields": {},
          "description": "",
          "device_count": 0,
          "display": "ebj-pop",
          "display_url": "https://demo.netbox.dev/dcim/sites/25/",
          "facility": "",
          "group": null,
          "id": 25,
          "last_updated": "2026-03-23T06:27:16.757188Z",
          "latitude": null,
          "longitude": null,
          "name": "ebj-pop",
          "owner": null,
          "physical_address": "",
          "prefix_count": 0,
          "rack_count": 1,
          "region": {
            "_depth": 1,
            "description": "",
            "display": "Roysambu pop",
            "id": 83,
            "name": "Roysambu pop",
            "site_count": 0,
            "slug": "roysambu-pop",
            "url": "https://demo.netbox.dev/api/dcim/regions/83/"
          },
          "shipping_address": "",
          "slug": "ebj-pop",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": null,
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/25/",
          "virtualmachine_count": 0,
          "vlan_count": 0
        },
        {
          "asns": [],
          "circuit_count": 1,
          "comments": "",
          "created": "2021-04-02T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 2,
          "display": "Grinnells Lab",
          "display_url": "https://demo.netbox.dev/dcim/sites/23/",
          "facility": "GRL",
          "group": null,
          "id": 23,
          "last_updated": "2021-12-30T15:45:37.561000Z",
          "latitude": null,
          "longitude": null,
          "name": "Grinnells Lab",
          "owner": null,
          "physical_address": "3200 Faucette Dr., Raleigh, NC 27607",
          "prefix_count": 0,
          "rack_count": 1,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "North Carolina",
            "id": 40,
            "name": "North Carolina",
            "site_count": 0,
            "slug": "us-nc",
            "url": "https://demo.netbox.dev/api/dcim/regions/40/"
          },
          "shipping_address": "",
          "slug": "ncsu-118",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "ff66ff",
              "display": "Echo",
              "display_url": "https://demo.netbox.dev/extras/tags/5/",
              "id": 5,
              "name": "Echo",
              "slug": "echo",
              "url": "https://demo.netbox.dev/api/extras/tags/5/"
            },
            {
              "color": "009688",
              "display": "Lima",
              "display_url": "https://demo.netbox.dev/extras/tags/12/",
              "id": 12,
              "name": "Lima",
              "slug": "lima",
              "url": "https://demo.netbox.dev/api/extras/tags/12/"
            },
            {
              "color": "795548",
              "display": "Victor",
              "display_url": "https://demo.netbox.dev/extras/tags/22/",
              "id": 22,
              "name": "Victor",
              "slug": "victor",
              "url": "https://demo.netbox.dev/api/extras/tags/22/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "NC State University",
            "id": 13,
            "name": "NC State University",
            "slug": "nc-state",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/13/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/23/",
          "virtualmachine_count": 0,
          "vlan_count": 0
        },
        {
          "asns": [],
          "circuit_count": 0,
          "comments": "",
          "created": "2021-03-10T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 0,
          "display": "JBB Branch 104",
          "display_url": "https://demo.netbox.dev/dcim/sites/15/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 15,
          "last_updated": "2021-12-30T15:45:37.573000Z",
          "latitude": null,
          "longitude": null,
          "name": "JBB Branch 104",
          "owner": null,
          "physical_address": "7 Indian Spring Lane\r\nMenasha, WI 54952",
          "prefix_count": 0,
          "rack_count": 0,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "Wisconsin",
            "id": 33,
            "name": "Wisconsin",
            "site_count": 0,
            "slug": "us-wi",
            "url": "https://demo.netbox.dev/api/dcim/regions/33/"
          },
          "shipping_address": "",
          "slug": "jbb-branch-104",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "9c27b0",
              "display": "Foxtrot",
              "display_url": "https://demo.netbox.dev/extras/tags/6/",
              "id": 6,
              "name": "Foxtrot",
              "slug": "foxtrot",
              "url": "https://demo.netbox.dev/api/extras/tags/6/"
            },
            {
              "color": "ffc107",
              "display": "Sierra",
              "display_url": "https://demo.netbox.dev/extras/tags/19/",
              "id": 19,
              "name": "Sierra",
              "slug": "sierra",
              "url": "https://demo.netbox.dev/api/extras/tags/19/"
            },
            {
              "color": "ff9800",
              "display": "Tango",
              "display_url": "https://demo.netbox.dev/extras/tags/20/",
              "id": 20,
              "name": "Tango",
              "slug": "tango",
              "url": "https://demo.netbox.dev/api/extras/tags/20/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Jimbob's Banking & Trust",
            "id": 10,
            "name": "Jimbob's Banking & Trust",
            "slug": "jimbobs-banking-trust",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/10/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/15/",
          "virtualmachine_count": 0,
          "vlan_count": 4
        },
        {
          "asns": [],
          "circuit_count": 0,
          "comments": "",
          "created": "2021-03-10T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 0,
          "display": "JBB Branch 109",
          "display_url": "https://demo.netbox.dev/dcim/sites/16/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 16,
          "last_updated": "2021-12-30T15:45:37.585000Z",
          "latitude": null,
          "longitude": null,
          "name": "JBB Branch 109",
          "owner": null,
          "physical_address": "14 South Mill Pond Ave.\r\nAnnandale, VA 22003",
          "prefix_count": 0,
          "rack_count": 0,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "Virginia",
            "id": 64,
            "name": "Virginia",
            "site_count": 0,
            "slug": "us-va",
            "url": "https://demo.netbox.dev/api/dcim/regions/64/"
          },
          "shipping_address": "",
          "slug": "jbb-branch-109",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "03a9f4",
              "display": "Juliett",
              "display_url": "https://demo.netbox.dev/extras/tags/10/",
              "id": 10,
              "name": "Juliett",
              "slug": "juliett",
              "url": "https://demo.netbox.dev/api/extras/tags/10/"
            },
            {
              "color": "cddc39",
              "display": "Quebec",
              "display_url": "https://demo.netbox.dev/extras/tags/17/",
              "id": 17,
              "name": "Quebec",
              "slug": "quebec",
              "url": "https://demo.netbox.dev/api/extras/tags/17/"
            },
            {
              "color": "ff5722",
              "display": "Uniform",
              "display_url": "https://demo.netbox.dev/extras/tags/21/",
              "id": 21,
              "name": "Uniform",
              "slug": "uniform",
              "url": "https://demo.netbox.dev/api/extras/tags/21/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Jimbob's Banking & Trust",
            "id": 10,
            "name": "Jimbob's Banking & Trust",
            "slug": "jimbobs-banking-trust",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/10/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/16/",
          "virtualmachine_count": 0,
          "vlan_count": 4
        },
        {
          "asns": [],
          "circuit_count": 0,
          "comments": "",
          "created": "2021-03-10T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 0,
          "display": "JBB Branch 115",
          "display_url": "https://demo.netbox.dev/dcim/sites/17/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 17,
          "last_updated": "2021-12-30T15:45:37.597000Z",
          "latitude": null,
          "longitude": null,
          "name": "JBB Branch 115",
          "owner": null,
          "physical_address": "44 Blue Spring Dr.\r\nWest Warwick, RI 02893",
          "prefix_count": 0,
          "rack_count": 0,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "Rhode Island",
            "id": 44,
            "name": "Rhode Island",
            "site_count": 0,
            "slug": "us-ri",
            "url": "https://demo.netbox.dev/api/dcim/regions/44/"
          },
          "shipping_address": "",
          "slug": "jbb-branch-115",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "8bc34a",
              "display": "Papa",
              "display_url": "https://demo.netbox.dev/extras/tags/16/",
              "id": 16,
              "name": "Papa",
              "slug": "papa",
              "url": "https://demo.netbox.dev/api/extras/tags/16/"
            },
            {
              "color": "cddc39",
              "display": "Quebec",
              "display_url": "https://demo.netbox.dev/extras/tags/17/",
              "id": 17,
              "name": "Quebec",
              "slug": "quebec",
              "url": "https://demo.netbox.dev/api/extras/tags/17/"
            },
            {
              "color": "607d8b",
              "display": "Yankee",
              "display_url": "https://demo.netbox.dev/extras/tags/25/",
              "id": 25,
              "name": "Yankee",
              "slug": "yankee",
              "url": "https://demo.netbox.dev/api/extras/tags/25/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Jimbob's Banking & Trust",
            "id": 10,
            "name": "Jimbob's Banking & Trust",
            "slug": "jimbobs-banking-trust",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/10/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/17/",
          "virtualmachine_count": 0,
          "vlan_count": 4
        },
        {
          "asns": [],
          "circuit_count": 0,
          "comments": "",
          "created": "2021-03-10T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 0,
          "display": "JBB Branch 120",
          "display_url": "https://demo.netbox.dev/dcim/sites/18/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 18,
          "last_updated": "2021-12-30T15:45:37.609000Z",
          "latitude": null,
          "longitude": null,
          "name": "JBB Branch 120",
          "owner": null,
          "physical_address": "682 Marlborough Street\r\nHicksville, NY 11801",
          "prefix_count": 0,
          "rack_count": 0,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "New York",
            "id": 43,
            "name": "New York",
            "site_count": 0,
            "slug": "us-ny",
            "url": "https://demo.netbox.dev/api/dcim/regions/43/"
          },
          "shipping_address": "",
          "slug": "jbb-branch-120",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "03a9f4",
              "display": "Juliett",
              "display_url": "https://demo.netbox.dev/extras/tags/10/",
              "id": 10,
              "name": "Juliett",
              "slug": "juliett",
              "url": "https://demo.netbox.dev/api/extras/tags/10/"
            },
            {
              "color": "ffc107",
              "display": "Sierra",
              "display_url": "https://demo.netbox.dev/extras/tags/19/",
              "id": 19,
              "name": "Sierra",
              "slug": "sierra",
              "url": "https://demo.netbox.dev/api/extras/tags/19/"
            },
            {
              "color": "ff9800",
              "display": "Tango",
              "display_url": "https://demo.netbox.dev/extras/tags/20/",
              "id": 20,
              "name": "Tango",
              "slug": "tango",
              "url": "https://demo.netbox.dev/api/extras/tags/20/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Jimbob's Banking & Trust",
            "id": 10,
            "name": "Jimbob's Banking & Trust",
            "slug": "jimbobs-banking-trust",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/10/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/18/",
          "virtualmachine_count": 0,
          "vlan_count": 4
        },
        {
          "asns": [],
          "circuit_count": 0,
          "comments": "",
          "created": "2021-03-10T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 0,
          "display": "JBB Branch 127",
          "display_url": "https://demo.netbox.dev/dcim/sites/19/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 19,
          "last_updated": "2021-12-30T15:45:37.621000Z",
          "latitude": null,
          "longitude": null,
          "name": "JBB Branch 127",
          "owner": null,
          "physical_address": "7730 Summerhouse St.\r\nOrange Park, FL 32065",
          "prefix_count": 0,
          "rack_count": 0,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "Florida",
            "id": 35,
            "name": "Florida",
            "site_count": 0,
            "slug": "us-fl",
            "url": "https://demo.netbox.dev/api/dcim/regions/35/"
          },
          "shipping_address": "",
          "slug": "jbb-branch-127",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "f44336",
              "display": "Bravo",
              "display_url": "https://demo.netbox.dev/extras/tags/2/",
              "id": 2,
              "name": "Bravo",
              "slug": "bravo",
              "url": "https://demo.netbox.dev/api/extras/tags/2/"
            },
            {
              "color": "009688",
              "display": "Lima",
              "display_url": "https://demo.netbox.dev/extras/tags/12/",
              "id": 12,
              "name": "Lima",
              "slug": "lima",
              "url": "https://demo.netbox.dev/api/extras/tags/12/"
            },
            {
              "color": "111111",
              "display": "Zulu",
              "display_url": "https://demo.netbox.dev/extras/tags/26/",
              "id": 26,
              "name": "Zulu",
              "slug": "zulu",
              "url": "https://demo.netbox.dev/api/extras/tags/26/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Jimbob's Banking & Trust",
            "id": 10,
            "name": "Jimbob's Banking & Trust",
            "slug": "jimbobs-banking-trust",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/10/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/19/",
          "virtualmachine_count": 0,
          "vlan_count": 4
        },
        {
          "asns": [],
          "circuit_count": 0,
          "comments": "",
          "created": "2021-03-10T00:00:00Z",
          "custom_fields": {},
          "description": "",
          "device_count": 0,
          "display": "JBB Branch 133",
          "display_url": "https://demo.netbox.dev/dcim/sites/20/",
          "facility": "",
          "group": {
            "_depth": 1,
            "description": "",
            "display": "Branch Offices",
            "id": 2,
            "name": "Branch Offices",
            "site_count": 0,
            "slug": "branch-offices",
            "url": "https://demo.netbox.dev/api/dcim/site-groups/2/"
          },
          "id": 20,
          "last_updated": "2021-12-30T15:45:37.634000Z",
          "latitude": null,
          "longitude": null,
          "name": "JBB Branch 133",
          "owner": null,
          "physical_address": "1 Old Union Ave.\r\nTroy, NY 12180",
          "prefix_count": 0,
          "rack_count": 0,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "New York",
            "id": 43,
            "name": "New York",
            "site_count": 0,
            "slug": "us-ny",
            "url": "https://demo.netbox.dev/api/dcim/regions/43/"
          },
          "shipping_address": "",
          "slug": "jbb-branch-133",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "ff66ff",
              "display": "Echo",
              "display_url": "https://demo.netbox.dev/extras/tags/5/",
              "id": 5,
              "name": "Echo",
              "slug": "echo",
              "url": "https://demo.netbox.dev/api/extras/tags/5/"
            },
            {
              "color": "03a9f4",
              "display": "Juliett",
              "display_url": "https://demo.netbox.dev/extras/tags/10/",
              "id": 10,
              "name": "Juliett",
              "slug": "juliett",
              "url": "https://demo.netbox.dev/api/extras/tags/10/"
            },
            {
              "color": "00bcd4",
              "display": "Kilo",
              "display_url": "https://demo.netbox.dev/extras/tags/11/",
              "id": 11,
              "name": "Kilo",
              "slug": "kilo",
              "url": "https://demo.netbox.dev/api/extras/tags/11/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "Jimbob's Banking & Trust",
            "id": 10,
            "name": "Jimbob's Banking & Trust",
            "slug": "jimbobs-banking-trust",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/10/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/20/",
          "virtualmachine_count": 0,
          "vlan_count": 4
        },
        {
          "asns": [],
          "circuit_count": 3,
          "comments": "",
          "created": "2021-04-02T00:00:00Z",
          "custom_fields": {},
          "description": "Main Distribution Frame",
          "device_count": 15,
          "display": "MDF",
          "display_url": "https://demo.netbox.dev/dcim/sites/21/",
          "facility": "065",
          "group": null,
          "id": 21,
          "last_updated": "2021-12-30T15:45:37.647000Z",
          "latitude": null,
          "longitude": null,
          "name": "MDF",
          "owner": null,
          "physical_address": "401 Dan Allen Dr., Raleigh, NC 27607",
          "prefix_count": 0,
          "rack_count": 26,
          "region": {
            "_depth": 2,
            "description": "",
            "display": "North Carolina",
            "id": 40,
            "name": "North Carolina",
            "site_count": 0,
            "slug": "us-nc",
            "url": "https://demo.netbox.dev/api/dcim/regions/40/"
          },
          "shipping_address": "",
          "slug": "ncsu-065",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [
            {
              "color": "3f51b5",
              "display": "Hotel",
              "display_url": "https://demo.netbox.dev/extras/tags/8/",
              "id": 8,
              "name": "Hotel",
              "slug": "hotel",
              "url": "https://demo.netbox.dev/api/extras/tags/8/"
            },
            {
              "color": "cddc39",
              "display": "Quebec",
              "display_url": "https://demo.netbox.dev/extras/tags/17/",
              "id": 17,
              "name": "Quebec",
              "slug": "quebec",
              "url": "https://demo.netbox.dev/api/extras/tags/17/"
            },
            {
              "color": "111111",
              "display": "Zulu",
              "display_url": "https://demo.netbox.dev/extras/tags/26/",
              "id": 26,
              "name": "Zulu",
              "slug": "zulu",
              "url": "https://demo.netbox.dev/api/extras/tags/26/"
            }
          ],
          "tenant": {
            "description": "",
            "display": "NC State University",
            "id": 13,
            "name": "NC State University",
            "slug": "nc-state",
            "url": "https://demo.netbox.dev/api/tenancy/tenants/13/"
          },
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/21/",
          "virtualmachine_count": 0,
          "vlan_count": 0
        },
        {
          "asns": [],
          "circuit_count": 0,
          "comments": "",
          "created": "2026-03-23T18:44:34.432192Z",
          "custom_fields": {},
          "description": "",
          "device_count": 0,
          "display": "teST",
          "display_url": "https://demo.netbox.dev/dcim/sites/28/",
          "facility": "",
          "group": null,
          "id": 28,
          "last_updated": "2026-03-23T18:44:34.432207Z",
          "latitude": null,
          "longitude": null,
          "name": "teST",
          "owner": null,
          "physical_address": "",
          "prefix_count": 0,
          "rack_count": 0,
          "region": {
            "_depth": 1,
            "description": "",
            "display": "France",
            "id": 12,
            "name": "France",
            "site_count": 0,
            "slug": "fr",
            "url": "https://demo.netbox.dev/api/dcim/regions/12/"
          },
          "shipping_address": "",
          "slug": "test",
          "status": {
            "label": "Active",
            "value": "active"
          },
          "tags": [],
          "tenant": null,
          "time_zone": null,
          "url": "https://demo.netbox.dev/api/dcim/sites/28/",
          "virtualmachine_count": 0,
          "vlan_count": 0
        }
      ]
    }
    ```

=== ":material-file-document-outline: YAML Output"

    ```yaml
    count: 28
    next: null
    previous: null
    results:
    - asns: []
      circuit_count: 0
      comments: ''
      created: '2026-03-23T12:17:40.257743Z'
      custom_fields: {}
      description: ''
      device_count: 3
      display: Amsterdam-DC
      display_url: https://demo.netbox.dev/dcim/sites/26/
      facility: ''
      group: null
      id: 26
      last_updated: '2026-03-23T12:17:40.257756Z'
      latitude: null
      longitude: null
      name: Amsterdam-DC
      owner: null
      physical_address: ''
      prefix_count: 0
      rack_count: 1
      region: null
      shipping_address: ''
      slug: amsterdam-dc
      status:
        label: Active
        value: active
      tags: []
      tenant: null
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/26/
      virtualmachine_count: 0
      vlan_count: 0
    - asns: []
      circuit_count: 1
      comments: ''
      created: '2021-04-02T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 4
      display: Butler Communications
      display_url: https://demo.netbox.dev/dcim/sites/24/
      facility: BUT
      group: null
      id: 24
      last_updated: '2021-12-30T15:45:37.371000Z'
      latitude: null
      longitude: null
      name: Butler Communications
      owner: null
      physical_address: 3210 Faucette Dr., Raleigh, NC 27607
      prefix_count: 0
      rack_count: 1
      region:
        _depth: 2
        description: ''
        display: North Carolina
        id: 40
        name: North Carolina
        site_count: 0
        slug: us-nc
        url: https://demo.netbox.dev/api/dcim/regions/40/
      shipping_address: ''
      slug: ncsu-128
      status:
        label: Active
        value: active
      tags:
      - color: 673ab7
        display: Golf
        display_url: https://demo.netbox.dev/extras/tags/7/
        id: 7
        name: Golf
        slug: golf
        url: https://demo.netbox.dev/api/extras/tags/7/
      - color: 009688
        display: Lima
        display_url: https://demo.netbox.dev/extras/tags/12/
        id: 12
        name: Lima
        slug: lima
        url: https://demo.netbox.dev/api/extras/tags/12/
      - color: 9e9e9e
        display: X-ray
        display_url: https://demo.netbox.dev/extras/tags/24/
        id: 24
        name: X-ray
        slug: x-ray
        url: https://demo.netbox.dev/api/extras/tags/24/
      tenant:
        description: ''
        display: NC State University
        id: 13
        name: NC State University
        slug: nc-state
        url: https://demo.netbox.dev/api/tenancy/tenants/13/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/24/
      virtualmachine_count: 0
      vlan_count: 0
    - asns: []
      circuit_count: 1
      comments: ''
      created: '2021-04-02T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 2
      display: D. S. Weaver Labs
      display_url: https://demo.netbox.dev/dcim/sites/22/
      facility: DSW
      group: null
      id: 22
      last_updated: '2021-12-30T15:45:37.549000Z'
      latitude: null
      longitude: null
      name: D. S. Weaver Labs
      owner: null
      physical_address: 3110 Faucette Dr., Raleigh, NC 27607
      prefix_count: 0
      rack_count: 1
      region:
        _depth: 2
        description: ''
        display: North Carolina
        id: 40
        name: North Carolina
        site_count: 0
        slug: us-nc
        url: https://demo.netbox.dev/api/dcim/regions/40/
      shipping_address: ''
      slug: ncsu-117
      status:
        label: Active
        value: active
      tags:
      - color: cddc39
        display: Quebec
        display_url: https://demo.netbox.dev/extras/tags/17/
        id: 17
        name: Quebec
        slug: quebec
        url: https://demo.netbox.dev/api/extras/tags/17/
      - color: ff9800
        display: Tango
        display_url: https://demo.netbox.dev/extras/tags/20/
        id: 20
        name: Tango
        slug: tango
        url: https://demo.netbox.dev/api/extras/tags/20/
      - color: 9e9e9e
        display: X-ray
        display_url: https://demo.netbox.dev/extras/tags/24/
        id: 24
        name: X-ray
        slug: x-ray
        url: https://demo.netbox.dev/api/extras/tags/24/
      tenant:
        description: ''
        display: NC State University
        id: 13
        name: NC State University
        slug: nc-state
        url: https://demo.netbox.dev/api/tenancy/tenants/13/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/22/
      virtualmachine_count: 0
      vlan_count: 0
    - asns: []
      circuit_count: 0
      comments: 'Lab contact: John Doe, john.doe@telekom.de'
      created: '2026-03-23T12:52:33.147332Z'
      custom_fields: {}
      description: ''
      device_count: 0
      display: Demo site with contact
      display_url: https://demo.netbox.dev/dcim/sites/27/
      facility: ''
      group: null
      id: 27
      last_updated: '2026-03-23T12:52:33.147344Z'
      latitude: null
      longitude: null
      name: Demo site with contact
      owner: null
      physical_address: ''
      prefix_count: 0
      rack_count: 0
      region: null
      shipping_address: ''
      slug: demo-site-with-contact
      status:
        label: Active
        value: active
      tags:
      - color: ffe4e1
        display: Delta
        display_url: https://demo.netbox.dev/extras/tags/4/
        id: 4
        name: Delta
        slug: delta
        url: https://demo.netbox.dev/api/extras/tags/4/
      tenant: null
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/27/
      virtualmachine_count: 0
      vlan_count: 0
    - asns: []
      circuit_count: 2
      comments: ''
      created: '2020-12-19T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 5
      display: DM-Akron
      display_url: https://demo.netbox.dev/dcim/sites/2/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 2
      last_updated: '2021-12-30T15:45:37.384000Z'
      latitude: null
      longitude: null
      name: DM-Akron
      owner: null
      physical_address: ''
      prefix_count: 5
      rack_count: 2
      region:
        _depth: 2
        description: ''
        display: Ohio
        id: 51
        name: Ohio
        site_count: 0
        slug: us-oh
        url: https://demo.netbox.dev/api/dcim/regions/51/
      shipping_address: ''
      slug: dm-akron
      status:
        label: Active
        value: active
      tags:
      - color: aa1409
        display: Alpha
        display_url: https://demo.netbox.dev/extras/tags/1/
        id: 1
        name: Alpha
        slug: alpha
        url: https://demo.netbox.dev/api/extras/tags/1/
      - color: f44336
        display: Bravo
        display_url: https://demo.netbox.dev/extras/tags/2/
        id: 2
        name: Bravo
        slug: bravo
        url: https://demo.netbox.dev/api/extras/tags/2/
      - color: 673ab7
        display: Golf
        display_url: https://demo.netbox.dev/extras/tags/7/
        id: 7
        name: Golf
        slug: golf
        url: https://demo.netbox.dev/api/extras/tags/7/
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/2/
      virtualmachine_count: 0
      vlan_count: 3
    - asns: []
      circuit_count: 2
      comments: ''
      created: '2020-12-19T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 4
      display: DM-Albany
      display_url: https://demo.netbox.dev/dcim/sites/3/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 3
      last_updated: '2021-12-30T15:45:37.397000Z'
      latitude: null
      longitude: null
      name: DM-Albany
      owner: null
      physical_address: ''
      prefix_count: 5
      rack_count: 1
      region:
        _depth: 2
        description: ''
        display: New York
        id: 43
        name: New York
        site_count: 0
        slug: us-ny
        url: https://demo.netbox.dev/api/dcim/regions/43/
      shipping_address: ''
      slug: dm-albany
      status:
        label: Active
        value: active
      tags:
      - color: e91e63
        display: Charlie
        display_url: https://demo.netbox.dev/extras/tags/3/
        id: 3
        name: Charlie
        slug: charlie
        url: https://demo.netbox.dev/api/extras/tags/3/
      - color: 2f6a31
        display: November
        display_url: https://demo.netbox.dev/extras/tags/14/
        id: 14
        name: November
        slug: november
        url: https://demo.netbox.dev/api/extras/tags/14/
      - color: 8bc34a
        display: Papa
        display_url: https://demo.netbox.dev/extras/tags/16/
        id: 16
        name: Papa
        slug: papa
        url: https://demo.netbox.dev/api/extras/tags/16/
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/3/
      virtualmachine_count: 0
      vlan_count: 3
    - asns: []
      circuit_count: 2
      comments: ''
      created: '2020-12-19T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 4
      display: DM-Binghamton
      display_url: https://demo.netbox.dev/dcim/sites/4/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 4
      last_updated: '2021-12-30T15:45:37.409000Z'
      latitude: null
      longitude: null
      name: DM-Binghamton
      owner: null
      physical_address: ''
      prefix_count: 5
      rack_count: 1
      region:
        _depth: 2
        description: ''
        display: New York
        id: 43
        name: New York
        site_count: 0
        slug: us-ny
        url: https://demo.netbox.dev/api/dcim/regions/43/
      shipping_address: ''
      slug: dm-binghamton
      status:
        label: Active
        value: active
      tags:
      - color: 673ab7
        display: Golf
        display_url: https://demo.netbox.dev/extras/tags/7/
        id: 7
        name: Golf
        slug: golf
        url: https://demo.netbox.dev/api/extras/tags/7/
      - color: cddc39
        display: Quebec
        display_url: https://demo.netbox.dev/extras/tags/17/
        id: 17
        name: Quebec
        slug: quebec
        url: https://demo.netbox.dev/api/extras/tags/17/
      - color: ffeb3b
        display: Romeo
        display_url: https://demo.netbox.dev/extras/tags/18/
        id: 18
        name: Romeo
        slug: romeo
        url: https://demo.netbox.dev/api/extras/tags/18/
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/4/
      virtualmachine_count: 0
      vlan_count: 3
    - asns: []
      circuit_count: 2
      comments: ''
      created: '2020-12-19T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 4
      display: DM-Buffalo
      display_url: https://demo.netbox.dev/dcim/sites/5/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 5
      last_updated: '2021-12-30T15:45:37.422000Z'
      latitude: null
      longitude: null
      name: DM-Buffalo
      owner: null
      physical_address: ''
      prefix_count: 5
      rack_count: 1
      region:
        _depth: 2
        description: ''
        display: New York
        id: 43
        name: New York
        site_count: 0
        slug: us-ny
        url: https://demo.netbox.dev/api/dcim/regions/43/
      shipping_address: ''
      slug: dm-buffalo
      status:
        label: Active
        value: active
      tags:
      - color: ffe4e1
        display: Delta
        display_url: https://demo.netbox.dev/extras/tags/4/
        id: 4
        name: Delta
        slug: delta
        url: https://demo.netbox.dev/api/extras/tags/4/
      - color: ff66ff
        display: Echo
        display_url: https://demo.netbox.dev/extras/tags/5/
        id: 5
        name: Echo
        slug: echo
        url: https://demo.netbox.dev/api/extras/tags/5/
      - color: '111111'
        display: Zulu
        display_url: https://demo.netbox.dev/extras/tags/26/
        id: 26
        name: Zulu
        slug: zulu
        url: https://demo.netbox.dev/api/extras/tags/26/
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/5/
      virtualmachine_count: 0
      vlan_count: 3
    - asns: []
      circuit_count: 2
      comments: ''
      created: '2020-12-19T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 4
      display: DM-Camden
      display_url: https://demo.netbox.dev/dcim/sites/6/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 6
      last_updated: '2021-12-30T15:45:37.434000Z'
      latitude: null
      longitude: null
      name: DM-Camden
      owner: null
      physical_address: ''
      prefix_count: 5
      rack_count: 1
      region:
        _depth: 2
        description: ''
        display: New Jersey
        id: 38
        name: New Jersey
        site_count: 0
        slug: us-nj
        url: https://demo.netbox.dev/api/dcim/regions/38/
      shipping_address: ''
      slug: dm-camden
      status:
        label: Active
        value: active
      tags:
      - color: 03a9f4
        display: Juliett
        display_url: https://demo.netbox.dev/extras/tags/10/
        id: 10
        name: Juliett
        slug: juliett
        url: https://demo.netbox.dev/api/extras/tags/10/
      - color: 00bcd4
        display: Kilo
        display_url: https://demo.netbox.dev/extras/tags/11/
        id: 11
        name: Kilo
        slug: kilo
        url: https://demo.netbox.dev/api/extras/tags/11/
      - color: '111111'
        display: Zulu
        display_url: https://demo.netbox.dev/extras/tags/26/
        id: 26
        name: Zulu
        slug: zulu
        url: https://demo.netbox.dev/api/extras/tags/26/
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/6/
      virtualmachine_count: 0
      vlan_count: 3
    - asns: []
      circuit_count: 2
      comments: ''
      created: '2020-12-19T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 4
      display: DM-Nashua
      display_url: https://demo.netbox.dev/dcim/sites/7/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 7
      last_updated: '2021-12-30T15:45:37.445000Z'
      latitude: null
      longitude: null
      name: DM-Nashua
      owner: null
      physical_address: ''
      prefix_count: 5
      rack_count: 1
      region:
        _depth: 2
        description: ''
        display: New Hampshire
        id: 37
        name: New Hampshire
        site_count: 0
        slug: us-nh
        url: https://demo.netbox.dev/api/dcim/regions/37/
      shipping_address: ''
      slug: dm-nashua
      status:
        label: Active
        value: active
      tags:
      - color: ff66ff
        display: Echo
        display_url: https://demo.netbox.dev/extras/tags/5/
        id: 5
        name: Echo
        slug: echo
        url: https://demo.netbox.dev/api/extras/tags/5/
      - color: 2f6a31
        display: November
        display_url: https://demo.netbox.dev/extras/tags/14/
        id: 14
        name: November
        slug: november
        url: https://demo.netbox.dev/api/extras/tags/14/
      - color: '111111'
        display: Zulu
        display_url: https://demo.netbox.dev/extras/tags/26/
        id: 26
        name: Zulu
        slug: zulu
        url: https://demo.netbox.dev/api/extras/tags/26/
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/7/
      virtualmachine_count: 0
      vlan_count: 3
    - asns: []
      circuit_count: 0
      comments: ''
      created: '2020-12-19T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 0
      display: DM-NYC
      display_url: https://demo.netbox.dev/dcim/sites/1/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Headquarters
        id: 3
        name: Headquarters
        site_count: 0
        slug: headquarters
        url: https://demo.netbox.dev/api/dcim/site-groups/3/
      id: 1
      last_updated: '2021-12-30T15:45:37.458000Z'
      latitude: null
      longitude: null
      name: DM-NYC
      owner: null
      physical_address: ''
      prefix_count: 0
      rack_count: 0
      region:
        _depth: 2
        description: ''
        display: New York
        id: 43
        name: New York
        site_count: 0
        slug: us-ny
        url: https://demo.netbox.dev/api/dcim/regions/43/
      shipping_address: ''
      slug: dm-nyc
      status:
        label: Active
        value: active
      tags:
      - color: 4caf50
        display: Oscar
        display_url: https://demo.netbox.dev/extras/tags/15/
        id: 15
        name: Oscar
        slug: oscar
        url: https://demo.netbox.dev/api/extras/tags/15/
      - color: cddc39
        display: Quebec
        display_url: https://demo.netbox.dev/extras/tags/17/
        id: 17
        name: Quebec
        slug: quebec
        url: https://demo.netbox.dev/api/extras/tags/17/
      - color: '795548'
        display: Victor
        display_url: https://demo.netbox.dev/extras/tags/22/
        id: 22
        name: Victor
        slug: victor
        url: https://demo.netbox.dev/api/extras/tags/22/
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/1/
      virtualmachine_count: 0
      vlan_count: 0
    - asns: []
      circuit_count: 2
      comments: ''
      created: '2020-12-19T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 4
      display: DM-Pittsfield
      display_url: https://demo.netbox.dev/dcim/sites/8/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 8
      last_updated: '2021-12-30T15:46:40.331000Z'
      latitude: null
      longitude: null
      name: DM-Pittsfield
      owner: null
      physical_address: ''
      prefix_count: 5
      rack_count: 1
      region:
        _depth: 2
        description: ''
        display: Massachusetts
        id: 76
        name: Massachusetts
        site_count: 0
        slug: us-ma
        url: https://demo.netbox.dev/api/dcim/regions/76/
      shipping_address: ''
      slug: dm-pittsfield
      status:
        label: Active
        value: active
      tags:
      - color: ff66ff
        display: Echo
        display_url: https://demo.netbox.dev/extras/tags/5/
        id: 5
        name: Echo
        slug: echo
        url: https://demo.netbox.dev/api/extras/tags/5/
      - color: 03a9f4
        display: Juliett
        display_url: https://demo.netbox.dev/extras/tags/10/
        id: 10
        name: Juliett
        slug: juliett
        url: https://demo.netbox.dev/api/extras/tags/10/
      - color: ff9800
        display: Tango
        display_url: https://demo.netbox.dev/extras/tags/20/
        id: 20
        name: Tango
        slug: tango
        url: https://demo.netbox.dev/api/extras/tags/20/
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/8/
      virtualmachine_count: 0
      vlan_count: 3
    - asns: []
      circuit_count: 2
      comments: ''
      created: '2020-12-19T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 4
      display: DM-Rochester
      display_url: https://demo.netbox.dev/dcim/sites/9/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 9
      last_updated: '2021-12-30T15:45:37.477000Z'
      latitude: null
      longitude: null
      name: DM-Rochester
      owner: null
      physical_address: ''
      prefix_count: 5
      rack_count: 1
      region:
        _depth: 2
        description: ''
        display: New York
        id: 43
        name: New York
        site_count: 0
        slug: us-ny
        url: https://demo.netbox.dev/api/dcim/regions/43/
      shipping_address: ''
      slug: dm-rochester
      status:
        label: Active
        value: active
      tags:
      - color: ff66ff
        display: Echo
        display_url: https://demo.netbox.dev/extras/tags/5/
        id: 5
        name: Echo
        slug: echo
        url: https://demo.netbox.dev/api/extras/tags/5/
      - color: 9c27b0
        display: Foxtrot
        display_url: https://demo.netbox.dev/extras/tags/6/
        id: 6
        name: Foxtrot
        slug: foxtrot
        url: https://demo.netbox.dev/api/extras/tags/6/
      - color: cddc39
        display: Quebec
        display_url: https://demo.netbox.dev/extras/tags/17/
        id: 17
        name: Quebec
        slug: quebec
        url: https://demo.netbox.dev/api/extras/tags/17/
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/9/
      virtualmachine_count: 0
      vlan_count: 3
    - asns: []
      circuit_count: 2
      comments: ''
      created: '2020-12-19T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 4
      display: DM-Scranton
      display_url: https://demo.netbox.dev/dcim/sites/10/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 10
      last_updated: '2021-12-30T15:45:37.489000Z'
      latitude: null
      longitude: null
      name: DM-Scranton
      owner: null
      physical_address: ''
      prefix_count: 5
      rack_count: 1
      region:
        _depth: 2
        description: ''
        display: Pennsylvania
        id: 63
        name: Pennsylvania
        site_count: 0
        slug: us-pa
        url: https://demo.netbox.dev/api/dcim/regions/63/
      shipping_address: ''
      slug: dm-scranton
      status:
        label: Active
        value: active
      tags:
      - color: 673ab7
        display: Golf
        display_url: https://demo.netbox.dev/extras/tags/7/
        id: 7
        name: Golf
        slug: golf
        url: https://demo.netbox.dev/api/extras/tags/7/
      - color: 03a9f4
        display: Juliett
        display_url: https://demo.netbox.dev/extras/tags/10/
        id: 10
        name: Juliett
        slug: juliett
        url: https://demo.netbox.dev/api/extras/tags/10/
      - color: 9e9e9e
        display: X-ray
        display_url: https://demo.netbox.dev/extras/tags/24/
        id: 24
        name: X-ray
        slug: x-ray
        url: https://demo.netbox.dev/api/extras/tags/24/
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/10/
      virtualmachine_count: 0
      vlan_count: 3
    - asns: []
      circuit_count: 2
      comments: ''
      created: '2020-12-19T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 4
      display: DM-Stamford
      display_url: https://demo.netbox.dev/dcim/sites/11/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 11
      last_updated: '2021-12-30T15:45:37.501000Z'
      latitude: null
      longitude: null
      name: DM-Stamford
      owner: null
      physical_address: ''
      prefix_count: 5
      rack_count: 1
      region:
        _depth: 2
        description: ''
        display: Connecticut
        id: 49
        name: Connecticut
        site_count: 0
        slug: us-ct
        url: https://demo.netbox.dev/api/dcim/regions/49/
      shipping_address: ''
      slug: dm-stamford
      status:
        label: Active
        value: active
      tags:
      - color: 03a9f4
        display: Juliett
        display_url: https://demo.netbox.dev/extras/tags/10/
        id: 10
        name: Juliett
        slug: juliett
        url: https://demo.netbox.dev/api/extras/tags/10/
      - color: 8bc34a
        display: Papa
        display_url: https://demo.netbox.dev/extras/tags/16/
        id: 16
        name: Papa
        slug: papa
        url: https://demo.netbox.dev/api/extras/tags/16/
      - color: 9e9e9e
        display: X-ray
        display_url: https://demo.netbox.dev/extras/tags/24/
        id: 24
        name: X-ray
        slug: x-ray
        url: https://demo.netbox.dev/api/extras/tags/24/
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/11/
      virtualmachine_count: 0
      vlan_count: 3
    - asns: []
      circuit_count: 2
      comments: ''
      created: '2020-12-19T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 4
      display: DM-Syracuse
      display_url: https://demo.netbox.dev/dcim/sites/12/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 12
      last_updated: '2021-12-30T15:45:37.513000Z'
      latitude: null
      longitude: null
      name: DM-Syracuse
      owner: null
      physical_address: ''
      prefix_count: 5
      rack_count: 1
      region:
        _depth: 2
        description: ''
        display: New York
        id: 43
        name: New York
        site_count: 0
        slug: us-ny
        url: https://demo.netbox.dev/api/dcim/regions/43/
      shipping_address: ''
      slug: dm-syracuse
      status:
        label: Active
        value: active
      tags:
      - color: 2f6a31
        display: November
        display_url: https://demo.netbox.dev/extras/tags/14/
        id: 14
        name: November
        slug: november
        url: https://demo.netbox.dev/api/extras/tags/14/
      - color: ff9800
        display: Tango
        display_url: https://demo.netbox.dev/extras/tags/20/
        id: 20
        name: Tango
        slug: tango
        url: https://demo.netbox.dev/api/extras/tags/20/
      - color: 607d8b
        display: Yankee
        display_url: https://demo.netbox.dev/extras/tags/25/
        id: 25
        name: Yankee
        slug: yankee
        url: https://demo.netbox.dev/api/extras/tags/25/
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/12/
      virtualmachine_count: 0
      vlan_count: 3
    - asns: []
      circuit_count: 2
      comments: ''
      created: '2020-12-19T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 4
      display: DM-Utica
      display_url: https://demo.netbox.dev/dcim/sites/13/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 13
      last_updated: '2021-12-30T15:45:37.525000Z'
      latitude: null
      longitude: null
      name: DM-Utica
      owner: null
      physical_address: ''
      prefix_count: 5
      rack_count: 1
      region:
        _depth: 2
        description: ''
        display: New York
        id: 43
        name: New York
        site_count: 0
        slug: us-ny
        url: https://demo.netbox.dev/api/dcim/regions/43/
      shipping_address: ''
      slug: dm-utica
      status:
        label: Active
        value: active
      tags:
      - color: e91e63
        display: Charlie
        display_url: https://demo.netbox.dev/extras/tags/3/
        id: 3
        name: Charlie
        slug: charlie
        url: https://demo.netbox.dev/api/extras/tags/3/
      - color: 00ffff
        display: Mike
        display_url: https://demo.netbox.dev/extras/tags/13/
        id: 13
        name: Mike
        slug: mike
        url: https://demo.netbox.dev/api/extras/tags/13/
      - color: 8bc34a
        display: Papa
        display_url: https://demo.netbox.dev/extras/tags/16/
        id: 16
        name: Papa
        slug: papa
        url: https://demo.netbox.dev/api/extras/tags/16/
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/13/
      virtualmachine_count: 0
      vlan_count: 3
    - asns: []
      circuit_count: 2
      comments: ''
      created: '2020-12-19T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 4
      display: DM-Yonkers
      display_url: https://demo.netbox.dev/dcim/sites/14/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 14
      last_updated: '2021-12-30T15:45:37.537000Z'
      latitude: null
      longitude: null
      name: DM-Yonkers
      owner: null
      physical_address: ''
      prefix_count: 5
      rack_count: 1
      region:
        _depth: 2
        description: ''
        display: New York
        id: 43
        name: New York
        site_count: 0
        slug: us-ny
        url: https://demo.netbox.dev/api/dcim/regions/43/
      shipping_address: ''
      slug: dm-yonkers
      status:
        label: Active
        value: active
      tags:
      - color: 2196f3
        display: India
        display_url: https://demo.netbox.dev/extras/tags/9/
        id: 9
        name: India
        slug: india
        url: https://demo.netbox.dev/api/extras/tags/9/
      - color: 8bc34a
        display: Papa
        display_url: https://demo.netbox.dev/extras/tags/16/
        id: 16
        name: Papa
        slug: papa
        url: https://demo.netbox.dev/api/extras/tags/16/
      - color: cddc39
        display: Quebec
        display_url: https://demo.netbox.dev/extras/tags/17/
        id: 17
        name: Quebec
        slug: quebec
        url: https://demo.netbox.dev/api/extras/tags/17/
      tenant:
        description: ''
        display: Dunder-Mifflin, Inc.
        id: 5
        name: Dunder-Mifflin, Inc.
        slug: dunder-mifflin
        url: https://demo.netbox.dev/api/tenancy/tenants/5/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/14/
      virtualmachine_count: 0
      vlan_count: 3
    - asns: []
      circuit_count: 0
      comments: ''
      created: '2026-03-23T06:27:16.757174Z'
      custom_fields: {}
      description: ''
      device_count: 0
      display: ebj-pop
      display_url: https://demo.netbox.dev/dcim/sites/25/
      facility: ''
      group: null
      id: 25
      last_updated: '2026-03-23T06:27:16.757188Z'
      latitude: null
      longitude: null
      name: ebj-pop
      owner: null
      physical_address: ''
      prefix_count: 0
      rack_count: 1
      region:
        _depth: 1
        description: ''
        display: Roysambu pop
        id: 83
        name: Roysambu pop
        site_count: 0
        slug: roysambu-pop
        url: https://demo.netbox.dev/api/dcim/regions/83/
      shipping_address: ''
      slug: ebj-pop
      status:
        label: Active
        value: active
      tags: []
      tenant: null
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/25/
      virtualmachine_count: 0
      vlan_count: 0
    - asns: []
      circuit_count: 1
      comments: ''
      created: '2021-04-02T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 2
      display: Grinnells Lab
      display_url: https://demo.netbox.dev/dcim/sites/23/
      facility: GRL
      group: null
      id: 23
      last_updated: '2021-12-30T15:45:37.561000Z'
      latitude: null
      longitude: null
      name: Grinnells Lab
      owner: null
      physical_address: 3200 Faucette Dr., Raleigh, NC 27607
      prefix_count: 0
      rack_count: 1
      region:
        _depth: 2
        description: ''
        display: North Carolina
        id: 40
        name: North Carolina
        site_count: 0
        slug: us-nc
        url: https://demo.netbox.dev/api/dcim/regions/40/
      shipping_address: ''
      slug: ncsu-118
      status:
        label: Active
        value: active
      tags:
      - color: ff66ff
        display: Echo
        display_url: https://demo.netbox.dev/extras/tags/5/
        id: 5
        name: Echo
        slug: echo
        url: https://demo.netbox.dev/api/extras/tags/5/
      - color: 009688
        display: Lima
        display_url: https://demo.netbox.dev/extras/tags/12/
        id: 12
        name: Lima
        slug: lima
        url: https://demo.netbox.dev/api/extras/tags/12/
      - color: '795548'
        display: Victor
        display_url: https://demo.netbox.dev/extras/tags/22/
        id: 22
        name: Victor
        slug: victor
        url: https://demo.netbox.dev/api/extras/tags/22/
      tenant:
        description: ''
        display: NC State University
        id: 13
        name: NC State University
        slug: nc-state
        url: https://demo.netbox.dev/api/tenancy/tenants/13/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/23/
      virtualmachine_count: 0
      vlan_count: 0
    - asns: []
      circuit_count: 0
      comments: ''
      created: '2021-03-10T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 0
      display: JBB Branch 104
      display_url: https://demo.netbox.dev/dcim/sites/15/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 15
      last_updated: '2021-12-30T15:45:37.573000Z'
      latitude: null
      longitude: null
      name: JBB Branch 104
      owner: null
      physical_address: "7 Indian Spring Lane\r\nMenasha, WI 54952"
      prefix_count: 0
      rack_count: 0
      region:
        _depth: 2
        description: ''
        display: Wisconsin
        id: 33
        name: Wisconsin
        site_count: 0
        slug: us-wi
        url: https://demo.netbox.dev/api/dcim/regions/33/
      shipping_address: ''
      slug: jbb-branch-104
      status:
        label: Active
        value: active
      tags:
      - color: 9c27b0
        display: Foxtrot
        display_url: https://demo.netbox.dev/extras/tags/6/
        id: 6
        name: Foxtrot
        slug: foxtrot
        url: https://demo.netbox.dev/api/extras/tags/6/
      - color: ffc107
        display: Sierra
        display_url: https://demo.netbox.dev/extras/tags/19/
        id: 19
        name: Sierra
        slug: sierra
        url: https://demo.netbox.dev/api/extras/tags/19/
      - color: ff9800
        display: Tango
        display_url: https://demo.netbox.dev/extras/tags/20/
        id: 20
        name: Tango
        slug: tango
        url: https://demo.netbox.dev/api/extras/tags/20/
      tenant:
        description: ''
        display: Jimbob's Banking & Trust
        id: 10
        name: Jimbob's Banking & Trust
        slug: jimbobs-banking-trust
        url: https://demo.netbox.dev/api/tenancy/tenants/10/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/15/
      virtualmachine_count: 0
      vlan_count: 4
    - asns: []
      circuit_count: 0
      comments: ''
      created: '2021-03-10T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 0
      display: JBB Branch 109
      display_url: https://demo.netbox.dev/dcim/sites/16/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 16
      last_updated: '2021-12-30T15:45:37.585000Z'
      latitude: null
      longitude: null
      name: JBB Branch 109
      owner: null
      physical_address: "14 South Mill Pond Ave.\r\nAnnandale, VA 22003"
      prefix_count: 0
      rack_count: 0
      region:
        _depth: 2
        description: ''
        display: Virginia
        id: 64
        name: Virginia
        site_count: 0
        slug: us-va
        url: https://demo.netbox.dev/api/dcim/regions/64/
      shipping_address: ''
      slug: jbb-branch-109
      status:
        label: Active
        value: active
      tags:
      - color: 03a9f4
        display: Juliett
        display_url: https://demo.netbox.dev/extras/tags/10/
        id: 10
        name: Juliett
        slug: juliett
        url: https://demo.netbox.dev/api/extras/tags/10/
      - color: cddc39
        display: Quebec
        display_url: https://demo.netbox.dev/extras/tags/17/
        id: 17
        name: Quebec
        slug: quebec
        url: https://demo.netbox.dev/api/extras/tags/17/
      - color: ff5722
        display: Uniform
        display_url: https://demo.netbox.dev/extras/tags/21/
        id: 21
        name: Uniform
        slug: uniform
        url: https://demo.netbox.dev/api/extras/tags/21/
      tenant:
        description: ''
        display: Jimbob's Banking & Trust
        id: 10
        name: Jimbob's Banking & Trust
        slug: jimbobs-banking-trust
        url: https://demo.netbox.dev/api/tenancy/tenants/10/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/16/
      virtualmachine_count: 0
      vlan_count: 4
    - asns: []
      circuit_count: 0
      comments: ''
      created: '2021-03-10T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 0
      display: JBB Branch 115
      display_url: https://demo.netbox.dev/dcim/sites/17/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 17
      last_updated: '2021-12-30T15:45:37.597000Z'
      latitude: null
      longitude: null
      name: JBB Branch 115
      owner: null
      physical_address: "44 Blue Spring Dr.\r\nWest Warwick, RI 02893"
      prefix_count: 0
      rack_count: 0
      region:
        _depth: 2
        description: ''
        display: Rhode Island
        id: 44
        name: Rhode Island
        site_count: 0
        slug: us-ri
        url: https://demo.netbox.dev/api/dcim/regions/44/
      shipping_address: ''
      slug: jbb-branch-115
      status:
        label: Active
        value: active
      tags:
      - color: 8bc34a
        display: Papa
        display_url: https://demo.netbox.dev/extras/tags/16/
        id: 16
        name: Papa
        slug: papa
        url: https://demo.netbox.dev/api/extras/tags/16/
      - color: cddc39
        display: Quebec
        display_url: https://demo.netbox.dev/extras/tags/17/
        id: 17
        name: Quebec
        slug: quebec
        url: https://demo.netbox.dev/api/extras/tags/17/
      - color: 607d8b
        display: Yankee
        display_url: https://demo.netbox.dev/extras/tags/25/
        id: 25
        name: Yankee
        slug: yankee
        url: https://demo.netbox.dev/api/extras/tags/25/
      tenant:
        description: ''
        display: Jimbob's Banking & Trust
        id: 10
        name: Jimbob's Banking & Trust
        slug: jimbobs-banking-trust
        url: https://demo.netbox.dev/api/tenancy/tenants/10/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/17/
      virtualmachine_count: 0
      vlan_count: 4
    - asns: []
      circuit_count: 0
      comments: ''
      created: '2021-03-10T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 0
      display: JBB Branch 120
      display_url: https://demo.netbox.dev/dcim/sites/18/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 18
      last_updated: '2021-12-30T15:45:37.609000Z'
      latitude: null
      longitude: null
      name: JBB Branch 120
      owner: null
      physical_address: "682 Marlborough Street\r\nHicksville, NY 11801"
      prefix_count: 0
      rack_count: 0
      region:
        _depth: 2
        description: ''
        display: New York
        id: 43
        name: New York
        site_count: 0
        slug: us-ny
        url: https://demo.netbox.dev/api/dcim/regions/43/
      shipping_address: ''
      slug: jbb-branch-120
      status:
        label: Active
        value: active
      tags:
      - color: 03a9f4
        display: Juliett
        display_url: https://demo.netbox.dev/extras/tags/10/
        id: 10
        name: Juliett
        slug: juliett
        url: https://demo.netbox.dev/api/extras/tags/10/
      - color: ffc107
        display: Sierra
        display_url: https://demo.netbox.dev/extras/tags/19/
        id: 19
        name: Sierra
        slug: sierra
        url: https://demo.netbox.dev/api/extras/tags/19/
      - color: ff9800
        display: Tango
        display_url: https://demo.netbox.dev/extras/tags/20/
        id: 20
        name: Tango
        slug: tango
        url: https://demo.netbox.dev/api/extras/tags/20/
      tenant:
        description: ''
        display: Jimbob's Banking & Trust
        id: 10
        name: Jimbob's Banking & Trust
        slug: jimbobs-banking-trust
        url: https://demo.netbox.dev/api/tenancy/tenants/10/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/18/
      virtualmachine_count: 0
      vlan_count: 4
    - asns: []
      circuit_count: 0
      comments: ''
      created: '2021-03-10T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 0
      display: JBB Branch 127
      display_url: https://demo.netbox.dev/dcim/sites/19/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 19
      last_updated: '2021-12-30T15:45:37.621000Z'
      latitude: null
      longitude: null
      name: JBB Branch 127
      owner: null
      physical_address: "7730 Summerhouse St.\r\nOrange Park, FL 32065"
      prefix_count: 0
      rack_count: 0
      region:
        _depth: 2
        description: ''
        display: Florida
        id: 35
        name: Florida
        site_count: 0
        slug: us-fl
        url: https://demo.netbox.dev/api/dcim/regions/35/
      shipping_address: ''
      slug: jbb-branch-127
      status:
        label: Active
        value: active
      tags:
      - color: f44336
        display: Bravo
        display_url: https://demo.netbox.dev/extras/tags/2/
        id: 2
        name: Bravo
        slug: bravo
        url: https://demo.netbox.dev/api/extras/tags/2/
      - color: 009688
        display: Lima
        display_url: https://demo.netbox.dev/extras/tags/12/
        id: 12
        name: Lima
        slug: lima
        url: https://demo.netbox.dev/api/extras/tags/12/
      - color: '111111'
        display: Zulu
        display_url: https://demo.netbox.dev/extras/tags/26/
        id: 26
        name: Zulu
        slug: zulu
        url: https://demo.netbox.dev/api/extras/tags/26/
      tenant:
        description: ''
        display: Jimbob's Banking & Trust
        id: 10
        name: Jimbob's Banking & Trust
        slug: jimbobs-banking-trust
        url: https://demo.netbox.dev/api/tenancy/tenants/10/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/19/
      virtualmachine_count: 0
      vlan_count: 4
    - asns: []
      circuit_count: 0
      comments: ''
      created: '2021-03-10T00:00:00Z'
      custom_fields: {}
      description: ''
      device_count: 0
      display: JBB Branch 133
      display_url: https://demo.netbox.dev/dcim/sites/20/
      facility: ''
      group:
        _depth: 1
        description: ''
        display: Branch Offices
        id: 2
        name: Branch Offices
        site_count: 0
        slug: branch-offices
        url: https://demo.netbox.dev/api/dcim/site-groups/2/
      id: 20
      last_updated: '2021-12-30T15:45:37.634000Z'
      latitude: null
      longitude: null
      name: JBB Branch 133
      owner: null
      physical_address: "1 Old Union Ave.\r\nTroy, NY 12180"
      prefix_count: 0
      rack_count: 0
      region:
        _depth: 2
        description: ''
        display: New York
        id: 43
        name: New York
        site_count: 0
        slug: us-ny
        url: https://demo.netbox.dev/api/dcim/regions/43/
      shipping_address: ''
      slug: jbb-branch-133
      status:
        label: Active
        value: active
      tags:
      - color: ff66ff
        display: Echo
        display_url: https://demo.netbox.dev/extras/tags/5/
        id: 5
        name: Echo
        slug: echo
        url: https://demo.netbox.dev/api/extras/tags/5/
      - color: 03a9f4
        display: Juliett
        display_url: https://demo.netbox.dev/extras/tags/10/
        id: 10
        name: Juliett
        slug: juliett
        url: https://demo.netbox.dev/api/extras/tags/10/
      - color: 00bcd4
        display: Kilo
        display_url: https://demo.netbox.dev/extras/tags/11/
        id: 11
        name: Kilo
        slug: kilo
        url: https://demo.netbox.dev/api/extras/tags/11/
      tenant:
        description: ''
        display: Jimbob's Banking & Trust
        id: 10
        name: Jimbob's Banking & Trust
        slug: jimbobs-banking-trust
        url: https://demo.netbox.dev/api/tenancy/tenants/10/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/20/
      virtualmachine_count: 0
      vlan_count: 4
    - asns: []
      circuit_count: 3
      comments: ''
      created: '2021-04-02T00:00:00Z'
      custom_fields: {}
      description: Main Distribution Frame
      device_count: 15
      display: MDF
      display_url: https://demo.netbox.dev/dcim/sites/21/
      facility: '065'
      group: null
      id: 21
      last_updated: '2021-12-30T15:45:37.647000Z'
      latitude: null
      longitude: null
      name: MDF
      owner: null
      physical_address: 401 Dan Allen Dr., Raleigh, NC 27607
      prefix_count: 0
      rack_count: 26
      region:
        _depth: 2
        description: ''
        display: North Carolina
        id: 40
        name: North Carolina
        site_count: 0
        slug: us-nc
        url: https://demo.netbox.dev/api/dcim/regions/40/
      shipping_address: ''
      slug: ncsu-065
      status:
        label: Active
        value: active
      tags:
      - color: 3f51b5
        display: Hotel
        display_url: https://demo.netbox.dev/extras/tags/8/
        id: 8
        name: Hotel
        slug: hotel
        url: https://demo.netbox.dev/api/extras/tags/8/
      - color: cddc39
        display: Quebec
        display_url: https://demo.netbox.dev/extras/tags/17/
        id: 17
        name: Quebec
        slug: quebec
        url: https://demo.netbox.dev/api/extras/tags/17/
      - color: '111111'
        display: Zulu
        display_url: https://demo.netbox.dev/extras/tags/26/
        id: 26
        name: Zulu
        slug: zulu
        url: https://demo.netbox.dev/api/extras/tags/26/
      tenant:
        description: ''
        display: NC State University
        id: 13
        name: NC State University
        slug: nc-state
        url: https://demo.netbox.dev/api/tenancy/tenants/13/
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/21/
      virtualmachine_count: 0
      vlan_count: 0
    - asns: []
      circuit_count: 0
      comments: ''
      created: '2026-03-23T18:44:34.432192Z'
      custom_fields: {}
      description: ''
      device_count: 0
      display: teST
      display_url: https://demo.netbox.dev/dcim/sites/28/
      facility: ''
      group: null
      id: 28
      last_updated: '2026-03-23T18:44:34.432207Z'
      latitude: null
      longitude: null
      name: teST
      owner: null
      physical_address: ''
      prefix_count: 0
      rack_count: 0
      region:
        _depth: 1
        description: ''
        display: France
        id: 12
        name: France
        site_count: 0
        slug: fr
        url: https://demo.netbox.dev/api/dcim/regions/12/
      shipping_address: ''
      slug: test
      status:
        label: Active
        value: active
      tags: []
      tenant: null
      time_zone: null
      url: https://demo.netbox.dev/api/dcim/sites/28/
      virtualmachine_count: 0
      vlan_count: 0
    ```

=== ":material-language-markdown: Markdown Output"

    | ID | Name | Display | Status | Tenant |
    | --- | --- | --- | --- | --- |
    | 26 | Amsterdam-DC | Amsterdam-DC | {"label":"Active","value":"active"} | - |
    | 24 | Butler Communications | Butler Communications | {"label":"Active","value":"active"} | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
    | 22 | D. S. Weaver Labs | D. S. Weaver Labs | {"label":"Active","value":"active"} | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
    | 27 | Demo site with contact | Demo site with contact | {"label":"Active","value":"active"} | - |
    | 2 | DM-Akron | DM-Akron | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 3 | DM-Albany | DM-Albany | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 4 | DM-Binghamton | DM-Binghamton | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 5 | DM-Buffalo | DM-Buffalo | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 6 | DM-Camden | DM-Camden | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 7 | DM-Nashua | DM-Nashua | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 1 | DM-NYC | DM-NYC | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 8 | DM-Pittsfield | DM-Pittsfield | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 9 | DM-Rochester | DM-Rochester | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 10 | DM-Scranton | DM-Scranton | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 11 | DM-Stamford | DM-Stamford | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 12 | DM-Syracuse | DM-Syracuse | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 13 | DM-Utica | DM-Utica | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 14 | DM-Yonkers | DM-Yonkers | {"label":"Active","value":"active"} | {"description":"","display":"Dunder-Mifflin, Inc.","id":5,"name":"Dunder-Mifflin, Inc.","slug":"dunder-mifflin","url":"https://demo.netbox.dev/api/tenancy/tenants/5/"} |
    | 25 | ebj-pop | ebj-pop | {"label":"Active","value":"active"} | - |
    | 23 | Grinnells Lab | Grinnells Lab | {"label":"Active","value":"active"} | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
    | 15 | JBB Branch 104 | JBB Branch 104 | {"label":"Active","value":"active"} | {"description":"","display":"Jimbob's Banking & Trust","id":10,"name":"Jimbob's Banking & Trust","slug":"jimbobs-banking-trust","url":"https://demo.netbox.dev/api/tenancy/tenants/10/"} |
    | 16 | JBB Branch 109 | JBB Branch 109 | {"label":"Active","value":"active"} | {"description":"","display":"Jimbob's Banking & Trust","id":10,"name":"Jimbob's Banking & Trust","slug":"jimbobs-banking-trust","url":"https://demo.netbox.dev/api/tenancy/tenants/10/"} |
    | 17 | JBB Branch 115 | JBB Branch 115 | {"label":"Active","value":"active"} | {"description":"","display":"Jimbob's Banking & Trust","id":10,"name":"Jimbob's Banking & Trust","slug":"jimbobs-banking-trust","url":"https://demo.netbox.dev/api/tenancy/tenants/10/"} |
    | 18 | JBB Branch 120 | JBB Branch 120 | {"label":"Active","value":"active"} | {"description":"","display":"Jimbob's Banking & Trust","id":10,"name":"Jimbob's Banking & Trust","slug":"jimbobs-banking-trust","url":"https://demo.netbox.dev/api/tenancy/tenants/10/"} |
    | 19 | JBB Branch 127 | JBB Branch 127 | {"label":"Active","value":"active"} | {"description":"","display":"Jimbob's Banking & Trust","id":10,"name":"Jimbob's Banking & Trust","slug":"jimbobs-banking-trust","url":"https://demo.netbox.dev/api/tenancy/tenants/10/"} |
    | 20 | JBB Branch 133 | JBB Branch 133 | {"label":"Active","value":"active"} | {"description":"","display":"Jimbob's Banking & Trust","id":10,"name":"Jimbob's Banking & Trust","slug":"jimbobs-banking-trust","url":"https://demo.netbox.dev/api/tenancy/tenants/10/"} |
    | 21 | MDF | MDF | {"label":"Active","value":"active"} | {"description":"","display":"NC State University","id":13,"name":"NC State University","slug":"nc-state","url":"https://demo.netbox.dev/api/tenancy/tenants/13/"} |
    | 28 | teST | teST | {"label":"Active","value":"active"} | - |

<span class="nbx-badge nbx-badge--ok">exit&nbsp;0</span> <span class="nbx-badge nbx-badge--neutral">2.780s</span>

!!! warning "Truncated"
    Output was truncated. Full text is in `docs/generated/raw/`.

---
