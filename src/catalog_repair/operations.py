from __future__ import annotations

import shutil
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .backup import create_backup, retain_backups
from .constants import CATALOG_TABLES, HOST_ID_COLUMNS, THREAD_ID_COLUMNS
from .database import (
    CatalogError,
    connect_readonly,
    connect_writable,
    integrity_check,
    require_healthy,
    table_columns,
    table_names,
)


@dataclass(frozen=True)
class Inspection:
    database: Path
    integrity: str
    tables: dict[str, int]
    catalog_tables_present: tuple[str, ...]


def inspect(database: Path) -> Inspection:
    with connect_readonly(database) as connection:
        names = table_names(connection)
        counts = {
            table: int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
            for table in sorted(names)
        }
        present = tuple(table for table in CATALOG_TABLES if table in names)
    return Inspection(database, integrity_check(database), counts, present)


def _backup_before_write(database: Path, backup_directory: Path | None, keep_backups: int) -> Path:
    require_healthy(database)
    backup = create_backup(database, backup_directory)
    retain_backups(backup.parent, keep_backups)
    return backup


def targeted_repair(
    database: Path,
    thread_id: str,
    host_id: str | None = None,
    backup_directory: Path | None = None,
    keep_backups: int = 3,
) -> tuple[Path, dict[str, int]]:
    """Remove only rows that explicitly contain the provided thread identifier."""
    if not thread_id.strip():
        raise CatalogError("A non-empty thread ID is required.")
    backup = _backup_before_write(database, backup_directory, keep_backups)
    deleted: dict[str, int] = {}
    try:
        with connect_writable(database) as connection:
            for table in CATALOG_TABLES:
                if table not in table_names(connection):
                    continue
                columns = table_columns(connection, table)
                thread_column = next((column for column in THREAD_ID_COLUMNS if column in columns), None)
                if not thread_column:
                    continue
                query = f'DELETE FROM "{table}" WHERE "{thread_column}" = ?'
                parameters: list[str] = [thread_id]
                if host_id:
                    host_column = next((column for column in HOST_ID_COLUMNS if column in columns), None)
                    if host_column:
                        query += f' AND "{host_column}" = ?'
                        parameters.append(host_id)
                cursor = connection.execute(query, parameters)
                if cursor.rowcount:
                    deleted[table] = cursor.rowcount
    except sqlite3.Error as error:
        raise CatalogError(f"Targeted repair failed; backup remains at {backup}: {error}") from error
    return backup, deleted


def full_rebuild(
    database: Path, backup_directory: Path | None = None, keep_backups: int = 3
) -> tuple[Path, dict[str, int]]:
    """Clear only the known local catalog cache tables, then let Desktop re-sync."""
    backup = _backup_before_write(database, backup_directory, keep_backups)
    cleared: dict[str, int] = {}
    try:
        with connect_writable(database) as connection:
            names = table_names(connection)
            for table in CATALOG_TABLES:
                if table not in names:
                    continue
                count = int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
                connection.execute(f'DELETE FROM "{table}"')
                cleared[table] = count
    except sqlite3.Error as error:
        raise CatalogError(f"Full rebuild failed; backup remains at {backup}: {error}") from error
    return backup, cleared


def restore(database: Path, backup: Path) -> None:
    if not backup.is_file():
        raise CatalogError(f"Backup does not exist: {backup}")
    require_healthy(backup)
    # Replacement is deliberate and occurs only after the source backup validates.
    shutil.copy2(backup, database)
