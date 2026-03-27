from pathlib import Path

OPENAPI_PATH = (
    Path(__file__).resolve().parent.parent
    / "netbox_sdk"
    / "reference"
    / "openapi"
    / "netbox-openapi.json"
)
