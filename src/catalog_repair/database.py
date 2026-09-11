from __future__ import annotations

import sqlite3
from pathlib import Path


class CatalogError(RuntimeError):
    """A precondition for a catalog operation was not met."""


def connect_readonly(database: Path) -> sqlite3.Connection:
    if not database.is_file():
        raise CatalogError(f"Database does not exist: {database}")
    return sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True)


def connect_writable(database: Path) -> sqlite3.Connection:
    if not database.is_file():
        raise CatalogError(f"Database does not exist: {database}")
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )
    }


def table_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    # table only comes from sqlite_master or the fixed catalog allow-list.
    return {row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')}


def integrity_check(database: Path) -> str:
    with connect_readonly(database) as connection:
        return str(connection.execute("PRAGMA integrity_check").fetchone()[0])


def require_healthy(database: Path) -> None:
    result = integrity_check(database)
    if result.lower() != "ok":
        raise CatalogError(f"SQLite integrity check failed: {result}")
