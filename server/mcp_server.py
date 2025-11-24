#!/usr/bin/env python3
from typing import Optional

"""Minimal MCP server for robot arm position retrieval.

This version centralizes paths and logging via `server.config` and
`server.error_handler` and keeps only the basic MCP tools required by the
agent: reading joint positions and reading the target file.
"""

import os
import sys
import importlib.util
import types
import hashlib
from pathlib import Path
from fastmcp import FastMCP

from .config import TARGET_PATH, SRC_DIR, DATA_DIR, ensure_dirs
from .error_handler import log_exception, log

# Ensure data dirs exist
ensure_dirs()


def _load_robot_control():
    """Load `diana_api.control` and return a module-like object.

    If loading fails, return a minimal stub exposing `RobotError` and
    `controller` with the same API used by the MCP tools so callers can
    still import symbols and the server remains responsive.
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
        log_exception(exc, prefix='Failed to load diana_api control: ')

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
        # Log and re-raise to allow MCP client to see original error
        log_exception(exc, prefix='get_joint_positions failed: ')
        raise


@mcp.tool()
def read_target_file() -> str:
    """Return content of the target file (text)."""
    try:
        with open(TARGET_PATH, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception as exc:
        log_exception(exc, prefix='read_target_file failed: ')
        raise


@mcp.tool()
def write_target_file(content: str, message: Optional[str] = None) -> dict:
    """Create a backup of `content` and atomically replace the target file.

    Returns a dict with the backup filename and metadata.
    """
    ts = __import__('datetime').datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    sha1 = hashlib.sha1(content.encode('utf-8')).hexdigest()
    fname = f'{ts}_{sha1[:8]}.py'
    dest = DATA_DIR / fname

    meta = {'timestamp': ts, 'sha1': sha1, 'message': message or ''}
    try:
        with open(dest, 'w', encoding='utf-8') as bf:
            bf.write('# MCP version backup\\n')
            bf.write('# ' + __import__('json').dumps(meta, ensure_ascii=False) + '\\n')
            bf.write(content)

        # Ensure target directory exists before atomic replace
        TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = TARGET_PATH.with_name(TARGET_PATH.name + '.mcp.tmp')
        with open(tmp, 'w', encoding='utf-8') as tf:
            tf.write(content)
        os.replace(tmp, TARGET_PATH)

        log(f'write_target_file: created {fname}')
        return {'version': fname, 'meta': meta}
    except Exception as exc:
        log_exception(exc, prefix='write_target_file failed: ')
        raise


def main():
    # Ensure target exists
    if not TARGET_PATH.is_file():
        TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TARGET_PATH, 'w', encoding='utf-8') as f:
            f.write('# DianaApi placeholder created by mcp_server\\\\n')

    mcp.run()


if __name__ == '__main__':
    main()
