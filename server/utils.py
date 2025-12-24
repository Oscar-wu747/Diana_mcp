"""工具函数和辅助类"""

import os
import sys
from io import StringIO
from typing import Optional


class SuppressRobotOutput:
    """临时抑制机械臂库的输出（包括C扩展直接写入文件描述符的输出）"""

    def __init__(self):
        self.stdout_buffer = StringIO()
        self.stderr_buffer = StringIO()
        self.original_stdout = None
        self.original_stderr = None
        self.original_stdout_fd = None
        self.original_stderr_fd = None
        self.saved_stdout_fd = None
        self.saved_stderr_fd = None
        self.devnull_fd = None

    def __enter__(self):
        # 保存原始的stdout和stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.original_stdout_fd = sys.stdout.fileno()
        self.original_stderr_fd = sys.stderr.fileno()

        # 保存原始文件描述符的副本（用于恢复）
        self.saved_stdout_fd = os.dup(self.original_stdout_fd)
        self.saved_stderr_fd = os.dup(self.original_stderr_fd)

        # 打开/dev/null用于重定向
        self.devnull_fd = os.open(os.devnull, os.O_WRONLY)

        # 在文件描述符级别重定向stdout和stderr到/dev/null
        # 这样可以捕获C扩展直接写入文件描述符的输出
        os.dup2(self.devnull_fd, self.original_stdout_fd)
        os.dup2(self.devnull_fd, self.original_stderr_fd)

        # 同时重定向Python的sys.stdout和sys.stderr
        sys.stdout = self.stdout_buffer
        sys.stderr = self.stderr_buffer

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 恢复Python的sys.stdout和sys.stderr
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

        # 恢复文件描述符级别的重定向
        if self.saved_stdout_fd is not None and self.original_stdout_fd is not None:
            saved_fd = self.saved_stdout_fd
            original_fd = self.original_stdout_fd
            os.dup2(saved_fd, original_fd)
            os.close(saved_fd)
        if self.saved_stderr_fd is not None and self.original_stderr_fd is not None:
            saved_fd = self.saved_stderr_fd
            original_fd = self.original_stderr_fd
            os.dup2(saved_fd, original_fd)
            os.close(saved_fd)

        # 关闭/dev/null文件描述符
        if self.devnull_fd is not None:
            os.close(self.devnull_fd)

        # 将输出保存到日志文件（虽然大部分输出已被重定向到/dev/null）
        output = self.stdout_buffer.getvalue() + self.stderr_buffer.getvalue()
        if output:
            try:
                from .config import DATA_DIR

                ROBOT_LIB_LOG = DATA_DIR / "robot_lib.log"
                with open(ROBOT_LIB_LOG, "a", encoding="utf-8") as f:
                    f.write(output)
            except Exception:
                pass  # 忽略日志写入错误
        return False


def normalize_ip(ip: Optional[str]) -> Optional[str]:
    """规范化 IP 参数，处理字符串 "null" 和不完整的 IP

    Args:
        ip: 原始 IP 地址字符串

    Returns:
        规范化后的 IP 地址，如果无效则返回 None
    """
    # 处理 None、空字符串、字符串 "null" 或 "None"
    if not ip or ip == "null" or ip == "None" or not ip.strip():
        return None

    # 验证 IP 格式（简单检查：至少包含 3 个点）
    if ip.count(".") < 3:
        return None

    return ip


def _normalize_ip(ip: Optional[str]) -> Optional[str]:
    """规范化 IP 参数（私有函数，保持向后兼容）"""
    return normalize_ip(ip)


def _get_ip_or_default(ip: Optional[str]) -> str:
    """获取 IP 地址，如果为空则返回默认 IP"""
    from .config import DEFAULT_ROBOT_IP

    normalized_ip = normalize_ip(ip)
    return normalized_ip if normalized_ip else DEFAULT_ROBOT_IP


def _parse_array_param(param, param_name: str = "array") -> list:
    """解析数组参数，支持 list 和 JSON 字符串格式

    Args:
        param: 可以是 list 或 str (JSON 格式)
        param_name: 参数名称，用于错误信息

    Returns:
        解析后的列表

    Raises:
        ValueError: 如果参数格式无效或为 None
    """
    if param is None:
        raise ValueError(f"{param_name} 参数不能为 None")

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


def check_connection(
    normalized_ip: Optional[str], raise_on_mismatch: bool = False
) -> tuple[bool, Optional[str], Optional[dict]]:
    """检查机械臂连接状态和IP匹配情况

    Args:
        normalized_ip: 规范化后的IP地址（可能为None）
        raise_on_mismatch: 如果IP不匹配是否抛出异常（True）或返回错误（False）

    Returns:
        (is_connected, current_ip, error_dict_or_None)
        - is_connected: 是否已连接
        - current_ip: 当前连接的IP地址（如果已连接）
        - error_dict_or_None: 如果有错误则返回错误字典，否则为None

    Raises:
        RobotError: 如果raise_on_mismatch=True且IP不匹配
    """
    from .robot_loader import robot_control

    # 如果未连接
    if not robot_control.controller.is_connected:
        return False, None, None

    current_ip = robot_control.controller.ip_address

    # 如果已连接，检查IP是否匹配
    if normalized_ip and normalized_ip != current_ip:
        error_msg = f"机械臂已连接到 {current_ip}，请先断开连接或使用正确的 IP"
        if raise_on_mismatch:
            RobotError = getattr(robot_control, "RobotError", RuntimeError)
            raise RobotError(error_msg)
        else:
            return (
                True,
                current_ip,
                {
                    "success": False,
                    "error": "IP_MISMATCH",
                    "message": error_msg,
                    "ip": current_ip,
                    "requested_ip": normalized_ip,
                },
            )

    # 连接正常，IP匹配或未指定IP
    return True, current_ip, None


def connect_if_needed(target_ip: str) -> str:
    """如果需要则连接机械臂

    Args:
        target_ip: 目标IP地址（必须是非None的字符串）

    Returns:
        实际使用的IP地址

    Raises:
        RobotError: 如果连接失败
    """
    from .config import get_net_info
    from .robot_loader import robot_control

    # 如果已连接，直接返回当前IP
    if robot_control.controller.is_connected:
        return robot_control.controller.ip_address

    # 需要连接
    net_info = get_net_info(target_ip)
    # 抑制机械臂库的输出
    with SuppressRobotOutput():
        robot_control.controller.ensure_connected(net_info=net_info)

    return robot_control.controller.ip_address


def ensure_robot_connected(
    ip: Optional[str], raise_on_mismatch: bool = False
) -> tuple[str, Optional[dict]]:
    """确保机械臂已连接，返回实际使用的 IP 和错误信息（如果有）

    这是一个组合函数，内部调用 normalize_ip、check_connection 和 connect_if_needed。

    Args:
        ip: 可选的 IP 地址
        raise_on_mismatch: 如果 IP 不匹配是否抛出异常（True）或返回错误（False）

    Returns:
        (实际使用的 IP, 错误信息字典或 None)
    """
    from .config import DEFAULT_ROBOT_IP

    # 1. IP规范化
    normalized_ip = normalize_ip(ip)

    # 2. 检查连接状态和IP匹配情况
    is_connected, current_ip, error = check_connection(normalized_ip, raise_on_mismatch)

    # 如果有错误（IP不匹配），直接返回
    if error:
        # 当有错误时，current_ip 必须是字符串（来自 check_connection 的逻辑）
        if current_ip is None:
            # 理论上不应该发生，但为了类型安全提供回退
            return DEFAULT_ROBOT_IP, error
        return current_ip, error

    # 3. 如果需要则连接
    if not is_connected:
        # 使用规范化后的IP或默认IP
        target_ip = normalized_ip if normalized_ip else DEFAULT_ROBOT_IP
        actual_ip = connect_if_needed(target_ip)
        return actual_ip, None

    # 已连接，返回当前IP
    # 当 is_connected=True 且 error=None 时，current_ip 必须是字符串
    if current_ip is None:
        # 理论上不应该发生，但为了类型安全提供回退
        return DEFAULT_ROBOT_IP, None
    return current_ip, None
