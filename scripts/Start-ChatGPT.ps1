[CmdletBinding()]
param(
    [ValidateSet('Inspect', 'Rebuild')]
    [string]$Mode = 'Inspect',
    [string]$Database = "$env:USERPROFILE\.codex\sqlite\codex-dev.db",
    [int]$KeepBackups = 3,
    [switch]$NoLaunch
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot

if (-not (Get-Command catalog-repair -ErrorAction SilentlyContinue)) {
    Write-Error "catalog-repair is not installed. Run: py -m pip install -e '$projectRoot'"
}

if ($Mode -eq 'Inspect') {
    & catalog-repair --database $Database --keep-backups $KeepBackups inspect
    exit $LASTEXITCODE
}

$confirmation = Read-Host 'Full rebuild clears only the local catalog cache after creating a SQLite backup. Type REBUILD to continue'
if ($confirmation -ne 'REBUILD') {
    Write-Host 'Cancelled. No data was changed.'
    exit 0
}

& catalog-repair --database $Database --keep-backups $KeepBackups rebuild --apply --yes --stop-app
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if (-not $NoLaunch) {
    Start-Process explorer.exe 'shell:AppsFolder\OpenAI.Codex_2p2nqsd0c76g0!App'
}
