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
项目包含自动配置，支持VS Code和Cursor：

**项目级配置（推荐，便于移植）**:
- **VS Code**: `.vscode/mcp.json`
- **Cursor**: `.cursor/mcp/myserver/mcp.json`

### 使用方法
1. 确保conda环境 `mcp-demo` 已激活
2. 重启 VS Code/Cursor 或重新加载 MCP 配置
3. MCP 服务器将自动启动（服务器名称：`diana-mcp`）
4. 可以在编辑器中使用以下工具

## API工具

| 工具 | 描述 | 参数 |
|------|------|------|
| `connect_robot` | 连接机械臂 | `ip?` (可选) |
| `disconnect_robot` | 断开连接 | - |
| `get_joint_positions` | 获取关节位置 | `ip?` |
| `get_tcp_pose` | 获取TCP位置 | `ip?` |
| `get_robot_state` | 获取机器人状态 | `ip?` |
| `move_joint_positions` | 关节模式移动 | `ip?, joints[7], velocity?, acceleration?` |
| `move_linear_pose` | 直线模式移动 | `ip?, pose[6], velocity?, acceleration?` |
| `move_tcp_direction` | TCP方向移动 | `ip?, direction, velocity?, acceleration?` |
| `rotate_tcp_direction` | TCP旋转 | `ip?, direction, velocity?, acceleration?` |
| `stop_motion` | 停止运动 | `ip?` |
| `resume_motion` | 恢复运动 | `ip?` |
| `enable_free_driving` | 自由驱动模式 | `ip?, mode` |

## MCP服务器配置

### 服务器信息
- **名称**: `diana-mcp`
- **类型**: stdio
- **命令**: 使用当前Python解释器 (`${command:python.interpreterPath}`)
- **参数**: `["-m", "server.mcp_server"]`
- **工作目录**: `${workspaceFolder}`
- **环境变量**: `PYTHONPATH=${workspaceFolder}`

## 项目结构

```
DianaApi_agent_MCP/
├── server/
│   ├── mcp_server.py      # MCP 服务器主文件
│   ├── tools.py           # 工具定义
│   ├── config.py          # 配置管理
│   └── error_handler.py   # 错误处理
├── src/
│   └── diana_api/         # 机械臂 API 核心库
├── lib/                   # 底层库文件 (.so)
├── .mcp_env               # 环境配置
├── var/
│   └── mcp/               # MCP 数据目录
├── examples/              # 示例脚本（`example_client.py`, `call_mcp_tool.py`）
├── environment.yml        # conda环境配置
└── install.sh            # 安装脚本
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

## 开发者测试

在没有真机的情况下运行测试：

**Smoke测试**:
```bash
# 从项目根运行（确保 PATH 指向系统 Python）
PYTHONPATH=./src python3 tests/run_tasks_smoke.py
```

**Pytest测试**:
```bash
pip install -U pytest
PYTHONPATH=./src pytest -q
```

✅ 所有配置测试通过

这些测试会 monkeypatch `diana_api` 的调用，验证任务模型与控制层逻辑，不需要连接真机。

## 许可证

MIT License - Copyright (c) 2025 Oscar-wu747
