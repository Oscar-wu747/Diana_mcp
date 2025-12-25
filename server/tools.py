"""MCP工具函数"""

import math
from typing import Any, Callable, Dict, Optional, Union

from fastmcp import Context

from .config import DEFAULT_HOME_JOINTS_DEGREES, get_net_info
from .error_handler import RobotControlError, log_exception
from .robot_loader import robot_control
from .utils import (
    SuppressRobotOutput,
    _get_ip_or_default,
    _normalize_ip,
    _parse_array_param,
    ensure_robot_connected,
)
from .validators import (
    validate_acceleration,
    validate_free_driving_mode,
    validate_joints,
    validate_pose,
    validate_tcp_direction,
    validate_velocity,
)


def _execute_robot_action(
    action: Callable,
    ip: Optional[str] = None,
    raise_on_mismatch: bool = True,
    skip_connection_check: bool = False,
    error_code: str = "OPERATION_FAILED",
    error_prefix: str = "操作失败: ",
    success_fields: Optional[Dict[str, Any]] = None,
    error_fields: Optional[Dict[str, Any]] = None,
) -> dict:
    """统一的工具执行模板（同步版本）

    Args:
        action: 要执行的操作函数（无参数）
        ip: 可选的 IP 地址
        raise_on_mismatch: 如果 IP 不匹配是否抛出异常
        skip_connection_check: 是否跳过连接检查（用于 connect/disconnect）
        error_code: 错误代码
        error_prefix: 错误日志前缀
        success_fields: 成功时额外返回的字段
        error_fields: 失败时额外返回的字段

    Returns:
        包含操作结果的字典
    """
    try:
        # 确保连接，IP 不匹配时根据 raise_on_mismatch 决定行为
        if not skip_connection_check:
            actual_ip, error = ensure_robot_connected(ip, raise_on_mismatch=raise_on_mismatch)
            if error:
                # 如果返回了错误信息，合并额外的错误字段
                if error_fields:
                    error.update(error_fields)
                return error

        # 抑制机械臂库的输出并执行操作
        with SuppressRobotOutput():
            result = action()

        # 构建成功响应
        response = {
            "success": True,
            "ip": robot_control.controller.ip_address,
        }

        # 如果 action 返回了字典，直接合并到响应中
        if isinstance(result, dict):
            response.update(result)
        elif result is not None:
            # 否则作为 result 字段
            response["result"] = result

        # 添加额外的成功字段（会覆盖 action 返回的同名字段）
        if success_fields:
            response.update(success_fields)

        return response

    except getattr(robot_control, "RobotError", Exception) as exc:
        log_exception(exc, prefix=error_prefix)
        response = {
            "success": False,
            "error": error_code,
            "message": f"{error_prefix}{str(exc)}",
            "ip": ip or "N/A",
        }
        if error_fields:
            response.update(error_fields)
        return response
    except Exception as exc:
        log_exception(exc, prefix=f"{error_prefix}(未知错误): ")
        response = {
            "success": False,
            "error": "UNKNOWN_ERROR",
            "message": f"未知错误: {str(exc)}",
            "ip": ip or "N/A",
        }
        if error_fields:
            response.update(error_fields)
        return response


async def _execute_robot_action_async(
    action: Callable,
    ip: Optional[str] = None,
    ctx: Optional[Context] = None,
    raise_on_mismatch: bool = True,
    skip_connection_check: bool = False,
    error_code: str = "OPERATION_FAILED",
    error_prefix: str = "操作失败: ",
    success_fields: Optional[Dict[str, Any]] = None,
    error_fields: Optional[Dict[str, Any]] = None,
) -> dict:
    """统一的工具执行模板（异步版本）

    Args:
        action: 要执行的操作函数（无参数）
        ip: 可选的 IP 地址
        ctx: MCP 上下文，用于输出信息
        raise_on_mismatch: 如果 IP 不匹配是否抛出异常
        skip_connection_check: 是否跳过连接检查（用于 connect/disconnect）
        error_code: 错误代码
        error_prefix: 错误日志前缀
        success_fields: 成功时额外返回的字段
        error_fields: 失败时额外返回的字段

    Returns:
        包含操作结果的字典
    """
    try:
        # 确保连接，IP 不匹配时根据 raise_on_mismatch 决定行为
        if not skip_connection_check:
            actual_ip, error = ensure_robot_connected(ip, raise_on_mismatch=raise_on_mismatch)
            if error:
                if ctx:
                    await ctx.info(error.get("message", "操作失败"))
                if error_fields:
                    error.update(error_fields)
                return error

        # 抑制机械臂库的输出并执行操作
        with SuppressRobotOutput():
            result = action()

        # 构建成功响应
        response = {
            "success": True,
            "ip": robot_control.controller.ip_address,
        }

        # 如果 action 返回了字典，直接合并到响应中
        if isinstance(result, dict):
            response.update(result)
        elif result is not None:
            # 否则作为 result 字段
            response["result"] = result

        # 添加额外的成功字段（会覆盖 action 返回的同名字段）
        if success_fields:
            response.update(success_fields)

        if ctx and "message" in response:
            await ctx.info(response["message"])

        return response

    except getattr(robot_control, "RobotError", Exception) as exc:
        log_exception(exc, prefix=error_prefix)
        error_msg = f"{error_prefix}{str(exc)}"
        if ctx:
            await ctx.info(error_msg)
        response = {
            "success": False,
            "error": error_code,
            "message": error_msg,
            "ip": ip or "N/A",
        }
        if error_fields:
            response.update(error_fields)
        return response
    except Exception as exc:
        log_exception(exc, prefix=f"{error_prefix}(未知错误): ")
        error_msg = f"未知错误: {str(exc)}"
        if ctx:
            await ctx.info(error_msg)
        response = {
            "success": False,
            "error": "UNKNOWN_ERROR",
            "message": error_msg,
            "ip": ip or "N/A",
        }
        if error_fields:
            response.update(error_fields)
        return response


def register_tools(mcp):
    """注册所有MCP工具"""

    @mcp.tool()
    async def connect_robot(ip: Optional[str] = None, ctx: Optional[Context] = None) -> dict:
        """显式连接机械臂

        Args:
            ip: 机器人的 IP 地址（可选，默认使用配置的 IP）

        Returns:
            连接结果
        """
        original_ip = ip  # 保存原始 IP 用于错误信息
        # 规范化 IP 参数
        normalized_ip = _get_ip_or_default(ip)

        if ctx:
            await ctx.info(f"正在连接到机器人 {normalized_ip}...")

        def action():
            net_info = get_net_info(normalized_ip)
            result = robot_control.controller.connect(net_info)
            message = f"机械臂连接{'成功' if result.get('status') == 'connected' else '已连接'}"
            return {
                "status": result.get("status", "connected"),
                "ip": result.get("ip", normalized_ip),
                "message": message,
            }

        return await _execute_robot_action_async(
            action=action,
            ip=None,
            ctx=ctx,
            raise_on_mismatch=False,
            skip_connection_check=True,
            error_code="CONNECT_FAILED",
            error_prefix="连接机械臂失败: ",
            error_fields={"ip": normalized_ip, "original_ip": original_ip if original_ip else None},
        )

    @mcp.tool()
    async def disconnect_robot(ctx: Optional[Context] = None) -> dict:
        """显式断开机械臂连接

        Returns:
            断开连接结果
        """
        if ctx:
            await ctx.info("正在断开与机器人的连接...")

        def action():
            result = robot_control.controller.disconnect()
            message = (
                f"机械臂{'已断开连接' if result.get('status') == 'disconnected' else '未连接'}"
            )
            return {"status": result.get("status", "disconnected"), "message": message}

        return await _execute_robot_action_async(
            action=action,
            ip=None,
            ctx=ctx,
            raise_on_mismatch=False,
            skip_connection_check=True,
            error_code="DISCONNECT_FAILED",
            error_prefix="断开机械臂连接失败: ",
        )

    @mcp.tool()
    def get_joint_positions(ip: Optional[str] = None) -> dict:
        """获取机械臂关节位置"""

        def action():
            joints = robot_control.controller.get_joint_positions()
            return {"joints": joints, "joint_count": len(joints)}

        return _execute_robot_action(
            action=action,
            ip=ip,
            raise_on_mismatch=False,
            error_code="GET_JOINT_POS_FAILED",
            error_prefix="获取关节位置失败: ",
            error_fields={"joints": [], "joint_count": 0},
        )

    @mcp.tool()
    def move_joint_positions(
        ip: Optional[str] = None,
        joints: Optional[list] = None,
        velocity: float = 0.5,
        acceleration: float = 0.5,
    ) -> dict:
        """以关节模式移动机械臂（7 个关节值）

        Args:
            ip: 可选的 IP 地址
            joints: 关节角度数组（弧度），7 个值
            velocity: 速度 (默认 0.5)
            acceleration: 加速度 (默认 0.5)
        """
        # 参数验证
        try:
            validated_joints = validate_joints(joints, "joints")
            validated_velocity = validate_velocity(velocity, "velocity")
            validated_acceleration = validate_acceleration(acceleration, "acceleration")
        except ValueError as e:
            return {
                "success": False,
                "error": "INVALID_PARAMETERS",
                "message": str(e),
                "ip": ip or "N/A",
                "result": None,
            }

        def action():
            return robot_control.controller.move_joint_positions(
                validated_joints, validated_velocity, validated_acceleration
            )

        return _execute_robot_action(
            action=action,
            ip=ip,
            raise_on_mismatch=True,
            error_code="MOVE_FAILED",
            error_prefix="执行关节运动失败: ",
            error_fields={"result": None},
        )

    @mcp.tool()
    def move_joint_positions_json(
        ip: Optional[str] = None,
        joints_json: str = "",
        velocity: float = 0.5,
        acceleration: float = 0.5,
    ) -> dict:
        """以关节模式移动机械臂（7 个关节值，JSON 字符串格式）

        Args:
            ip: 可选的 IP 地址
            joints_json: 关节角度数组的 JSON 字符串格式，如 '[-1.48, -0.42, 0.29, 2.27, 0.12, -1.05, -0.05]'
            velocity: 速度 (默认 0.5)
            acceleration: 加速度 (默认 0.5)
        """
        # 解析 JSON 字符串
        try:
            joints = _parse_array_param(joints_json, "joints_json")
        except ValueError as e:
            return {
                "success": False,
                "error": "INVALID_PARAMETERS",
                "message": f"关节参数 JSON 格式错误: {str(e)}",
                "ip": ip or "N/A",
                "result": None,
            }

        # 参数验证
        try:
            validated_joints = validate_joints(joints, "joints_json")
            validated_velocity = validate_velocity(velocity, "velocity")
            validated_acceleration = validate_acceleration(acceleration, "acceleration")
        except ValueError as e:
            return {
                "success": False,
                "error": "INVALID_PARAMETERS",
                "message": str(e),
                "ip": ip or "N/A",
                "result": None,
            }

        def action():
            return robot_control.controller.move_joint_positions(
                validated_joints, validated_velocity, validated_acceleration
            )

        return _execute_robot_action(
            action=action,
            ip=ip,
            raise_on_mismatch=True,
            error_code="MOVE_FAILED",
            error_prefix="执行关节运动失败: ",
            error_fields={"result": None},
        )

    @mcp.tool()
    def move_linear_pose(
        ip: Optional[str] = None,
        pose: Optional[list] = None,
        velocity: float = 0.2,
        acceleration: float = 0.2,
    ) -> dict:
        """以 TCP 直线模式移动机械臂（6 元 pose）

        Args:
            ip: 可选的 IP 地址
            pose: TCP 姿态数组 [x, y, z, rx, ry, rz]，6 个值
            velocity: 速度 (默认 0.2)
            acceleration: 加速度 (默认 0.2)
        """
        # 参数验证
        try:
            validated_pose = validate_pose(pose, "pose")
            validated_velocity = validate_velocity(velocity, "velocity")
            validated_acceleration = validate_acceleration(acceleration, "acceleration")
        except ValueError as e:
            return {
                "success": False,
                "error": "INVALID_PARAMETERS",
                "message": str(e),
                "ip": ip or "N/A",
                "result": None,
            }

        def action():
            return robot_control.controller.move_linear_pose(
                validated_pose, validated_velocity, validated_acceleration
            )

        return _execute_robot_action(
            action=action,
            ip=ip,
            raise_on_mismatch=True,
            error_code="MOVE_FAILED",
            error_prefix="执行直线运动失败: ",
            error_fields={"result": None},
        )

    @mcp.tool()
    def get_tcp_pose(ip: Optional[str] = None) -> dict:
        """获取机械臂TCP位置"""

        def action():
            tcp_pose = robot_control.controller.get_tcp_pose()
            return {"tcp_pose": tcp_pose}

        return _execute_robot_action(
            action=action,
            ip=ip,
            raise_on_mismatch=False,
            error_code="GET_TCP_POSE_FAILED",
            error_prefix="获取TCP位置失败: ",
            error_fields={"tcp_pose": []},
        )

    @mcp.tool()
    def get_robot_state(ip: Optional[str] = None) -> dict:
        """获取机械臂状态"""

        def action():
            robot_state = robot_control.controller.get_robot_state()
            return {"robot_state": robot_state}

        return _execute_robot_action(
            action=action,
            ip=ip,
            raise_on_mismatch=False,
            error_code="GET_ROBOT_STATE_FAILED",
            error_prefix="获取机器人状态失败: ",
            error_fields={"robot_state": {}},
        )

    @mcp.tool()
    def resume_motion(ip: Optional[str] = None) -> dict:
        """恢复机械臂运动"""

        def action():
            return robot_control.controller.resume_motion()

        return _execute_robot_action(
            action=action,
            ip=ip,
            raise_on_mismatch=True,
            error_code="RESUME_FAILED",
            error_prefix="恢复运动失败: ",
            error_fields={"result": None},
        )

    @mcp.tool()
    def enable_free_driving(ip: Optional[str] = None, mode: int = 1) -> dict:
        """启用机械臂自由驱动模式

        Args:
            mode: 自由驱动模式 (0: 禁用, 1: 正常, 2: 强制)
        """
        # 参数验证
        try:
            validated_mode = validate_free_driving_mode(mode, "mode")
        except ValueError as e:
            return {
                "success": False,
                "error": "INVALID_PARAMETERS",
                "message": str(e),
                "ip": ip or "N/A",
                "result": None,
            }

        def action():
            return robot_control.controller.enable_free_driving(validated_mode)

        return _execute_robot_action(
            action=action,
            ip=ip,
            raise_on_mismatch=True,
            error_code="FREE_DRIVING_FAILED",
            error_prefix="启用自由驱动失败: ",
            error_fields={"result": None},
        )

    @mcp.tool()
    def move_tcp_direction(
        ip: Optional[str] = None,
        direction: int = 0,
        velocity: float = 0.2,
        acceleration: float = 0.2,
    ) -> dict:
        """以TCP方向移动机械臂"""
        # 参数验证
        try:
            validated_direction = validate_tcp_direction(direction, "direction")
            validated_velocity = validate_velocity(velocity, "velocity")
            validated_acceleration = validate_acceleration(acceleration, "acceleration")
        except ValueError as e:
            return {
                "success": False,
                "error": "INVALID_PARAMETERS",
                "message": str(e),
                "ip": ip or "N/A",
                "result": None,
            }

        def action():
            return robot_control.controller.move_tcp_direction(
                validated_direction, validated_velocity, validated_acceleration
            )

        return _execute_robot_action(
            action=action,
            ip=ip,
            raise_on_mismatch=True,
            error_code="MOVE_TCP_FAILED",
            error_prefix="TCP方向移动失败: ",
            error_fields={"result": None},
        )

    @mcp.tool()
    def rotate_tcp_direction(
        ip: Optional[str] = None,
        direction: int = 0,
        velocity: float = 0.2,
        acceleration: float = 0.2,
    ) -> dict:
        """旋转TCP方向"""
        # 参数验证
        try:
            validated_direction = validate_tcp_direction(direction, "direction")
            validated_velocity = validate_velocity(velocity, "velocity")
            validated_acceleration = validate_acceleration(acceleration, "acceleration")
        except ValueError as e:
            return {
                "success": False,
                "error": "INVALID_PARAMETERS",
                "message": str(e),
                "ip": ip or "N/A",
                "result": None,
            }

        def action():
            return robot_control.controller.rotate_tcp_direction(
                validated_direction, validated_velocity, validated_acceleration
            )

        return _execute_robot_action(
            action=action,
            ip=ip,
            raise_on_mismatch=True,
            error_code="ROTATE_TCP_FAILED",
            error_prefix="TCP旋转失败: ",
            error_fields={"result": None},
        )

    @mcp.tool()
    def stop_motion(ip: Optional[str] = None) -> dict:
        """立即停止机械臂的运动"""

        def action():
            return robot_control.controller.stop_motion()

        return _execute_robot_action(
            action=action,
            ip=ip,
            raise_on_mismatch=True,
            error_code="STOP_FAILED",
            error_prefix="停止运动失败: ",
            error_fields={"result": None},
        )

    @mcp.tool()
    def get_task(task_id: str) -> dict:
        """获取指定任务的状态"""

        def action():
            t = robot_control.controller.get_task(task_id)
            return {"task": t}

        return _execute_robot_action(
            action=action,
            ip=None,
            skip_connection_check=True,
            error_code="TASK_NOT_FOUND",
            error_prefix="获取任务失败: ",
            error_fields={"task_id": task_id},
        )

    @mcp.tool()
    def wait_task(task_id: str, timeout: Optional[float] = None) -> dict:
        """等待指定任务完成（timeout 秒可选）"""

        def action():
            t = robot_control.controller.wait_task(task_id, timeout)
            return {"task": t}

        result = _execute_robot_action(
            action=action,
            ip=None,
            skip_connection_check=True,
            error_code="TASK_NOT_FOUND",
            error_prefix="等待任务失败: ",
            error_fields={"task_id": task_id},
        )

        # 特殊处理：检查是否是超时错误
        if not result.get("success") and "message" in result:
            msg = result["message"]
            if "timeout" in msg.lower():
                result["error"] = "TASK_TIMEOUT"

        return result

    @mcp.tool()
    def cancel_task(task_id: str) -> dict:
        """取消指定任务（会尝试停止机械臂）"""

        def action():
            t = robot_control.controller.cancel_task(task_id)
            return {"task": t}

        return _execute_robot_action(
            action=action,
            ip=None,
            skip_connection_check=True,
            error_code="TASK_CANCEL_FAILED",
            error_prefix="取消任务失败: ",
            error_fields={"task_id": task_id},
        )

    @mcp.tool()
    def move_to_home_position(
        ip: Optional[str] = None,
        velocity: float = 0.5,
        acceleration: float = 0.5,
    ) -> dict:
        """移动机械臂到默认原点位置

        Args:
            ip: 可选的 IP 地址
            velocity: 速度 (默认 0.5)
            acceleration: 加速度 (默认 0.5)

        默认原点关节角度（度）从配置文件读取: DEFAULT_HOME_JOINTS_DEGREES
        """
        # 从配置文件读取默认原点关节角度（度）
        home_joints_degrees = DEFAULT_HOME_JOINTS_DEGREES.copy()
        # 转换为弧度
        home_joints_radians = [math.radians(deg) for deg in home_joints_degrees]

        # 参数验证
        try:
            validated_joints = validate_joints(home_joints_radians, "home_joints")
            validated_velocity = validate_velocity(velocity, "velocity")
            validated_acceleration = validate_acceleration(acceleration, "acceleration")
        except ValueError as e:
            return {
                "success": False,
                "error": "INVALID_PARAMETERS",
                "message": str(e),
                "ip": ip or "N/A",
                "result": None,
            }

        def action():
            result = robot_control.controller.move_joint_positions(
                validated_joints, validated_velocity, validated_acceleration
            )
            return {
                **result,
                "home_joints_degrees": home_joints_degrees,
                "home_joints_radians": home_joints_radians,
                "message": "机械臂正在移动到默认原点位置",
            }

        return _execute_robot_action(
            action=action,
            ip=ip,
            raise_on_mismatch=True,
            error_code="MOVE_TO_HOME_FAILED",
            error_prefix="移动到原点位置失败: ",
            error_fields={"result": None},
        )
