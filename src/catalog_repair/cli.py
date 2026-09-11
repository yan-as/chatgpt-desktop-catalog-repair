from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .constants import DEFAULT_DATABASE
from .database import CatalogError
from .operations import full_rebuild, inspect, restore, targeted_repair


def _path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="catalog-repair", description="Repair a local Desktop conversation catalog safely.")
    parser.add_argument("--database", type=_path, default=DEFAULT_DATABASE, help="Path to codex-dev.db.")
    parser.add_argument("--backup-dir", type=_path, help="Directory for SQLite backups.")
    parser.add_argument("--keep-backups", type=int, default=3, help="Number of backups to retain (default: 3).")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inspect", help="Read-only integrity and catalog inspection.")
    target = sub.add_parser("targeted-repair", help="Delete rows matching one explicit thread ID.")
    target.add_argument("--thread-id", required=True)
    target.add_argument("--host-id")
    rebuild = sub.add_parser("rebuild", help="Clear the known local catalog cache tables.")
    rebuild.add_argument("--stop-app", action="store_true", help="Stop ChatGPT/Codex processes before repair.")
    restore_cmd = sub.add_parser("restore", help="Replace the database from a validated backup.")
    restore_cmd.add_argument("--backup", type=_path, required=True)
    for command in (target, rebuild, restore_cmd):
        command.add_argument("--apply", action="store_true", help="Permit a database mutation.")
        command.add_argument("--yes", action="store_true", help="Confirm the requested mutation.")
    return parser


def _require_apply(args: argparse.Namespace) -> None:
    if not args.apply or not args.yes:
        raise CatalogError("This operation changes data. Re-run with both --apply and --yes.")


def _stop_desktop() -> None:
    if sys.platform != "win32":
        raise CatalogError("--stop-app is currently supported on Windows only.")
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Process ChatGPT,Codex -ErrorAction SilentlyContinue | Stop-Process -Force"],
        check=True,
    )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "inspect":
            report = inspect(args.database)
            print(json.dumps({"database": str(report.database), "integrity": report.integrity, "catalog_tables": report.catalog_tables_present, "tables": report.tables}, indent=2))
        elif args.command == "targeted-repair":
            _require_apply(args)
            backup, deleted = targeted_repair(args.database, args.thread_id, args.host_id, args.backup_dir, args.keep_backups)
            print(json.dumps({"backup": str(backup), "deleted": deleted}, indent=2))
        elif args.command == "rebuild":
            _require_apply(args)
            if args.stop_app:
                _stop_desktop()
            backup, cleared = full_rebuild(args.database, args.backup_dir, args.keep_backups)
            print(json.dumps({"backup": str(backup), "cleared": cleared}, indent=2))
        else:
            _require_apply(args)
            restore(args.database, args.backup)
            print(f"Restored {args.database} from {args.backup}")
    except (CatalogError, OSError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
