**MCP Server**: 简单 stdio MCP 服务器

- **位置**: `server/mcp_server.py`
- **目标文件**: `src/diana_api/diana_api.py`

运行前准备（使用你指定的 conda 环境 `mcp-demo`）:

```bash
conda activate mcp-demo
python server/mcp_server.py
```

或者在 VS Code 中使用 `.vscode/mcp.json` 的 stdio 配置来启动 MCP 服务器。

协议 (JSON-RPC 2.0):

- 初始化: `{"jsonrpc":"2.0","id":1,"method":"initialize",...}`
- 列工具: `{"jsonrpc":"2.0","id":2,"method":"tools/list"}`
- 调用工具: `{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"diana.read_range","arguments":{"start":10,"end":20}}}`

仍兼容旧的逐行 JSON 格式:
- 读取: `{ "op": "read" }`
- 搜索: `{ "op": "search", "query": "text" }`
- 写入: `{ "op": "write", "content": "...", "message": "optional" }`
- 列版本: `{ "op": "list_versions" }`
- 取回版本: `{ "op": "get_version", "name": "<version-filename>" }`

响应格式: JSON-RPC 2.0 (`result` / `error`)，或旧版 `{ "ok": true/false, "data": ..., "error": "..." }`。

备份与审计: 写入操作会把新内容保存到 `var/mcp/versions/`，并在 `var/mcp/audit.log` 记录审计入口。可通过 `DIANA_API_ROOT` 环境变量自定义根目录。

注意:
- 目前实现主要面向单文件编辑；如需扩展更多资源或权限控制，请提出需求。
