"""Test helper utilities for database compatibility."""

import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import String, TypeDecorator
from sqlalchemy.ext.compiler import compiles


# Create SQLite-compatible versions of PostgreSQL types
class SqliteINET(TypeDecorator):
    """INET type that works in tests with SQLite."""

    impl = String(45)
    cache_ok = True


class SqliteUUID(TypeDecorator):
    """UUID type that works in tests with SQLite."""

    impl = String(36)
    cache_ok = True


def setup_sqlite_compatibility():
    """Setup SQLite to handle PostgreSQL types by replacing them."""

    # Compile INET as String for SQLite
    @compiles(pg.INET, "sqlite")
    def compile_inet_sqlite(type_, compiler, **kw):
        return "VARCHAR(45)"

    # Compile UUID as String for SQLite
    @compiles(pg.UUID, "sqlite")
    def compile_uuid_sqlite(type_, compiler, **kw):
        return "VARCHAR(36)"
