from pathlib import Path
from datetime import datetime

# Basic path configuration for the simplified MCP server
SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
SRC_DIR = PROJECT_ROOT / 'src'
LIB_DIR = PROJECT_ROOT / 'lib'
DATA_DIR = PROJECT_ROOT / 'var' / 'mcp'
AUDIT_LOG = DATA_DIR / 'audit.log'

# Default robot connection settings
DEFAULT_ROBOT_IP = "192.168.10.75"
DEFAULT_PORTS = (0, 0, 0, 0, 0)

def now_ts():
    """获取当前时间戳"""
    return datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

def ensure_dirs():
    """确保必要的目录存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def get_net_info(ip: str) -> tuple:
    """生成网络连接信息元组"""
    return (ip, *DEFAULT_PORTS)
