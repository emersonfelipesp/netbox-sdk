# netbox-cli aims to be a TUI mirror of NetBox UI.
- You must "mirror" UI, such as navigation, cards, etc.
- For it, you must understand NetBox code and Django (mainly focusing on template understanding)
- All actions a user can do on NetBox UI or API, must also be able to do on TUI.

## NetBox Conneciton
- The NetBox connection must be only API-based, without ever touching NetBox Models directly or other any other way to get info from it.
- You must not implement pynetbox lib on this project or any other NetBox lib/SDK, use `aiohttp` instead with full async supports.
- For API construction, you can always check NetBox OpenAPI schema at `./reference/openapi/netbox-openapi.json` or `./reference/openapi/netbox-openapi.yaml`

## How create the TUI:
- Use `Textual` project. Reference for it can be found at `./reference/textual`
- Although I want to focus on TUI, the `netbox-cli` project must also support bash/terminal direct commands, using normal arguments such as `nbx dcim devices get --id 1`
- Both TUI and CLI must be interchangeable, everything must work on both scenarios, let to user choice its preference.
