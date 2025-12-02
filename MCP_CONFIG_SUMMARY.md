# MCP 配置总结

## 配置文件位置
- **VS Code MCP 配置**: `.vscode/mcp.json` (项目级配置，便于移植)
- **Cursor MCP 配置**: `.cursor/mcp/myserver/mcp.json` (项目级配置，便于移植)
- **用户级配置**: `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` (VS Code推荐)
- **Cursor 用户级配置**: `~/.config/cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` (Cursor推荐)

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
├── .mcp_env               # 环境配置
└── var/
    └── mcp/               # MCP 数据目录
```

## MCP 服务器配置

### 服务器名称
`diana-mcp`

### 配置详情
- **类型**: stdio
- **命令**: 使用VS Code当前Python解释器 (`${command:python.interpreterPath}`)
- **参数**: `["-m", "server.mcp_server"]`
- **工作目录**: `${workspaceFolder}`
- **环境变量**:
  - `PYTHONPATH=${workspaceFolder}`
  - `FASTMCP_NO_BANNER=1`

### 可用工具
- `get_joint_positions(ip?)`: 获取机械臂关节位置
- `move_joint_positions(ip?, joints, velocity, acceleration)`: 关节模式移动
- `move_linear_pose(ip?, pose, velocity, acceleration)`: 直线模式移动
- `stop_motion(ip?)`: 停止运动

## 测试结果
✅ 所有配置测试通过

## 使用方法
1. 确保conda环境 `mcp-demo` 已激活
2. 重启 VS Code/Cursor 或重新加载 MCP 配置
3. MCP 服务器将自动启动
4. 可以在编辑器中使用上述工具
