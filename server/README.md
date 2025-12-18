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
| `get_joint_positions` | 获取机械臂当前关节位置 | 可选 `ip:str` |
| `move_joint_positions` | 以关节模式移动机械臂（7个关节值） | `joints:list`, `velocity:float`, `acceleration:float`, 可选 `ip:str` |
| `move_linear_pose` | 以TCP直线模式移动机械臂（6元pose） | `pose:list`, `velocity:float`, `acceleration:float`, 可选 `ip:str` |
| `stop_motion` | 立即停止机械臂运动 | 可选 `ip:str` |

所有工具都基于 `diana_api.control` 模块，提供高层封装和错误处理。

示例脚本位于仓库的 `examples/` 目录；例如 `examples/call_mcp_tool.py` 提供了一个本地直接调用工具的示例，便于开发时快速验证功能。
