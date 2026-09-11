import sqlite3
from pathlib import Path

from catalog_repair.constants import CATALOG_TABLES
from catalog_repair.operations import full_rebuild, inspect, targeted_repair


def make_database(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE local_thread_catalog (thread_id TEXT, host_id TEXT, title TEXT)")
        connection.execute("CREATE TABLE local_thread_catalog_metadata (thread_id TEXT, host_id TEXT)")
        connection.execute("CREATE TABLE unrelated_state (value TEXT)")
        connection.executemany(
            "INSERT INTO local_thread_catalog VALUES (?, ?, ?)",
            [("ghost", "host-a", "Old chat"), ("keep", "host-a", "Current chat")],
        )
        connection.execute("INSERT INTO local_thread_catalog_metadata VALUES ('ghost', 'host-a')")
        connection.execute("INSERT INTO unrelated_state VALUES ('preserve me')")


def scalar(path: Path, statement: str) -> int | str:
    with sqlite3.connect(path) as connection:
        return connection.execute(statement).fetchone()[0]


def test_inspect_is_read_only(tmp_path: Path) -> None:
    database = tmp_path / "codex-dev.db"
    make_database(database)
    report = inspect(database)
    assert report.integrity == "ok"
    assert report.tables["local_thread_catalog"] == 2
    assert scalar(database, "SELECT COUNT(*) FROM local_thread_catalog") == 2


def test_targeted_repair_only_removes_explicit_thread(tmp_path: Path) -> None:
    database = tmp_path / "codex-dev.db"
    backups = tmp_path / "backups"
    make_database(database)
    backup, deleted = targeted_repair(database, "ghost", "host-a", backups)
    assert backup.is_file()
    assert deleted == {"local_thread_catalog": 1, "local_thread_catalog_metadata": 1}
    assert scalar(database, "SELECT COUNT(*) FROM local_thread_catalog") == 1
    assert scalar(database, "SELECT COUNT(*) FROM unrelated_state") == 1


def test_rebuild_only_clears_known_catalog_tables(tmp_path: Path) -> None:
    database = tmp_path / "codex-dev.db"
    make_database(database)
    _, cleared = full_rebuild(database, tmp_path / "backups")
    assert cleared["local_thread_catalog"] == 2
    assert scalar(database, "SELECT COUNT(*) FROM local_thread_catalog") == 0
    assert scalar(database, "SELECT COUNT(*) FROM unrelated_state") == 1
    assert "unrelated_state" not in CATALOG_TABLES
