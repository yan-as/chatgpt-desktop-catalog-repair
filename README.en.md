# ChatGPT Desktop Catalog Repair

A small tool for inspecting and repairing the local conversation catalog used by ChatGPT and Codex Desktop.

[简体中文](README.md)

## What it does

The Desktop app can occasionally get its local catalog out of sync: a conversation you already deleted still shows in the sidebar, or the sidebar no longer matches the cloud. This tool inspects and repairs that local state.

What it does **not** do:

- It cannot recover conversations deleted on the server; once deleted there, they are gone.
- It does not contact OpenAI or require your account credentials.
- By default it only inspects and changes nothing.

## Read this first

- This is an **unofficial** community tool, not an OpenAI product.
- The Desktop local database schema is not a public compatibility contract and can change between versions.
- Any command that changes data requires both `--apply --yes`, and always creates a backup first.
- Backups can contain private conversation metadata. Do not upload them anywhere public (GitHub, issues, etc.).
- Close the Desktop app before repairing, then reopen it afterwards and wait for sync.

## Install (Windows)

Requires Python 3.10 or newer; the optional launcher requires PowerShell 7.

```powershell
git clone https://github.com/yan-as/chatgpt-desktop-catalog-repair.git
cd chatgpt-desktop-catalog-repair
py -m pip install .
```

Run a read-only check to confirm everything works (this changes nothing):

```powershell
catalog-repair inspect
```

## Usage

| I want to | Command | Changes data? |
| --- | --- | --- |
| Check catalog state | `inspect` | No, read-only |
| Delete one specific conversation | `targeted-repair` | Yes |
| Rebuild the local catalog after large-scale drift | `rebuild` | Yes |
| Restore from a backup | `restore` | Yes |

The default database is `%USERPROFILE%\.codex\sqlite\codex-dev.db`. Use `--database` to point elsewhere; the tool never scans your drives.

### 1. Read-only inspection (recommended first)

```powershell
catalog-repair inspect
```

The output is JSON. `"integrity": "ok"` means the database itself is healthy; the rest is informational.

### 2. Delete a specific "ghost" conversation

Use only when you already have the exact `thread-id`; optionally add `--host-id` to narrow to a device:

```powershell
catalog-repair targeted-repair --thread-id "thread_xxx" --host-id "host_yyy" --apply --yes
```

It never guesses from a title, a 404, or a failed sync; you supply the exact ID. A wrong ID deletes nothing. It creates a backup first, then reports which rows were removed.

### 3. Large-scale drift: rebuild the local catalog

For a stale sidebar, no reliable ID, or when targeted repair did not help. It only clears local cache tables and then lets Desktop re-sync; other data is untouched:

```powershell
catalog-repair rebuild --apply --yes --stop-app
```

`--stop-app` stops the `ChatGPT` and `Codex` processes before writing. Reopen the app afterwards and wait for sync.

### 4. Restore from a backup

Every change is backed up automatically. List backups:

```powershell
dir "$env:USERPROFILE\.codex\sqlite\chatgpt-catalog-backups"
```

Close the app, then restore one backup (this overwrites the current database):

```powershell
catalog-repair restore --backup "C:\Users\you\.codex\sqlite\chatgpt-catalog-backups\codex-dev-20260912-012539Z.db" --apply --yes
```

## FAQ

- **`Database does not exist`**: it cannot find `codex-dev.db`. Point `--database` at the right path, or confirm the Desktop app has been installed and run.
- **Still shows up after deletion**: this is usually sync-related. Close the app, repair, reopen, and wait; if it keeps coming back, consider `rebuild`.
- **Not sure what to delete**: don't guess. Run `inspect` first; without an exact ID, use `rebuild` instead.

## Other entry points

A PowerShell 7 launcher is included, read-only by default:

```powershell
pwsh -ExecutionPolicy Bypass -File .\scripts\Start-ChatGPT.ps1
```

Rebuild mode (asks you to type `REBUILD` to confirm):

```powershell
pwsh -ExecutionPolicy Bypass -File .\scripts\Start-ChatGPT.ps1 -Mode Rebuild
```

## Technical details (most users can skip)

### Safety guarantees

- `inspect` is always read-only.
- Every data-changing command requires both `--apply` and `--yes`.
- Backups use Python's SQLite backup API, including committed WAL data.
- The newest three backups are kept by default.

### Tables cleared by `rebuild`

Only a fixed allow-list of local cache tables:

```text
local_thread_catalog
local_thread_catalog_hosts
local_thread_catalog_metadata
local_thread_catalog_sync_state
local_thread_catalog_scan_checkpoints
local_thread_catalog_scan_entries
```

### Development

```powershell
py -m pip install -e ".[dev]"
py -m pytest
py -m ruff check .
```

Tests use temporary synthetic SQLite databases and never open your real catalog.

### Limitations

- The local schema and app identifier are not public compatibility contracts and may change.
- It repairs local catalog state only; it cannot restore server-side deletions.
- Rebuild depends on a successful later sync.

## License

[MIT](LICENSE)