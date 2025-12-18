#!/bin/bash

# Diana MCP Agent 安装脚本

echo "安装 Diana MCP Agent..."

# 检查 Python 版本
python3 --version

# 安装依赖
pip install -e .

echo "安装完成！"
echo "运行服务器：python -m server.mcp_server"