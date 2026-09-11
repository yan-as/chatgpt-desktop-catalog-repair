from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .constants import DEFAULT_BACKUP_DIRNAME
from .database import CatalogError, connect_readonly


def default_backup_directory(database: Path) -> Path:
    return database.parent / DEFAULT_BACKUP_DIRNAME


def create_backup(database: Path, backup_directory: Path | None = None) -> Path:
    """Create a consistent SQLite backup, including data still represented by WAL."""
    destination_dir = backup_directory or default_backup_directory(database)
    destination_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")
    destination = destination_dir / f"{database.stem}-{stamp}.db"
    suffix = 1
    while destination.exists():
        destination = destination_dir / f"{database.stem}-{stamp}-{suffix}.db"
        suffix += 1

    try:
        with connect_readonly(database) as source, sqlite3.connect(destination) as target:
            source.backup(target)
    except sqlite3.Error as error:
        destination.unlink(missing_ok=True)
        raise CatalogError(f"Could not back up database: {error}") from error
    return destination


def retain_backups(backup_directory: Path, keep: int) -> list[Path]:
    if keep < 1:
        raise CatalogError("Backup retention must be at least 1.")
    backups = sorted(backup_directory.glob("*.db"), key=lambda path: path.stat().st_mtime, reverse=True)
    removed = backups[keep:]
    for backup in removed:
        backup.unlink()
    return removed
