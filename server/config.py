from pathlib import Path
from datetime import datetime

# Basic path configuration for the simplified MCP server
SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
SRC_DIR = PROJECT_ROOT / 'src'
TARGET_PATH = SRC_DIR / 'diana_api' / 'diana_api.py'
DATA_DIR = PROJECT_ROOT / 'var' / 'mcp'
AUDIT_LOG = DATA_DIR / 'audit.log'

def now_ts():
    return datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

def ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
