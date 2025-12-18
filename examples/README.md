# Examples

本目录包含用于开发与快速验证的示例脚本：

- `example_client.py`：使用 `fastmcp.Client` 作为远程客户端示例，展示如何调用 MCP 工具链（连接、读取状态、移动、断开）。
- `call_mcp_tool.py`：在项目内部直接导入并调用 `server.tools` 中的函数，便于在没有 MCP 服务器运行时快速本地验证工具行为。

运行示例（开发者机器）：

```bash
# 运行 example_client（需要 MCP 服务器在运行）
python3 examples/example_client.py

# 在没有 MCP 服务器时，直接运行本地示例
PYTHONPATH=./src python3 examples/call_mcp_tool.py
```

如果需要在 CI 中运行示例，建议使用最小的 smoke 测试脚本：`tests/run_tasks_smoke.py`。
