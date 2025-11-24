## Diana MCP Server

`server/mcp_server.py` 提供一个面向 VS Code / Cursor 的本地 MCP stdio 服务器，用于安全地读写 `src/diana_api/diana_api.py`。启动前请先激活 `conda activate mcp-demo`。

### 启动

```bash
conda activate mcp-demo
python server/mcp_server.py
```

VS Code 中可在 `.vscode/mcp.json` 指向同样的命令。

### JSON-RPC 能力

| 方法 / 工具 | 说明 |
| --- | --- |
| `initialize` / `shutdown` / `ping` | JSON-RPC 基础握手，默认 `protocolVersion=2025-06-18`。 |
| `tools/list` | 返回下表中的工具描述。 |
| `tools/call` | 执行指定工具，返回文本内容。 |
| `resources/list` | 目前返回空数组，保留扩展点。 |
| `prompts/list` | 目前返回空数组，保留扩展点。 |

### 可用工具

| 工具名 | 作用 | 参数 |
| --- | --- | --- |
| `diana.read_file` | 读取 `src/diana_api/diana_api.py` 全量文本。 | 无 |
| `diana.read_range` | 按行区间读取片段。 | `start:int`, `end:int` |
| `diana.search` | 基于子串的行级搜索。 | `query:str` |
| `diana.symbols` | 返回 AST 解析出的函数/类符号列表。 | 无 |
| `diana.stats` | 返回文件行数、字节大小与 SHA1。 | 无 |
| `diana.list_versions` | 枚举 `var/mcp/versions/` 中的备份。 | 无 |
| `diana.get_version` | 读取指定备份内容。 | `name:str` |
| `diana.write_file` | 写入内容并生成备份，默认进行语法校验。 | `content:str`, 可选 `message:str`, `check_syntax:bool` |
| `robot.get_joint_positions` | 基于 `diana_api.control` 的高层封装返回 7 轴关节角度；首次调用可提供 `ip` 自动建立连接。 | 可选 `ip:str` |

所有工具在 JSON-RPC 模式下都会以 `tools/call` 调用；为了兼容旧脚本，也可以直接向进程写入 `{"op":"read"}` 等简化 JSON。

