# DianaApi 机械臂位置获取 Agent

一个简化的MCP服务器，用于通过Model Context Protocol获取机械臂关节位置。

## 功能

- `get_joint_positions(ip?)`: 获取机械臂当前关节位置

## 安装和运行

1. 激活conda环境：
```bash
conda activate mcp-demo
```

2. 运行MCP服务器：
```bash
python server/mcp_server.py
```

## 配置

- 默认机械臂IP: `192.168.10.75`
- 可以通过`get_joint_positions`工具的参数指定其他IP地址

## 项目结构

- `server/mcp_server.py`: MCP服务器主文件
- `server/config.py`: 配置管理
- `server/error_handler.py`: 错误处理
- `src/diana_api/`: 机械臂API核心库
- `lib/`: 底层库文件
