# DianaApi 机械臂位置获取 Agent

一个简洁完整的MCP服务器，用于通过Model Context Protocol控制Diana机械臂。

## 功能

- `connect_robot(ip?)`: 连接到机械臂
- `disconnect_robot()`: 断开与机械臂的连接
- `get_joint_positions(ip?)`: 获取机械臂当前关节位置
- `get_tcp_pose(ip?)`: 获取机械臂TCP位置
- `get_robot_state(ip?)`: 获取机械臂状态信息
- `move_joint_positions(ip?, joints, velocity, acceleration)`: 关节模式移动
- `move_linear_pose(ip?, pose, velocity, acceleration)`: 直线模式移动
- `move_tcp_direction(ip?, direction, velocity, acceleration)`: TCP方向移动
- `rotate_tcp_direction(ip?, direction, velocity, acceleration)`: TCP旋转
- `stop_motion(ip?)`: 停止运动
- `resume_motion(ip?)`: 恢复运动
- `enable_free_driving(ip?, mode)`: 启用自由驱动模式 (0: 禁用, 1: 普通, 2: 强制)

## 安装和运行

### 环境准备

1. 创建conda环境：
```bash
conda env create -f environment.yml
```

2. 激活conda环境：
```bash
conda activate mcp-demo
```

### 安装

```bash
./install.sh
```

### MCP服务器配置

#### 自动配置（推荐）
项目已包含IDE配置文件，便于移植：
- **VS Code**: `.vscode/mcp.json`
- **Cursor**: `.cursor/mcp/myserver/mcp.json`

IDE会自动识别并启动MCP服务器。

#### 手动运行
```bash
conda activate mcp-demo
python -m server.mcp_server
```

### 环境配置
- 默认机械臂IP: `192.168.10.75`
- 可以通过工具参数指定其他IP地址

## 项目结构

```
DianaApi_agent_MCP/
├── server/                   # MCP服务器模块
├── server/                   # 原始模块化版本（保留）
│   ├── mcp_server.py
│   ├── config.py
│   └── ...
├── src/
│   └── diana_api/            # 机械臂API核心库
├── example_client.py         # 使用示例
├── setup.py                  # 安装配置
├── install.sh                # 安装脚本
└── README.md
```

## 使用示例

参考 `example_client.py` 查看完整的使用示例。



## 项目结构

- `server/mcp_server.py`: MCP服务器主文件
- `server/config.py`: 配置管理
- `server/error_handler.py`: 错误处理
- `src/diana_api/`: 机械臂API核心库
- `lib/`: 底层库文件
