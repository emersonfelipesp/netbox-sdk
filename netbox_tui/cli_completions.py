"""Command tree builder for the NbxCliTuiApp interactive CLI builder.

Provides :class:`CliCommandNode` (branch/leaf model) and
:func:`nbx_root_command_nodes` which builds the full navigation tree from a
:class:`~netbox_cli.schema.SchemaIndex`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from netbox_sdk.schema import SchemaIndex


class CliCommandNode(BaseModel):
    """One item in the CLI builder navigation menu.

    * **Branch**: ``children`` non-empty. Selecting the row appends
      ``enter_tail`` to the accumulated argv and shows ``children`` as the
      next level.
    * **Leaf**: ``children`` empty. Selecting the row fills the command input
      with the accumulated argv plus ``tail``.
    """

    model_config = ConfigDict(frozen=True)

    label: str
    description: str = ""
    children: tuple[CliCommandNode, ...] = Field(default_factory=tuple)
    # argv tokens appended when entering a branch
    enter_tail: tuple[str, ...] = Field(default_factory=tuple)
    # final argv tokens for a leaf command
    tail: tuple[str, ...] = Field(default_factory=tuple)
    # leaf metadata for input hints
    requires_id: bool = False
    allows_body: bool = False
    allows_query: bool = False

    @model_validator(mode="after")
    def _branch_or_leaf(self) -> CliCommandNode:
        if self.children and self.tail:
            raise ValueError(f"CliCommandNode {self.label!r}: cannot have both children and tail")
        if not self.children and not self.tail:
            raise ValueError(f"CliCommandNode {self.label!r}: must have either children or tail")
        return self


_ACTION_DESCRIPTIONS: dict[str, str] = {
    "list": "GET all objects",
    "get": "GET one by ID",
    "create": "POST — create new",
    "update": "PUT — full replace",
    "patch": "PATCH — partial update",
    "delete": "DELETE by ID",
}


def _supported_actions_for(group: str, resource: str, index: SchemaIndex) -> list[str]:
    """Return CLI action names for a group/resource derived from the schema."""
    rows = index.operations_for(group, resource)
    by_pair = {(item.path, item.method.upper()) for item in rows}
    paths = index.resource_paths(group, resource)
    if paths is None:
        return []

    actions: list[str] = []
    if paths.list_path and (paths.list_path, "GET") in by_pair:
        actions.append("list")
    if paths.detail_path and (paths.detail_path, "GET") in by_pair:
        actions.append("get")
    if paths.list_path and (paths.list_path, "POST") in by_pair:
        actions.append("create")
    if paths.detail_path and (paths.detail_path, "PUT") in by_pair:
        actions.append("update")
    if paths.detail_path and (paths.detail_path, "PATCH") in by_pair:
        actions.append("patch")
    if paths.detail_path and (paths.detail_path, "DELETE") in by_pair:
        actions.append("delete")
    return actions


def _action_leaf_nodes(group: str, resource: str, index: SchemaIndex) -> list[CliCommandNode]:
    nodes: list[CliCommandNode] = []
    for action in _supported_actions_for(group, resource, index):
        req_id = action in {"get", "update", "patch", "delete"}
        allow_body = action in {"create", "update", "patch"}
        allow_query = action == "list"
        desc = _ACTION_DESCRIPTIONS.get(action, action)
        hints: list[str] = []
        if req_id:
            hints.append("required: --id N")
        if allow_body:
            hints.append("payload: --body-json")
        if allow_query:
            hints.append("optional: -q key=value")
        suffix = f"  [{', '.join(hints)}]" if hints else ""
        nodes.append(
            CliCommandNode(
                label=action,
                description=f"{desc}{suffix}",
                tail=(action,),
                requires_id=req_id,
                allows_body=allow_body,
                allows_query=allow_query,
            )
        )
    return nodes


def _resource_branch_nodes(group: str, index: SchemaIndex) -> list[CliCommandNode]:
    nodes: list[CliCommandNode] = []
    for resource in index.resources(group):
        action_nodes = _action_leaf_nodes(group, resource, index)
        if not action_nodes:
            continue
        nodes.append(
            CliCommandNode(
                label=resource,
                description=f"/{group}/{resource}/",
                enter_tail=(resource,),
                children=tuple(action_nodes),
            )
        )
    return nodes


def _schema_group_nodes(index: SchemaIndex) -> list[CliCommandNode]:
    nodes: list[CliCommandNode] = []
    for group in index.groups():
        resource_nodes = _resource_branch_nodes(group, index)
        if not resource_nodes:
            continue
        nodes.append(
            CliCommandNode(
                label=group,
                description=f"API group · {len(resource_nodes)} resources",
                enter_tail=(group,),
                children=tuple(resource_nodes),
            )
        )
    return nodes


def _static_leaf_nodes() -> list[CliCommandNode]:
    """Static (non-dynamic) nbx commands available in the builder."""
    return [
        CliCommandNode(
            label="init",
            description="Configure NetBox connection interactively",
            tail=("init",),
        ),
        CliCommandNode(
            label="config",
            description="Show active profile configuration",
            tail=("config",),
        ),
        CliCommandNode(
            label="groups",
            description="List all API groups from the schema",
            tail=("groups",),
        ),
        CliCommandNode(
            label="logs",
            description="View structured application log entries",
            tail=("logs",),
        ),
        CliCommandNode(
            label="call",
            description="Raw HTTP call — edit to add METHOD PATH",
            tail=("call",),
            allows_body=True,
        ),
    ]


def nbx_root_command_nodes(index: SchemaIndex) -> list[CliCommandNode]:
    """Return all root-level command nodes (static leaves + schema group branches)."""
    return _static_leaf_nodes() + _schema_group_nodes(index)
