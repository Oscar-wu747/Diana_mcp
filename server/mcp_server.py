#!/usr/bin/env python3
"""简化的MCP服务器，用于获取机械臂关节位置"""

from fastmcp import FastMCP

from .config import ensure_dirs
from .error_handler import log
from .tools import register_tools

# 确保数据目录存在
ensure_dirs()

# 初始化FastMCP服务器
mcp = FastMCP("Diana 机械臂 MCP 服务器")

# 注册所有工具
register_tools(mcp)


def main():
    """启动MCP服务器"""
    log("启动机械臂位置MCP服务器")
    mcp.run()


if __name__ == '__main__':
    main()
