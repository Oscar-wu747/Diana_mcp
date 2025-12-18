"""MCP工具函数"""

from typing import Optional, Union, Any
from fastmcp import Context
from .utils import SuppressRobotOutput, _normalize_ip, _get_ip_or_default, ensure_robot_connected, _parse_array_param
from .robot_loader import robot_control
from .config import get_net_info
from .error_handler import log_exception, RobotControlError


def register_tools(mcp):
    """注册所有MCP工具"""

    @mcp.tool()
    async def connect_robot(ip: Optional[str] = None, ctx: Context = None) -> dict:
        """显式连接机械臂
        
        Args:
            ip: 机器人的 IP 地址（可选，默认使用配置的 IP）
        
        Returns:
            连接结果
        """
        original_ip = ip  # 保存原始 IP 用于错误信息
        try:
            # 规范化 IP 参数
            ip = _get_ip_or_default(ip)
            
            if ctx:
                await ctx.info(f"正在连接到机器人 {ip}...")
            
            net_info = get_net_info(ip)
            # 抑制机械臂库的输出
            with SuppressRobotOutput():
                result = robot_control.controller.connect(net_info)
            
            message = f"机械臂连接{'成功' if result.get('status') == 'connected' else '已连接'}"
            if ctx:
                await ctx.info(message)
            
            return {
                'success': True,
                'status': result.get('status', 'connected'),
                'ip': result.get('ip', ip),
                'message': message
            }
        except getattr(robot_control, 'RobotError', Exception) as exc:
            log_exception(exc, prefix='连接机械臂失败: ')
            error_msg = f"连接机械臂失败: {str(exc)}"
            if ctx:
                await ctx.info(error_msg)
            return {
                'success': False,
                'error': 'CONNECT_FAILED',
                'message': error_msg,
                'ip': ip if 'ip' in locals() else (original_ip or 'N/A'),
                'original_ip': original_ip if original_ip else None
            }
        except Exception as exc:
            log_exception(exc, prefix='连接机械臂失败(未知错误): ')
            error_msg = f"未知错误: {str(exc)}"
            if ctx:
                await ctx.info(error_msg)
            return {
                'success': False,
                'error': 'UNKNOWN_ERROR',
                'message': error_msg,
                'ip': ip if 'ip' in locals() else (original_ip or 'N/A'),
                'original_ip': original_ip if original_ip else None
            }

    @mcp.tool()
    async def disconnect_robot(ctx: Context = None) -> dict:
        """显式断开机械臂连接
        
        Returns:
            断开连接结果
        """
        try:
            if ctx:
                await ctx.info("正在断开与机器人的连接...")
            
            # 抑制机械臂库的输出
            with SuppressRobotOutput():
                result = robot_control.controller.disconnect()
            
            message = f"机械臂{'已断开连接' if result.get('status') == 'disconnected' else '未连接'}"
            if ctx:
                await ctx.info(message)
            
            return {
                'success': True,
                'status': result.get('status', 'disconnected'),
                'message': message
            }
        except getattr(robot_control, 'RobotError', Exception) as exc:
            log_exception(exc, prefix='断开机械臂连接失败: ')
            error_msg = f"断开机械臂连接失败: {str(exc)}"
            if ctx:
                await ctx.info(error_msg)
            return {
                'success': False,
                'error': 'DISCONNECT_FAILED',
                'message': error_msg
            }
        except Exception as exc:
            log_exception(exc, prefix='断开机械臂连接失败(未知错误): ')
            error_msg = f"未知错误: {str(exc)}"
            if ctx:
                await ctx.info(error_msg)
            return {
                'success': False,
                'error': 'UNKNOWN_ERROR',
                'message': error_msg
            }

    @mcp.tool()
    def get_joint_positions(ip: Optional[str] = None) -> dict:
        """获取机械臂关节位置"""
        try:
            # 确保连接，不抛出异常，返回错误信息
            actual_ip, error = ensure_robot_connected(ip, raise_on_mismatch=False)
            if error:
                error['joints'] = []
                error['joint_count'] = 0
                return error

            # 抑制机械臂库的输出
            with SuppressRobotOutput():
                joints = robot_control.controller.get_joint_positions()
            return {
                'success': True,
                'ip': robot_control.controller.ip_address,
                'joints': joints,
                'joint_count': len(joints)
            }
        except getattr(robot_control, 'RobotError', Exception) as exc:
            log_exception(exc, prefix='获取关节位置失败: ')
            return {
                'success': False,
                'error': 'GET_JOINT_POS_FAILED',
                'message': f"获取关节位置失败: {str(exc)}",
                'ip': ip or 'N/A',
                'joints': [],
                'joint_count': 0
            }
        except Exception as exc:
            log_exception(exc, prefix='获取关节位置失败(未知错误): ')
            return {
                'success': False,
                'error': 'UNKNOWN_ERROR',
                'message': f"未知错误: {str(exc)}",
                'ip': ip or 'N/A',
                'joints': [],
                'joint_count': 0
            }

    @mcp.tool()
    def move_joint_positions(ip: Optional[str] = None, joints: Optional[list] = None, velocity: float = 0.5, acceleration: float = 0.5) -> dict:
        """以关节模式移动机械臂（7 个关节值）
        
        Args:
            ip: 可选的 IP 地址
            joints: 关节角度数组（弧度），7 个值
            velocity: 速度 (默认 0.5)
            acceleration: 加速度 (默认 0.5)
        """
        try:
            if not joints or len(joints) != 7:
                return {
                    'success': False,
                    'error': 'INVALID_PARAMETERS',
                    'message': '关节移动需要 7 个关节值',
                    'ip': ip or 'N/A',
                    'result': None
                }

            # 确保连接，IP 不匹配时抛出异常
            actual_ip, error = ensure_robot_connected(ip, raise_on_mismatch=True)

            # 抑制机械臂库的输出
            with SuppressRobotOutput():
                result = robot_control.controller.move_joint_positions(joints, velocity, acceleration)
            # 返回控制器 ip 与 move 的结果（如 taskId / status）
            return {
                'success': True,
                'ip': robot_control.controller.ip_address,
                'result': result
            }
        except getattr(robot_control, 'RobotError', Exception) as exc:
            log_exception(exc, prefix='执行关节运动失败: ')
            return {
                'success': False,
                'error': 'MOVE_FAILED',
                'message': f"执行关节运动失败: {str(exc)}",
                'ip': ip or 'N/A',
                'result': None
            }
        except Exception as exc:
            log_exception(exc, prefix='执行关节运动失败(未知错误): ')
            return {
                'success': False,
                'error': 'UNKNOWN_ERROR',
                'message': f"未知错误: {str(exc)}",
                'ip': ip or 'N/A',
                'result': None
            }
    
    @mcp.tool()
    def move_joint_positions_json(ip: Optional[str] = None, joints_json: str = "", velocity: float = 0.5, acceleration: float = 0.5) -> dict:
        """以关节模式移动机械臂（7 个关节值，JSON 字符串格式）
        
        Args:
            ip: 可选的 IP 地址
            joints_json: 关节角度数组的 JSON 字符串格式，如 '[-1.48, -0.42, 0.29, 2.27, 0.12, -1.05, -0.05]'
            velocity: 速度 (默认 0.5)
            acceleration: 加速度 (默认 0.5)
        """
        try:
            # 解析 JSON 字符串
            try:
                joints = _parse_array_param(joints_json, "joints_json")
            except ValueError as e:
                return {
                    'success': False,
                    'error': 'INVALID_PARAMETERS',
                    'message': f"关节参数 JSON 格式错误: {str(e)}",
                    'ip': ip or 'N/A',
                    'result': None
                }
            
            if not joints or len(joints) != 7:
                return {
                    'success': False,
                    'error': 'INVALID_PARAMETERS',
                    'message': '关节移动需要 7 个关节值',
                    'ip': ip or 'N/A',
                    'result': None
                }

            # 确保连接，IP 不匹配时抛出异常
            actual_ip, error = ensure_robot_connected(ip, raise_on_mismatch=True)

            # 抑制机械臂库的输出
            with SuppressRobotOutput():
                result = robot_control.controller.move_joint_positions(joints, velocity, acceleration)
            # 返回控制器 ip 与 move 的结果（如 taskId / status）
            return {
                'success': True,
                'ip': robot_control.controller.ip_address,
                'result': result
            }
        except getattr(robot_control, 'RobotError', Exception) as exc:
            log_exception(exc, prefix='执行关节运动失败: ')
            return {
                'success': False,
                'error': 'MOVE_FAILED',
                'message': f"执行关节运动失败: {str(exc)}",
                'ip': ip or 'N/A',
                'result': None
            }
        except Exception as exc:
            log_exception(exc, prefix='执行关节运动失败(未知错误): ')
            return {
                'success': False,
                'error': 'UNKNOWN_ERROR',
                'message': f"未知错误: {str(exc)}",
                'ip': ip or 'N/A',
                'result': None
            }
    
    @mcp.tool()
    def move_linear_pose(ip: Optional[str] = None, pose: Optional[list] = None, velocity: float = 0.2, acceleration: float = 0.2) -> dict:
        """以 TCP 直线模式移动机械臂（6 元 pose）
        
        Args:
            ip: 可选的 IP 地址
            pose: TCP 姿态数组 [x, y, z, rx, ry, rz]，6 个值
            velocity: 速度 (默认 0.2)
            acceleration: 加速度 (默认 0.2)
        """
        try:
            if not pose or len(pose) != 6:
                return {
                    'success': False,
                    'error': 'INVALID_PARAMETERS',
                    'message': '直线移动需要 6 个姿态值',
                    'ip': ip or 'N/A',
                    'result': None
                }

            # 确保连接，IP 不匹配时抛出异常
            actual_ip, error = ensure_robot_connected(ip, raise_on_mismatch=True)

            # 抑制机械臂库的输出
            with SuppressRobotOutput():
                result = robot_control.controller.move_linear_pose(pose, velocity, acceleration)
            return {
                'success': True,
                'ip': robot_control.controller.ip_address,
                'result': result
            }
        except getattr(robot_control, 'RobotError', Exception) as exc:
            log_exception(exc, prefix='执行直线运动失败: ')
            return {
                'success': False,
                'error': 'MOVE_FAILED',
                'message': f"执行直线运动失败: {str(exc)}",
                'ip': ip or 'N/A',
                'result': None
            }
        except Exception as exc:
            log_exception(exc, prefix='执行直线运动失败(未知错误): ')
            return {
                'success': False,
                'error': 'UNKNOWN_ERROR',
                'message': f"未知错误: {str(exc)}",
                'ip': ip or 'N/A',
                'result': None
            }

    @mcp.tool()
    def get_tcp_pose(ip: Optional[str] = None) -> dict:
        """获取机械臂TCP位置"""
        try:
            # 确保连接，不抛出异常，返回错误信息
            actual_ip, error = ensure_robot_connected(ip, raise_on_mismatch=False)
            if error:
                error['tcp_pose'] = []
                return error

            # 抑制机械臂库的输出
            with SuppressRobotOutput():
                tcp_pose = robot_control.controller.get_tcp_pose()
            return {
                'success': True,
                'ip': robot_control.controller.ip_address,
                'tcp_pose': tcp_pose,
            }
        except getattr(robot_control, 'RobotError', Exception) as exc:
            log_exception(exc, prefix='获取TCP位置失败: ')
            return {
                'success': False,
                'error': 'GET_TCP_POSE_FAILED',
                'message': f"获取TCP位置失败: {str(exc)}",
                'ip': ip or 'N/A',
                'tcp_pose': [],
            }
        except Exception as exc:
            log_exception(exc, prefix='获取TCP位置失败(未知错误): ')
            return {
                'success': False,
                'error': 'UNKNOWN_ERROR',
                'message': f"未知错误: {str(exc)}",
                'ip': ip or 'N/A',
                'tcp_pose': [],
            }

    @mcp.tool()
    def get_robot_state(ip: Optional[str] = None) -> dict:
        """获取机械臂状态"""
        try:
            # 确保连接，不抛出异常，返回错误信息
            actual_ip, error = ensure_robot_connected(ip, raise_on_mismatch=False)
            if error:
                error['robot_state'] = {}
                return error

            # 抑制机械臂库的输出
            with SuppressRobotOutput():
                robot_state = robot_control.controller.get_robot_state()
            return {
                'success': True,
                'ip': robot_control.controller.ip_address,
                'robot_state': robot_state,
            }
        except getattr(robot_control, 'RobotError', Exception) as exc:
            log_exception(exc, prefix='获取机器人状态失败: ')
            return {
                'success': False,
                'error': 'GET_ROBOT_STATE_FAILED',
                'message': f"获取机器人状态失败: {str(exc)}",
                'ip': ip or 'N/A',
                'robot_state': {},
            }
        except Exception as exc:
            log_exception(exc, prefix='获取机器人状态失败(未知错误): ')
            return {
                'success': False,
                'error': 'UNKNOWN_ERROR',
                'message': f"未知错误: {str(exc)}",
                'ip': ip or 'N/A',
                'robot_state': {},
            }

    @mcp.tool()
    def resume_motion(ip: Optional[str] = None) -> dict:
        """恢复机械臂运动"""
        try:
            # 确保连接，IP 不匹配时抛出异常
            actual_ip, error = ensure_robot_connected(ip, raise_on_mismatch=True)

            # 抑制机械臂库的输出
            with SuppressRobotOutput():
                result = robot_control.controller.resume_motion()
            return {
                'success': True,
                'ip': robot_control.controller.ip_address,
                'result': result
            }
        except getattr(robot_control, 'RobotError', Exception) as exc:
            log_exception(exc, prefix='恢复运动失败: ')
            return {
                'success': False,
                'error': 'RESUME_FAILED',
                'message': f"恢复运动失败: {str(exc)}",
                'ip': ip or 'N/A',
                'result': None
            }
        except Exception as exc:
            log_exception(exc, prefix='恢复运动失败(未知错误): ')
            return {
                'success': False,
                'error': 'UNKNOWN_ERROR',
                'message': f"未知错误: {str(exc)}",
                'ip': ip or 'N/A',
                'result': None
            }

    @mcp.tool()
    def enable_free_driving(ip: Optional[str] = None, mode: int = 1) -> dict:
        """启用机械臂自由驱动模式
        
        Args:
            mode: 自由驱动模式 (0: 禁用, 1: 正常, 2: 强制)
        """
        try:
            # 确保连接，IP 不匹配时抛出异常
            actual_ip, error = ensure_robot_connected(ip, raise_on_mismatch=True)

            # 抑制机械臂库的输出
            with SuppressRobotOutput():
                result = robot_control.controller.enable_free_driving(mode)
            return {
                'success': True,
                'ip': robot_control.controller.ip_address,
                'result': result
            }
        except getattr(robot_control, 'RobotError', Exception) as exc:
            log_exception(exc, prefix='启用自由驱动失败: ')
            return {
                'success': False,
                'error': 'FREE_DRIVING_FAILED',
                'message': f"启用自由驱动失败: {str(exc)}",
                'ip': ip or 'N/A',
                'result': None
            }
        except Exception as exc:
            log_exception(exc, prefix='启用自由驱动失败(未知错误): ')
            return {
                'success': False,
                'error': 'UNKNOWN_ERROR',
                'message': f"未知错误: {str(exc)}",
                'ip': ip or 'N/A',
                'result': None
            }

    @mcp.tool()
    def move_tcp_direction(ip: Optional[str] = None, direction: int = 0, velocity: float = 0.2, acceleration: float = 0.2) -> dict:
        """以TCP方向移动机械臂"""
        try:
            # 确保连接，IP 不匹配时抛出异常
            actual_ip, error = ensure_robot_connected(ip, raise_on_mismatch=True)

            # 抑制机械臂库的输出
            with SuppressRobotOutput():
                result = robot_control.controller.move_tcp_direction(direction, velocity, acceleration)
            return {
                'success': True,
                'ip': robot_control.controller.ip_address,
                'result': result
            }
        except getattr(robot_control, 'RobotError', Exception) as exc:
            log_exception(exc, prefix='TCP方向移动失败: ')
            return {
                'success': False,
                'error': 'MOVE_TCP_FAILED',
                'message': f"TCP方向移动失败: {str(exc)}",
                'ip': ip or 'N/A',
                'result': None
            }
        except Exception as exc:
            log_exception(exc, prefix='TCP方向移动失败(未知错误): ')
            return {
                'success': False,
                'error': 'UNKNOWN_ERROR',
                'message': f"未知错误: {str(exc)}",
                'ip': ip or 'N/A',
                'result': None
            }

    @mcp.tool()
    def rotate_tcp_direction(ip: Optional[str] = None, direction: int = 0, velocity: float = 0.2, acceleration: float = 0.2) -> dict:
        """旋转TCP方向"""
        try:
            # 确保连接，IP 不匹配时抛出异常
            actual_ip, error = ensure_robot_connected(ip, raise_on_mismatch=True)

            # 抑制机械臂库的输出
            with SuppressRobotOutput():
                result = robot_control.controller.rotate_tcp_direction(direction, velocity, acceleration)
            return {
                'success': True,
                'ip': robot_control.controller.ip_address,
                'result': result
            }
        except getattr(robot_control, 'RobotError', Exception) as exc:
            log_exception(exc, prefix='TCP旋转失败: ')
            return {
                'success': False,
                'error': 'ROTATE_TCP_FAILED',
                'message': f"TCP旋转失败: {str(exc)}",
                'ip': ip or 'N/A',
                'result': None
            }
        except Exception as exc:
            log_exception(exc, prefix='TCP旋转失败(未知错误): ')
            return {
                'success': False,
                'error': 'UNKNOWN_ERROR',
                'message': f"未知错误: {str(exc)}",
                'ip': ip or 'N/A',
                'result': None
            }

    @mcp.tool()
    def stop_motion(ip: Optional[str] = None) -> dict:
        """立即停止机械臂的运动"""
        try:
            # 确保连接，IP 不匹配时抛出异常
            actual_ip, error = ensure_robot_connected(ip, raise_on_mismatch=True)

            # 抑制机械臂库的输出
            with SuppressRobotOutput():
                result = robot_control.controller.stop_motion()
            return {
                'success': True,
                'ip': robot_control.controller.ip_address,
                'result': result
            }
        except getattr(robot_control, 'RobotError', Exception) as exc:
            log_exception(exc, prefix='停止运动失败: ')
            return {
                'success': False,
                'error': 'STOP_FAILED',
                'message': f"停止运动失败: {str(exc)}",
                'ip': ip or 'N/A',
                'result': None
            }
        except Exception as exc:
            log_exception(exc, prefix='停止运动失败(未知错误): ')
            return {
                'success': False,
                'error': 'UNKNOWN_ERROR',
                'message': f"未知错误: {str(exc)}",
                'ip': ip or 'N/A',
                'result': None
            }