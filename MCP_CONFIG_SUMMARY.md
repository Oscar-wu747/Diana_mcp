# MCP 配置总结

## 配置文件位置
- **Cursor MCP 配置**: `~/.cursor/mcp.json`

## 项目结构
```
DianaApi_agent_MCP/
├── server/
│   ├── mcp_server.py      # MCP 服务器主文件
│   ├── config.py          # 配置管理
│   └── error_handler.py   # 错误处理
├── src/
│   └── diana_api/         # 机械臂 API 核心库
├── lib/                   # 底层库文件 (.so)
└── var/
    └── mcp/               # MCP 数据目录
```

## MCP 服务器配置

### 服务器名称
`diana-mcp`

### 配置详情
- **类型**: stdio
- **Python 路径**: `/home/jetson/miniconda3/envs/Diana/bin/python`
- **运行方式**: 模块方式 (`-m server.mcp_server`)
- **工作目录**: `/home/jetson/Documents/DianaApi_agent_MCP`
- **环境变量**: `PYTHONPATH=/home/jetson/Documents/DianaApi_agent_MCP`

### 可用工具
- `get_joint_positions(ip?)`: 获取机械臂关节位置

## 测试结果
✅ 所有配置测试通过

## 使用方法
1. 重启 Cursor 或重新加载 MCP 配置
2. MCP 服务器将自动启动
3. 可以在 Cursor 中使用 `get_joint_positions` 工具

