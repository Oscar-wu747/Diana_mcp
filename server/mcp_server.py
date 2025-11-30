#!/usr/bin/env python3
from typing import Optional

"""简化的MCP服务器，用于获取机械臂关节位置"""

import sys
import importlib.util
import types
from fastmcp import FastMCP

from .config import SRC_DIR, ensure_dirs, get_net_info
from .error_handler import log_exception, log, RobotControlError

# 确保数据目录存在
ensure_dirs()


def _load_robot_control():
    """加载机械臂控制模块，失败时返回备用存根"""
    init_file = SRC_DIR / 'diana_api' / '__init__.py'
    spec = importlib.util.spec_from_file_location('diana_api', init_file)
    if spec is None or spec.loader is None:
        raise RuntimeError('无法定位diana_api包')
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault('diana_api', module)
    try:
        spec.loader.exec_module(module)
        return module.control
    except Exception as exc:
        log_exception(exc, prefix='加载diana_api控制模块失败: ')

        class RobotError(RuntimeError):
            pass

        class _StubController:
            def __init__(self):
                self._ip = None

            @property
            def ip_address(self):
                return self._ip

            def ensure_connected(self, *, ip=None, _net_info=None):
                raise RobotError('机械臂库不可用')

            def get_joint_positions(self):
                raise RobotError('机械臂库不可用')

        ctrl_mod = types.SimpleNamespace(RobotError=RobotError, controller=_StubController())
        return ctrl_mod


# 加载机械臂控制模块
robot_control = _load_robot_control()

# 初始化FastMCP服务器
mcp = FastMCP("机械臂位置服务器")


@mcp.tool()
def get_joint_positions(ip: Optional[str] = None) -> dict:
    """获取机械臂关节位置"""
    try:
        if ip:
            net_info = get_net_info(ip)
            robot_control.controller.ensure_connected(net_info=net_info)
        else:
            robot_control.controller.ensure_connected()

        joints = robot_control.controller.get_joint_positions()
        return {
            'ip': robot_control.controller.ip_address,
            'joints': joints,
            'joint_count': len(joints)
        }
    except getattr(robot_control, 'RobotError', Exception) as exc:
        log_exception(exc, prefix='获取关节位置失败: ')
        raise RobotControlError("GET_JOINT_POS_FAILED") from exc


def main():
    """启动MCP服务器"""
    log("启动机械臂位置MCP服务器")
    mcp.run()


if __name__ == '__main__':
    main()
