"""Authoritative schema export (LABS-1.024): the schema of a live TypeDB database as TypeQL, JSON and a standalone
HTML explorer, with core/profile attribution by verified replay. See docs/schema-export/design.md."""

from .parse import SchemaExportError, SchemaParseError, facts, parse_schema, render_schema

__all__ = ["SchemaExportError", "SchemaParseError", "parse_schema", "render_schema", "facts"]
