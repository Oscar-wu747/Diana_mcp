"""工具函数和辅助类"""

import sys
from io import StringIO
from typing import Optional


class SuppressRobotOutput:
    """临时抑制机械臂库的输出"""
    def __init__(self):
        self.stdout_buffer = StringIO()
        self.stderr_buffer = StringIO()
        self.original_stdout = None
        self.original_stderr = None
    
    def __enter__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self.stdout_buffer
        sys.stderr = self.stderr_buffer
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        # 将输出保存到日志文件
        output = self.stdout_buffer.getvalue() + self.stderr_buffer.getvalue()
        if output:
            try:
                from .config import DATA_DIR
                ROBOT_LIB_LOG = DATA_DIR / 'robot_lib.log'
                with open(ROBOT_LIB_LOG, 'a', encoding='utf-8') as f:
                    f.write(output)
            except Exception:
                pass  # 忽略日志写入错误
        return False


def _normalize_ip(ip: Optional[str]) -> Optional[str]:
    """规范化 IP 参数，处理字符串 "null" 和不完整的 IP"""
    from .config import DEFAULT_ROBOT_IP
    
    # 处理 None、空字符串、字符串 "null" 或 "None"
    if not ip or ip == "null" or ip == "None" or not ip.strip():
        return None
    
    # 验证 IP 格式（简单检查：至少包含 3 个点）
    if ip.count('.') < 3:
        return None
    
    return ip


def _get_ip_or_default(ip: Optional[str]) -> str:
    """获取 IP 地址，如果为空则返回默认 IP"""
    from .config import DEFAULT_ROBOT_IP
    normalized_ip = _normalize_ip(ip)
    return normalized_ip if normalized_ip else DEFAULT_ROBOT_IP


def _parse_array_param(param, param_name: str = "array") -> list:
    """解析数组参数，支持 list 和 JSON 字符串格式
    
    Args:
        param: 可以是 list 或 str (JSON 格式)
        param_name: 参数名称，用于错误信息
    
    Returns:
        解析后的列表
    
    Raises:
        ValueError: 如果参数格式无效
    """
    if param is None:
        return None
    
    # 如果已经是列表，直接返回
    if isinstance(param, list):
        return param
    
    # 如果是字符串，尝试解析为 JSON
    if isinstance(param, str):
        try:
            import json
            parsed = json.loads(param)
            if isinstance(parsed, list):
                return parsed
            else:
                raise ValueError(f"{param_name} 参数必须是数组格式")
        except json.JSONDecodeError as e:
            raise ValueError(f"{param_name} 参数 JSON 解析失败: {e}")
    
    raise ValueError(f"{param_name} 参数必须是 list 或 JSON 字符串格式")


def ensure_robot_connected(ip: Optional[str], raise_on_mismatch: bool = False) -> tuple[str, Optional[dict]]:
    """确保机械臂已连接，返回实际使用的 IP 和错误信息（如果有）
    
    Args:
        ip: 可选的 IP 地址
        raise_on_mismatch: 如果 IP 不匹配是否抛出异常（True）或返回错误（False）
    
    Returns:
        (实际使用的 IP, 错误信息字典或 None)
    """
    from .robot_loader import robot_control
    from .config import DEFAULT_ROBOT_IP, get_net_info
    
    normalized_ip = _normalize_ip(ip)
    
    # 检查是否已连接
    if not robot_control.controller.is_connected:
        # 使用规范化后的 IP 或默认 IP
        actual_ip = normalized_ip if normalized_ip else DEFAULT_ROBOT_IP
        net_info = get_net_info(actual_ip)
        # 抑制机械臂库的输出
        with SuppressRobotOutput():
            robot_control.controller.ensure_connected(net_info=net_info)
        return actual_ip, None
    elif normalized_ip and normalized_ip != robot_control.controller.ip_address:
        # 如果已连接但 IP 不匹配
        error_msg = f'机械臂已连接到 {robot_control.controller.ip_address}，请先断开连接或使用正确的 IP'
        if raise_on_mismatch:
            RobotError = getattr(robot_control, 'RobotError', RuntimeError)
            raise RobotError(error_msg)
        else:
            return robot_control.controller.ip_address, {
                'success': False,
                'error': 'IP_MISMATCH',
                'message': error_msg,
                'ip': robot_control.controller.ip_address,
                'requested_ip': normalized_ip,
            }
    
    # 如果 normalized_ip 为 None（即传入的是 null/None/空），直接使用已连接的 IP
    return robot_control.controller.ip_address, None