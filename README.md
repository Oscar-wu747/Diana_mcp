# DianaApi MCP Agent

基于Model Context Protocol的Diana机械臂控制服务器，提供完整的机械臂操作接口。

## 功能特性

- 🔗 **连接管理**: 连接/断开机械臂，支持多IP配置
- 📊 **状态监控**: 获取关节位置、TCP姿态、机器人状态
- 🤖 **运动控制**: 关节模式、直线模式、TCP方向移动
- 🛑 **安全控制**: 运动停止、恢复、自由驱动模式
- ⚡ **实时交互**: 通过MCP协议与AI助手无缝集成

## 快速开始

### 环境准备
```bash
# 创建conda环境
conda env create -f environment.yml
conda activate mcp-demo

# 安装依赖
./install.sh
```

### 运行服务器
```bash
# 激活环境后运行
python -m server.mcp_server
```

### IDE集成
项目包含自动配置：
- **VS Code**: `.vscode/mcp.json`
- **Cursor**: `.cursor/mcp/myserver/mcp.json`

## API工具

| 工具 | 描述 | 参数 |
|------|------|------|
| `connect_robot` | 连接机械臂 | `ip?` (可选) |
| `disconnect_robot` | 断开连接 | - |
| `get_joint_positions` | 获取关节位置 | `ip?` |
| `get_tcp_pose` | 获取TCP位置 | `ip?` |
| `get_robot_state` | 获取机器人状态 | `ip?` |
| `move_joint_positions` | 关节模式移动 | `ip?, joints[7], velocity?, acceleration?` |
| `move_joint_positions_json` | 关节移动(JSON) | `ip?, joints_json, velocity?, acceleration?` |
| `move_linear_pose` | 直线模式移动 | `ip?, pose[6], velocity?, acceleration?` |
| `move_tcp_direction` | TCP方向移动 | `ip?, direction, velocity?, acceleration?` |
| `rotate_tcp_direction` | TCP旋转 | `ip?, direction, velocity?, acceleration?` |
| `stop_motion` | 停止运动 | `ip?` |
| `resume_motion` | 恢复运动 | `ip?` |
| `enable_free_driving` | 自由驱动模式 | `ip?, mode` |

## 项目结构

```
DianaApi_agent_MCP/
├── server/              # MCP服务器核心
│   ├── mcp_server.py   # 主服务器文件
│   ├── tools.py         # 工具定义
│   ├── config.py        # 配置管理
│   └── error_handler.py # 错误处理
├── src/diana_api/       # 机械臂API核心库
├── lib/                 # 底层库文件(.so)
├── examples/            # 示例脚本（`example_client.py`, `call_mcp_tool.py`）
├── environment.yml      # conda环境配置
└── install.sh          # 安装脚本
```

## 使用示例

```python
import asyncio
from fastmcp import Client

async def main():
    async with Client("server.mcp_server") as client:
        # 连接机器人
        result = await client.call_tool("connect_robot", {"ip": "192.168.10.75"})

        # 获取关节位置
        joints = await client.call_tool("get_joint_positions", {})

        # 移动到零位
        await client.call_tool("move_joint_positions", {
            "joints": [0.0] * 7,
            "velocity": 0.2
        })

asyncio.run(main())
```

## 配置

- **默认IP**: `192.168.10.75`
- **Python版本**: >=3.8
- **依赖**: fastmcp>=2.13.0

## 许可证

MIT License - Copyright (c) 2025 Oscar-wu747
