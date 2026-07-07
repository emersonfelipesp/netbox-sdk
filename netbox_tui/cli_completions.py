"""Command tree builder for the NbxCliTuiApp interactive CLI builder.

Provides :class:`CliCommandNode` (branch/leaf model) and
:func:`nbx_root_command_nodes` which builds the full navigation tree from a
:class:`~netbox_cli.schema.SchemaIndex`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from netbox_sdk.proxbox import ProxboxResourceSpec, proxbox_resources
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


def _proxbox_action_leaf_nodes(actions: tuple[str, ...]) -> list[CliCommandNode]:
    nodes: list[CliCommandNode] = []
    for action in actions:
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


def _proxbox_spec_for_path(command_path: tuple[str, ...]) -> ProxboxResourceSpec | None:
    for spec in proxbox_resources():
        if spec.command_parts == command_path:
            return spec
    return None


def _proxbox_child_parts(prefix: tuple[str, ...]) -> list[str]:
    prefix_len = len(prefix)
    return sorted(
        {
            spec.command_parts[prefix_len]
            for spec in proxbox_resources()
            if len(spec.command_parts) > prefix_len
            and spec.command_parts[:prefix_len] == prefix
        }
    )


def _proxbox_branch_node(
    command_path: tuple[str, ...],
    spec: ProxboxResourceSpec | None,
) -> CliCommandNode:
    children: list[CliCommandNode] = []
    for child_part in _proxbox_child_parts(command_path):
        child_path = (*command_path, child_part)
        children.append(_proxbox_branch_node(child_path, _proxbox_spec_for_path(child_path)))
    if spec is not None:
        children.extend(_proxbox_action_leaf_nodes(spec.supported_actions))

    label = command_path[-1]
    description = spec.description if spec is not None else f"Proxbox {' '.join(command_path)}"
    return CliCommandNode(
        label=label,
        description=description,
        enter_tail=(label,),
        children=tuple(children),
    )


def _proxbox_utility_nodes() -> list[CliCommandNode]:
    return [
        CliCommandNode(
            label="resources",
            description="List the dedicated Proxbox resource catalog",
            tail=("resources",),
        ),
        CliCommandNode(
            label="ops",
            description="Show operations for one Proxbox catalog resource",
            tail=("ops",),
        ),
        CliCommandNode(
            label="sync",
            description="Schedule a Proxbox sync job and stream progress",
            tail=("sync",),
        ),
        CliCommandNode(
            label="sync-types",
            description="List Proxbox sync type slugs",
            tail=("sync-types",),
        ),
        CliCommandNode(
            label="tui",
            description="Launch the Proxbox request workbench",
            tail=("tui",),
        ),
    ]


def _proxbox_root_nodes() -> list[CliCommandNode]:
    children = _proxbox_utility_nodes()
    for child_part in _proxbox_child_parts(()):
        command_path = (child_part,)
        children.append(_proxbox_branch_node(command_path, _proxbox_spec_for_path(command_path)))
    return [
        CliCommandNode(
            label="proxbox",
            description="Dedicated netbox-proxbox CRUD, sync, and TUI commands",
            enter_tail=("proxbox",),
            children=tuple(children),
        )
    ]


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
    return _static_leaf_nodes() + _proxbox_root_nodes() + _schema_group_nodes(index)
