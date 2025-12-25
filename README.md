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
./scripts/install.sh
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
| `move_joint_positions_json` | 关节模式移动（JSON格式） | `ip?, joints_json, velocity?, acceleration?` |
| `move_linear_pose` | 直线模式移动 | `ip?, pose[6], velocity?, acceleration?` |
| `move_to_home_position` | 移动到默认原点位置 | `ip?, velocity?, acceleration?` |
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
├── docs/                  # 文档目录
│   └── IMPROVEMENTS.md    # 改进建议文档
├── scripts/               # 脚本目录
│   ├── format_code.sh     # 代码格式化脚本
│   └── install.sh         # 安装脚本
├── server/                # MCP 服务器代码
│   ├── mcp_server.py      # MCP 服务器主文件
│   ├── tools.py           # 工具定义
│   ├── config.py          # 配置管理
│   ├── error_handler.py   # 错误处理
│   ├── utils.py           # 工具函数和辅助类
│   └── robot_loader.py    # 机器人控制模块加载器
├── src/                   # 源代码
│   └── diana_api/         # 机械臂 API 核心库
├── lib/                   # 底层库文件 (.so)
├── var/                   # 运行时数据
│   ├── mcp/               # MCP 数据目录
│   └── logs/              # 日志文件目录
├── examples/              # 示例脚本
│   ├── example_client.py
│   └── call_mcp_tool.py
├── tests/                 # 测试脚本
├── environment.yml        # conda环境配置
├── setup.py               # Python 包配置
├── pyproject.toml         # 项目配置文件
└── README.md              # 项目主文档
```

### 代码架构

项目采用**模板方法模式（Template Method Pattern）**统一管理所有 MCP 工具函数：

- **统一执行模板**: `_execute_robot_action()` 和 `_execute_robot_action_async()` 统一处理连接检查、输出抑制、错误处理和响应格式化
- **工具函数简化**: 每个工具函数只需关注参数验证和调用对应的 controller 方法
- **代码复用**: 减少重复代码约 77 行，提高可维护性

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

        # 移动到默认原点位置（推荐）
        await client.call_tool("move_to_home_position", {
            "velocity": 0.5,
            "acceleration": 0.5
        })

asyncio.run(main())
```

## 配置

- **默认IP**: `192.168.10.75`
- **默认原点位置**: 关节角度（度）`[-85, -25, 16, 130, 7, -60, -3]`，可在 `server/config.py` 中修改 `DEFAULT_HOME_JOINTS_DEGREES`
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

## 代码格式化

项目使用 [Black](https://black.readthedocs.io/) 进行代码格式化。

**安装格式化工具**:
```bash
# 使用 conda 环境（推荐）
conda env update -f environment.yml

# 或直接安装
pip install black>=23.12.0 isort>=5.13.0
```

**格式化代码**:
```bash
# 使用脚本（推荐）
./scripts/format_code.sh

# 或手动运行
black .
isort .
```

**只检查不修改**:
```bash
black --check .
isort --check .
```

**Pre-commit 钩子**（可选）:
```bash
pip install pre-commit
pre-commit install
# 之后每次 git commit 前会自动格式化
```

## 许可证

MIT License - Copyright (c) 2025 Oscar-wu747
