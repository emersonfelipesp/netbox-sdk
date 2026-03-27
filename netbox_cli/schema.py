"""Re-exports from sdk.schema — real implementation lives in the sdk package."""

from sdk.schema import (
    _FILTER_EXCLUDE_NAMES,
    _LOOKUP_SUFFIXES,
    HTTP_METHODS,
    FilterParam,
    Operation,
    ResourcePaths,
    SchemaIndex,
    build_schema_index,
    load_openapi_schema,
    parse_group_resource,
)

__all__ = [
    "HTTP_METHODS",
    "FilterParam",
    "Operation",
    "ResourcePaths",
    "SchemaIndex",
    "_FILTER_EXCLUDE_NAMES",
    "_LOOKUP_SUFFIXES",
    "build_schema_index",
    "load_openapi_schema",
    "parse_group_resource",
]
