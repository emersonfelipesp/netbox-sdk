from pathlib import Path

OPENAPI_PATH = (
    Path(__file__).resolve().parent.parent
    / "netbox_cli"
    / "reference"
    / "openapi"
    / "netbox-openapi.json"
)
