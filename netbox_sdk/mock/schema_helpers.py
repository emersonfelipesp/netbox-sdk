"""Schema utilities for the NetBox mock API: $ref resolution, value generation."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from netbox_sdk.mock.netbox_fields import _seed_int, semantic_netbox_value


class RefResolver:
    """Resolves JSON Schema ``$ref`` references against OpenAPI ``components/schemas``.

    Handles:
    - Direct ``$ref``: ``{"$ref": "#/components/schemas/Site"}``
    - ``allOf`` with ``$ref`` branches
    - ``oneOf`` / ``anyOf`` — picks the first non-array variant
    - Nested ``$ref`` within resolved schemas

    All resolutions are cached to avoid repeated traversal of the 768-schema tree.
    """

    def __init__(self, components_schemas: dict[str, Any]) -> None:
        self._schemas = components_schemas
        self._cache: dict[str, dict[str, Any]] = {}

    def resolve(self, schema: dict[str, Any] | None) -> dict[str, Any]:
        """Return the resolved schema dict for *schema*, following ``$ref`` and compositions."""
        if not isinstance(schema, dict):
            return {}

        # Direct $ref
        ref = schema.get("$ref")
        if isinstance(ref, str):
            return self._resolve_ref(ref)

        # allOf: merge all branches into one flat schema
        all_of = schema.get("allOf")
        if isinstance(all_of, list) and all_of:
            merged: dict[str, Any] = {}
            for branch in all_of:
                resolved_branch = self.resolve(branch) if isinstance(branch, dict) else {}
                merged = _deep_merge(merged, resolved_branch)
            # Carry over nullable/description from outer schema
            for key in ("nullable", "description", "readOnly", "writeOnly"):
                if key in schema:
                    merged.setdefault(key, schema[key])
            return merged

        # oneOf / anyOf: prefer the first non-array, non-null branch
        for key in ("oneOf", "anyOf"):
            variants = schema.get(key)
            if isinstance(variants, list) and variants:
                preferred = self._pick_preferred_variant(variants)
                if preferred:
                    return self.resolve(preferred)

        return schema

    def resolve_property(self, prop_schema: dict[str, Any]) -> dict[str, Any]:
        """Resolve a property schema, preserving outer nullable/readOnly."""
        resolved = self.resolve(prop_schema)
        for key in ("nullable", "readOnly", "writeOnly", "description"):
            if key in prop_schema and key not in resolved:
                resolved = dict(resolved)
                resolved[key] = prop_schema[key]
        return resolved

    def _resolve_ref(self, ref: str) -> dict[str, Any]:
        """Resolve a ``#/components/schemas/{Name}`` reference, with caching."""
        if ref in self._cache:
            return self._cache[ref]

        prefix = "#/components/schemas/"
        if not ref.startswith(prefix):
            return {}

        name = ref[len(prefix) :]
        raw = self._schemas.get(name)
        if not isinstance(raw, dict):
            return {}

        # Placeholder to break cycles before recursing
        self._cache[ref] = {}
        resolved = self.resolve(raw)
        self._cache[ref] = resolved
        return resolved

    def _pick_preferred_variant(self, variants: list[Any]) -> dict[str, Any] | None:
        """Pick the most useful variant from a oneOf/anyOf list.

        Preference order: non-array object, first non-null variant, first variant.
        """
        # Prefer non-array object variants (avoid bulk array branch)
        for v in variants:
            if not isinstance(v, dict):
                continue
            resolved = self.resolve(v)
            if resolved.get("type") == "object" or "properties" in resolved:
                return v
        # Fallback: first non-null variant
        for v in variants:
            if isinstance(v, dict) and v.get("type") != "null":
                return v
        return variants[0] if variants else None


def schema_kind(schema: dict[str, Any] | None, resolver: RefResolver) -> str:
    """Classify a resolved schema into a storage kind.

    Returns:
        - ``"paginated_list"``: NetBox paginated envelope (count/next/previous/results)
        - ``"array"``: bare array type
        - ``"object"``: dict-like object
        - ``"scalar"``: primitive (string, integer, etc.)
        - ``"none"``: null / empty / void
    """
    resolved = resolver.resolve(schema) if schema else {}
    if not resolved:
        return "none"

    schema_type = resolved.get("type")

    # Detect NetBox paginated list: object with count + results
    if schema_type == "object":
        props = resolved.get("properties", {})
        if "count" in props and "results" in props:
            return "paginated_list"
        if props or "additionalProperties" in resolved:
            return "object"
        return "object"

    if schema_type == "array":
        return "array"

    if schema_type in ("string", "integer", "number", "boolean"):
        return "scalar"

    if schema_type is None and not resolved:
        return "none"

    return "object"


def extract_items_schema(
    paginated_schema: dict[str, Any],
    resolver: RefResolver,
) -> dict[str, Any] | None:
    """For a paginated list response schema, return the schema of a single result item."""
    resolved = resolver.resolve(paginated_schema)
    results_prop = resolved.get("properties", {}).get("results", {})
    if not isinstance(results_prop, dict):
        return None
    resolved_results = resolver.resolve(results_prop)
    items = resolved_results.get("items")
    if isinstance(items, dict):
        return resolver.resolve(items)
    return None


def sample_value_for_schema(
    schema: dict[str, Any] | None,
    *,
    resolver: RefResolver,
    seed: str,
    field_name: str | None = None,
    depth: int = 0,
    max_depth: int = 3,
) -> Any:
    """Generate a deterministic sample value for a JSON schema.

    Respects NetBox field semantics (names, slugs, IPs, MACs, etc.) and caps
    recursion depth at *max_depth* to avoid infinite loops on nested serializers.
    """
    if depth > max_depth:
        return None

    if schema is None:
        return None

    resolved = resolver.resolve(schema)
    if not resolved:
        return None

    # Check nullable first
    is_nullable = resolved.get("nullable", False)

    schema_type = resolved.get("type")

    # --- Semantic override ---
    semantic = semantic_netbox_value(field_name=field_name, seed=seed, schema=resolved)
    if semantic is not None:
        return semantic

    # --- Enum ---
    enum = resolved.get("enum")
    if isinstance(enum, list) and enum:
        # Prefer "active" for status-like fields
        if field_name and field_name.lower() in ("status", "type", "mode"):
            for preferred in ("active", "enabled", "online", "present"):
                if preferred in enum:
                    return preferred
        return enum[0]

    # --- Object with properties ---
    if schema_type == "object" or "properties" in resolved:
        props = resolved.get("properties", {})
        if not props:
            return {}
        result: dict[str, Any] = {}
        for prop_name, prop_schema in props.items():
            if not isinstance(prop_schema, dict):
                continue
            prop_resolved = resolver.resolve_property(prop_schema)
            # Skip writeOnly fields in responses
            if prop_resolved.get("writeOnly"):
                continue
            child_seed = f"{seed}_{prop_name}"
            value = sample_value_for_schema(
                prop_schema,
                resolver=resolver,
                seed=child_seed,
                field_name=prop_name,
                depth=depth + 1,
                max_depth=max_depth,
            )
            result[prop_name] = value
        return result

    # --- Array ---
    if schema_type == "array":
        items_schema = resolved.get("items")
        if not isinstance(items_schema, dict):
            return []
        child = sample_value_for_schema(
            items_schema,
            resolver=resolver,
            seed=f"{seed}_item0",
            field_name=field_name,
            depth=depth + 1,
            max_depth=max_depth,
        )
        return [child] if child is not None else []

    # --- Scalars ---
    if schema_type == "string":
        fmt = resolved.get("format", "")
        if fmt == "uri":
            idx = _seed_int(seed, modulus=9999, offset=1)
            return f"http://mock.example.com/api/mock/{idx}/"
        if fmt in ("date-time", "date"):
            return "2025-01-15T10:00:00Z" if fmt == "date-time" else "2025-01-15"
        if fmt == "ipv4":
            b = _seed_int(seed, modulus=200, offset=10)
            c = _seed_int(seed + "c", modulus=200, offset=10)
            return f"10.1.{b}.{c}"
        if fmt == "ipv6":
            return "2001:db8::1"
        idx = _seed_int(seed, modulus=99, offset=1)
        return f"mock-value-{idx}"

    if schema_type == "integer":
        return _seed_int(seed, modulus=9999, offset=1)

    if schema_type == "number":
        return round(_seed_int(seed, modulus=10000) / 100.0, 2)

    if schema_type == "boolean":
        return bool(_seed_int(seed, modulus=2))

    # Nullable fallback
    if is_nullable:
        return None

    return None


def merge_with_schema_defaults(
    schema: dict[str, Any] | None,
    *,
    resolver: RefResolver,
    seed: str,
    override: Any | None = None,
) -> Any:
    """Generate schema defaults and deep-merge *override* values on top."""
    base = sample_value_for_schema(schema, resolver=resolver, seed=seed)
    if override is None:
        return base
    return _deep_merge(base, override)


def schema_fingerprint(openapi_document: dict[str, Any]) -> str:
    """Return a stable SHA-256 fingerprint for a loaded OpenAPI document."""
    serialized = json.dumps(openapi_document, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _deep_merge(base: Any, override: Any) -> Any:
    """Recursively merge two values; override wins on conflicts."""
    if isinstance(base, dict) and isinstance(override, dict):
        merged = deepcopy(base)
        for key, value in override.items():
            if key in merged:
                merged[key] = _deep_merge(merged[key], value)
            else:
                merged[key] = deepcopy(value)
        return merged
    return deepcopy(override)


__all__ = [
    "RefResolver",
    "schema_kind",
    "extract_items_schema",
    "sample_value_for_schema",
    "merge_with_schema_defaults",
    "schema_fingerprint",
]
