from __future__ import annotations

from pathlib import Path

DEFAULT_DATABASE = Path.home() / ".codex" / "sqlite" / "codex-dev.db"
DEFAULT_BACKUP_DIRNAME = "chatgpt-catalog-backups"

# These table names were observed in the Windows desktop catalog. Rebuild never
# touches a table outside this allow-list, even if a future database adds one.
CATALOG_TABLES = (
    "local_thread_catalog",
    "local_thread_catalog_hosts",
    "local_thread_catalog_metadata",
    "local_thread_catalog_sync_state",
    "local_thread_catalog_scan_checkpoints",
    "local_thread_catalog_scan_entries",
)

THREAD_ID_COLUMNS = ("thread_id", "id")
HOST_ID_COLUMNS = ("host_id",)
WINDOWS_APP_ID = "OpenAI.Codex_2p2nqsd0c76g0!App"
