from .config import DATA_DIR, AUDIT_LOG, now_ts

# Error message templates - centralized error message management
ERROR_MESSAGES = {
    "ROBOT_NOT_CONNECTED": "机器人未连接，请先连接机器人",
    "INVALID_IP": "无效的IP地址格式",
    "CONNECTION_FAILED": "连接机器人失败，请检查网络和控制器状态",
    "GET_JOINT_POS_FAILED": "获取关节位置失败",
    "MOVE_FAILED": "执行运动失败",
    "STOP_FAILED": "停止运动失败",
    "CONNECT_FAILED": "连接机器人失败",
    "DISCONNECT_FAILED": "断开机器人失败",
    "ROBOT_LIBRARY_NOT_AVAILABLE": "机器人库不可用",
    "FILE_OPERATION_FAILED": "文件操作失败",
    "INVALID_PARAMETERS": "参数无效",
    "UNKNOWN_ERROR": "未知错误"
}

def log(message: str) -> None:
    """记录日志消息"""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_LOG, 'a', encoding='utf-8') as af:
            af.write(f"{now_ts()} {message}\n")
    except Exception:
        # best-effort logging; swallow errors to avoid crashing server
        pass

def log_exception(exc: Exception, prefix: str = '') -> None:
    """记录异常信息"""
    log(f"{prefix}{exc!r}")

def get_error_message(error_key: str, **kwargs) -> str:
    """根据错误键获取错误消息"""
    message = ERROR_MESSAGES.get(error_key, ERROR_MESSAGES["UNKNOWN_ERROR"])
    if kwargs:
        message = message.format(**kwargs)
    return message

class RobotControlError(Exception):
    """机器人控制错误"""

    def __init__(self, error_key: str, **kwargs):
        self.error_key = error_key
        self.message = get_error_message(error_key, **kwargs)
        super().__init__(self.message)
