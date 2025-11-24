# Diana API

## 项目简介

Diana API 提供一套 Python ctypes 绑定，用于调用底层机器人控制 SDK，并附带一个符合 Model Context Protocol (MCP) 的本地服务端，方便在编辑器内读写主脚本。

## 目录结构（2025 重整版）

- `src/diana_api/`：主 Python 绑定（原 `bin/DianaApi.py`），可通过 `import diana_api` 复用；内置 `diana_api.control` 高层封装（连接、运动、状态管理）。
- `lib/`：平台相关的二进制依赖 (`*.so` / `*.dll`)，通过环境变量 `DIANA_API_LIB_DIR` 可自定义路径。
- `server/mcp_server.py`：MCP stdio 服务，提供文件读写、版本管理等功能。
- `examples/`：演示脚本（`pos_get.py`, `test*.py` 等）。
- `var/mcp/`：MCP 服务器的审计日志与版本备份。
- `api-documentation/`：API 文档。

> 运行示例或 MCP 服务前，请先激活 `conda activate mcp-demo` 并确保 `lib/` 下的共享库完整。
