# ChatGPT Desktop Catalog Repair

修复 ChatGPT / Codex 桌面端本地会话目录的小工具。

[English](README.en.md)

## 它能做什么

桌面端偶尔会出现这类本地缓存问题：「已经删掉的对话还一直挂在侧栏」「侧栏内容跟云端对不上」。这个小工具用来检查和修复这些本地目录状态。

它**不做**这些事：

- 不能恢复已经在云端（服务端）删掉的对话，删了就真没了。
- 不连接 OpenAI，也不需要你的账号或密码。
- 默认只查看、不修改任何数据。

## 先说风险

- 这是**非官方**社区工具，与 OpenAI 无关。
- 桌面端的本地数据库结构并不公开承诺，随时可能随版本变化。
- 任何会**改动数据**的命令，都必须你同时加上 `--apply --yes` 才会执行，并且执行前会先自动备份一次。
- 备份文件里可能包含你的私人对话信息，**不要**上传到 GitHub、issue 或其他公开位置。
- 修复前请先**彻底退出**桌面应用；改完再重新打开，等待同步。

## 安装（Windows）

需要 Python 3.10 或更高版本；可选的启动器需要 PowerShell 7。

```powershell
git clone https://github.com/yan-as/chatgpt-desktop-catalog-repair.git
cd chatgpt-desktop-catalog-repair
py -m pip install .
```

装好后先跑一次只读检查，确认一切正常（这一步不会改任何数据）：

```powershell
catalog-repair inspect
```

## 怎么用

| 我要做什么 | 命令 | 会不会改数据 |
| --- | --- | --- |
| 先看看目录状态 | `inspect` | 不会，只读 |
| 删掉某个特定对话 | `targeted-repair` | 会 |
| 大面积错乱，重建本地目录 | `rebuild` | 会 |
| 从备份恢复 | `restore` | 会 |

默认数据库在 `%USERPROFILE%\.codex\sqlite\codex-dev.db`。如果你的不在那里，用 `--database` 指定路径；工具**不会**去扫描你的硬盘。

### 1. 只读检查（建议先做）

```powershell
catalog-repair inspect
```

输出是一段 JSON，`"integrity": "ok"` 表示数据库本身没问题，其余字段只是信息。

### 2. 删掉某个「幽灵」对话

只有在你手里有确切的 `thread-id` 时才用；可以再加 `--host-id` 进一步限定到某台设备：

```powershell
catalog-repair targeted-repair --thread-id "thread_xxx" --host-id "host_yyy" --apply --yes
```

这个命令**不会**根据标题、404 或同步失败去「猜」该删哪个对话，你必须自己给出准确 ID；给错 ID 就不会删到东西。命令会先备份，再输出删掉了哪些记录。

### 3. 大面积错乱：重建本地目录

侧栏严重过时、没有可靠 ID，或精确删除没效果时用。它只会清空本地缓存表，之后靠自己重新同步，**不会**碰到其它数据：

```powershell
catalog-repair rebuild --apply --yes --stop-app
```

`--stop-app` 会在写入前关掉 ChatGPT / Codex 进程。成功后重新打开桌面应用，等它同步完成。

### 4. 从备份恢复

每次改动前都会自动备份。先看看有哪些备份：

```powershell
dir "$env:USERPROFILE\.codex\sqlite\chatgpt-catalog-backups"
```

退出桌面应用后，选择一份恢复（会用它**覆盖**当前数据库）：

```powershell
catalog-repair restore --backup "C:\Users\你\.codex\sqlite\chatgpt-catalog-backups\codex-dev-20260912-012539Z.db" --apply --yes
```

## 常见问题

- **提示 `Database does not exist`**：没找到 `codex-dev.db`。用 `--database` 指定正确路径，或先确认已安装并运行过桌面客户端。
- **删了还是会再出现**：这类问题往往来自同步。先关应用、再操作、再重开并等待同步；仍反复出现再考虑「重建」。
- **不确定该删哪个**：不要乱试。先 `inspect`；没有确切 ID 就用「重建」，而不是猜。

## 其它入口

项目附带一个 PowerShell 7 启动器，默认是只读检查：

```powershell
pwsh -ExecutionPolicy Bypass -File .\scripts\Start-ChatGPT.ps1
```

重建模式（会要求你输入 `REBUILD` 确认）：

```powershell
pwsh -ExecutionPolicy Bypass -File .\scripts\Start-ChatGPT.ps1 -Mode Rebuild
```

## 技术细节（一般用户可跳过）

### 安全机制

- `inspect` 永远是只读的。
- 所有会改数据的命令都要求同时带 `--apply` 和 `--yes`。
- 备份用 Python 内置的 SQLite Backup API，能覆盖已提交但还在 WAL 里的数据。
- 默认保留最新 3 份备份。

### 重建会清空的表

只清空固定的本地缓存表：

```text
local_thread_catalog
local_thread_catalog_hosts
local_thread_catalog_metadata
local_thread_catalog_sync_state
local_thread_catalog_scan_checkpoints
local_thread_catalog_scan_entries
```

### 开发与验证

```powershell
py -m pip install -e ".[dev]"
py -m pytest
py -m ruff check .
```

测试只使用临时生成的合成 SQLite 数据库，不会读取真实聊天目录。

### 已知限制

- 本地数据库结构和应用标识并非公开兼容承诺，未来可能变化。
- 只能修复本地目录状态，无法恢复服务端已删除的对话。
- 完整重建依赖桌面端后续成功同步。

## 许可证

[MIT](LICENSE)