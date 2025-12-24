#!/bin/bash

# Diana MCP Agent 安装脚本

set -e

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 切换到项目根目录
cd "$PROJECT_ROOT"

echo "安装 Diana MCP Agent..."

# 检查 Python 版本
python3 --version

# 安装依赖
pip install -e .

echo "安装完成！"
echo "运行服务器：python -m server.mcp_server"