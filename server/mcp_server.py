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


@mcp.tool()
def move_joint_positions(ip: Optional[str] = None, joints: Optional[list] = None, velocity: float = 0.5, acceleration: float = 0.5) -> dict:
    """以关节模式移动机械臂（7 个关节值）"""
    try:
        if not joints or len(joints) != 7:
            raise RobotControlError("INVALID_PARAMETERS")

        if ip:
            net_info = get_net_info(ip)
            robot_control.controller.ensure_connected(net_info=net_info)
        else:
            robot_control.controller.ensure_connected()

        result = robot_control.controller.move_joint_positions(joints, velocity, acceleration)
        # 返回控制器 ip 与 move 的结果（如 taskId / status）
        return {
            'ip': robot_control.controller.ip_address,
            'result': result
        }
    except getattr(robot_control, 'RobotError', Exception) as exc:
        log_exception(exc, prefix='执行关节运动失败: ')
        raise RobotControlError("MOVE_FAILED") from exc


@mcp.tool()
def move_linear_pose(ip: Optional[str] = None, pose: Optional[list] = None, velocity: float = 0.2, acceleration: float = 0.2) -> dict:
    """以 TCP 直线模式移动机械臂（6 元 pose）"""
    try:
        if not pose or len(pose) != 6:
            raise RobotControlError("INVALID_PARAMETERS")

        if ip:
            net_info = get_net_info(ip)
            robot_control.controller.ensure_connected(net_info=net_info)
        else:
            robot_control.controller.ensure_connected()

        result = robot_control.controller.move_linear_pose(pose, velocity, acceleration)
        return {
            'ip': robot_control.controller.ip_address,
            'result': result
        }
    except getattr(robot_control, 'RobotError', Exception) as exc:
        log_exception(exc, prefix='执行直线运动失败: ')
        raise RobotControlError("MOVE_FAILED") from exc


@mcp.tool()
def stop_motion(ip: Optional[str] = None) -> dict:
    """立即停止机械臂的运动"""
    try:
        if ip:
            net_info = get_net_info(ip)
            robot_control.controller.ensure_connected(net_info=net_info)
        else:
            robot_control.controller.ensure_connected()

        result = robot_control.controller.stop_motion()
        return {
            'ip': robot_control.controller.ip_address,
            'result': result
        }
    except getattr(robot_control, 'RobotError', Exception) as exc:
        log_exception(exc, prefix='停止运动失败: ')
        raise RobotControlError("STOP_FAILED") from exc


def main():
    """启动MCP服务器"""
    log("启动机械臂位置MCP服务器")
    mcp.run()


if __name__ == '__main__':
    main()
