#!/usr/bin/env python3
from typing import Optional


"""Simple MCP server for robot arm control using fastmcp."""

import os
import sys
import json
import datetime
import importlib.util
import types
from pathlib import Path
import hashlib
from fastmcp import FastMCP

# Path configuration
SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
SRC_DIR = PROJECT_ROOT / 'src'
TARGET_PATH = SRC_DIR / 'diana_api' / 'diana_api.py'
DATA_DIR = PROJECT_ROOT / 'var' / 'mcp'
AUDIT_LOG = DATA_DIR / 'audit.log'

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

def _now_ts():
    """Return UTC timestamp as compact string."""
    return datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

def _load_robot_control():
    """Load `diana_api` package and return its `control` submodule.

    Returns a stub module if loading fails so callers can still import symbols.
    """
    init_file = SRC_DIR / 'diana_api' / '__init__.py'
    spec = importlib.util.spec_from_file_location('diana_api', init_file)
    if spec is None or spec.loader is None:
        raise RuntimeError('Unable to locate diana_api package at src/diana_api')
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault('diana_api', module)
    try:
        spec.loader.exec_module(module)
        return module.control
    except Exception as exc:
        # log and provide a minimal stub so the server remains responsive
        try:
            with open(DATA_DIR / 'load_error.log', 'a', encoding='utf-8') as ef:
                ef.write(f"{_now_ts()} Failed to load diana_api control module: {exc!r}\n")
        except Exception:
            pass

        class RobotError(RuntimeError):
            pass

        class _StubController:
            def __init__(self):
                self._ip = None

            @property
            def ip_address(self):
                return self._ip

            def ensure_connected(self, *, ip=None, _net_info=None):
                raise RobotError('robot library not available')

            def get_joint_positions(self):
                raise RobotError('robot library not available')

        # Use a simple namespace to hold the stub attributes (silences type checks)
        ctrl_mod = types.SimpleNamespace(RobotError=RobotError, controller=_StubController())
        return ctrl_mod

# Load robot control
robot_control = _load_robot_control()

# Initialize FastMCP server
mcp = FastMCP("Robot Control Server")

@mcp.tool()
def get_joint_positions(ip: Optional[str] = None):
    """Get current joint positions of the robot arm.
    
    Args:
        ip: IP address of the robot (if not already connected)
        
    Returns:
        dict: Dictionary containing IP address and joint positions
    """
    try:
        robot_control.controller.ensure_connected(ip=ip)
        joints = robot_control.controller.get_joint_positions()
        return {'ip': robot_control.controller.ip_address, 'joints': joints}
    except getattr(robot_control, 'RobotError', Exception) as exc:
        # propagate the original robot-related error
        raise

@mcp.tool()
def read_target_file() -> str:
    """Return content of the target file (text)."""
    with open(TARGET_PATH, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

@mcp.tool()
def write_target_file(content: str, message: Optional[str] = None) -> dict:
    """Create a backup of `content` and atomically replace the target file.

    Returns a dict with the backup filename and metadata.
    """
    ts = _now_ts()
    sha1 = hashlib.sha1(content.encode('utf-8')).hexdigest()
    fname = f'{ts}_{sha1[:8]}.py'
    dest = DATA_DIR / fname

    meta = {'timestamp': ts, 'sha1': sha1, 'message': message or ''}
    with open(dest, 'w', encoding='utf-8') as bf:
        bf.write('# MCP version backup\n')
        bf.write('# ' + json.dumps(meta, ensure_ascii=False) + '\n')
        bf.write(content)

    # Ensure target directory exists before atomic replace
    TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = TARGET_PATH.with_name(TARGET_PATH.name + '.mcp.tmp')
    with open(tmp, 'w', encoding='utf-8') as tf:
        tf.write(content)
    os.replace(tmp, TARGET_PATH)

    try:
        with open(AUDIT_LOG, 'a', encoding='utf-8') as af:
            af.write(json.dumps({'op': 'write', 'version': fname, 'meta': meta, 'ts': _now_ts()}, ensure_ascii=False) + '\n')
    except Exception:
        pass

    return {'version': fname, 'meta': meta}

def main():
    # Ensure target exists
    if not TARGET_PATH.is_file():
        # Create an empty target to avoid crashes
        TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TARGET_PATH, 'w', encoding='utf-8') as f:
            f.write('# DianaApi placeholder created by mcp_server\\n')

    # Start the server
    mcp.run()

if __name__ == '__main__':
    main()
