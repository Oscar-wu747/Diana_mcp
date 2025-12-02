# DianaApi 机械臂位置获取 Agent

一个简化的MCP服务器，用于通过Model Context Protocol获取机械臂关节位置。

## 功能

- `get_joint_positions(ip?)`: 获取机械臂当前关节位置

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

### MCP服务器配置

#### 自动配置（推荐）
项目已包含IDE配置文件，便于移植：
- **VS Code**: `.vscode/mcp.json`
- **Cursor**: `.cursor/mcp/myserver/mcp.json`

IDE会自动识别并启动MCP服务器。

#### 用户级配置（全局）
也可以在用户级配置中添加服务器，便于在多个项目中使用。

#### 手动运行
```bash
conda activate mcp-demo
python -m server.mcp_server
```

### 环境配置
- 默认机械臂IP: `192.168.10.75`
- 可以通过工具参数指定其他IP地址
- 环境配置文件：`.mcp_env`（包含conda环境名称）



## 项目结构

- `server/mcp_server.py`: MCP服务器主文件
- `server/config.py`: 配置管理
- `server/error_handler.py`: 错误处理
- `src/diana_api/`: 机械臂API核心库
- `lib/`: 底层库文件
