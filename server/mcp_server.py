#!/usr/bin/env python3
"""Simple stdio-based MCP server for managing `src/diana_api/diana_api.py`.

Supports both JSON-RPC 2.0 (`initialize`, `tools/list`, `tools/call`, etc.)
and the legacy per-line JSON protocol:
  {"op": "read"}
  {"op": "search", "query": "text"}
  {"op": "write", "content": "...", "message": "optional"}
  {"op": "list_versions"}
  {"op": "get_version", "name": "version-filename"}

Response:
  JSON-RPC: {"jsonrpc": "2.0", "id": <id>, "result": {...}}
  Legacy: {"ok": true/false, "data": ... , "error": "..."}

Start it from VSCode MCP stdio or run manually after activating `conda activate mcp-demo`.
"""

from __future__ import annotations

import os
import sys
import json
import hashlib
import datetime
import threading
import ast
import importlib.util
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
SRC_DIR = PROJECT_ROOT / 'src'
TARGET_PATH = SRC_DIR / 'diana_api' / 'diana_api.py'
DATA_DIR = PROJECT_ROOT / 'var' / 'mcp'
def _load_robot_control():
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
        # Fail gracefully: log and return a stub control object so MCP can run in read-only/limited mode
        err = f'Failed to load diana_api control module: {exc}'
        try:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(DATA_DIR / 'load_error.log', 'a', encoding='utf-8') as ef:
                ef.write(_now_ts() + ' ' + err + '\n')
        except Exception:
            pass

        # Minimal fallback control module (module-like) so callers expecting
        # `RobotError` and `controller` still work.
        import types

        class RobotError(RuntimeError):
            pass

        class _StubController:
            def __init__(self):
                self._ip = None

            @property
            def ip_address(self):
                return self._ip

            def ensure_connected(self, *, ip=None, _net_info=None):
                # stub: always raise since underlying library failed to load
                raise RobotError('robot library not available: ' + str(exc))

            def get_joint_positions(self):
                raise RobotError('robot library not available')

        ctrl_mod = types.ModuleType('diana_api.control_stub')
        ctrl_mod.RobotError = RobotError
        ctrl_mod.controller = _StubController()
        return ctrl_mod


robot_control = _load_robot_control()
VERS_DIR = DATA_DIR / 'versions'
AUDIT_LOG = DATA_DIR / 'audit.log'
PROTOCOL_VERSION = '2025-06-18'
SERVER_INFO = {'name': 'diana-mcp-server', 'version': '1.0.0'}
SERVER_CAPABILITIES = {
    'tools': {'listChanged': False},
    'resources': {'listChanged': False},
    'prompts': {'listChanged': False},
}
REGISTERED_RESOURCES = []
REGISTERED_PROMPTS = []

write_lock = threading.Lock()
shutdown_event = threading.Event()
client_state = {'initialized': False, 'clientInfo': None, 'capabilities': {}}

DATA_DIR.mkdir(parents=True, exist_ok=True)
VERS_DIR.mkdir(parents=True, exist_ok=True)


def _now_ts():
    return datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')


def _sha1(text: bytes) -> str:
    return hashlib.sha1(text).hexdigest()


def read_target() -> str:
    with open(TARGET_PATH, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def search_target(query: str):
    matches = []
    with open(TARGET_PATH, 'r', encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f, start=1):
            if query in line:
                matches.append({'line': i, 'text': line.rstrip('\n')})
    return matches


def read_target_range(start: int, end: int):
    if start is None or end is None:
        raise ValueError('start and end required')
    if start < 1:
        start = 1
    if end < start:
        return []
    out = []
    with open(TARGET_PATH, 'r', encoding='utf-8', errors='replace') as f:
        for i, line in enumerate(f, start=1):
            if i > end:
                break
            if i >= start:
                out.append({'line': i, 'text': line.rstrip('\n')})
    return out


def get_symbols():
    """Return list of top-level functions and classes with line numbers."""
    content = read_target()
    try:
        tree = ast.parse(content)
    except Exception:
        return []
    syms = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            syms.append({'type': 'function', 'name': node.name, 'line': getattr(node, 'lineno', None)})
        elif isinstance(node, ast.AsyncFunctionDef):
            syms.append({'type': 'async function', 'name': node.name, 'line': getattr(node, 'lineno', None)})
        elif isinstance(node, ast.ClassDef):
            syms.append({'type': 'class', 'name': node.name, 'line': getattr(node, 'lineno', None)})
    # sort by line
    syms.sort(key=lambda s: (s.get('line') or 0))
    return syms


def stats_target():
    content = read_target()
    raw = content.encode('utf-8')
    return {'lines': content.count('\n') + 1, 'size': len(raw), 'sha1': _sha1(raw)}


def list_versions():
    items = []
    for path in sorted(VERS_DIR.iterdir()):
        if path.is_file():
            items.append({'name': path.name, 'size': path.stat().st_size})
    return items


def get_version(name: str) -> str:
    p = VERS_DIR / name
    if not p.is_file():
        raise FileNotFoundError(name)
    with open(p, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def write_target(content: str, message: str | None = None, check_syntax: bool = True) -> dict:
    # optionally check syntax before writing
    if check_syntax:
        try:
            ast.parse(content)
        except SyntaxError as se:
            raise

    with write_lock:
        # create backup first
        raw = content.encode('utf-8')
        sha = _sha1(raw)
        ts = _now_ts()
        fname = f'{ts}_{sha[:8]}.py'
        dest = VERS_DIR / fname
        # store metadata header as JSON at start of file
        meta = {'timestamp': ts, 'sha1': sha, 'message': message or ''}
        with open(dest, 'w', encoding='utf-8') as bf:
            bf.write('# MCP version backup\n')
            bf.write('# ' + json.dumps(meta) + '\n')
            bf.write(content)

        # atomically replace target
        tmp = TARGET_PATH.with_name(TARGET_PATH.name + '.mcp.tmp')
        with open(tmp, 'w', encoding='utf-8') as tf:
            tf.write(content)
        os.replace(tmp, TARGET_PATH)

    # record audit
    try:
        log_audit({'op': 'write', 'version': fname, 'meta': meta})
    except Exception:
        pass
    return {'version': fname, 'meta': meta}


def log_audit(entry: dict):
    entry = dict(entry)
    entry['ts'] = _now_ts()
    with open(AUDIT_LOG, 'a', encoding='utf-8') as af:
        af.write(json.dumps(entry, ensure_ascii=False) + '\n')


class JsonRpcError(Exception):
    def __init__(self, code: int, message: str, data: dict | str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


def _legacy_call(op: str, params: dict | None = None):
    return handle_request({**(params or {}), 'op': op})


def _legacy_call_data(op: str, params: dict | None = None):
    resp = _legacy_call(op, params)
    if not isinstance(resp, dict):
        raise JsonRpcError(-32001, 'Legacy handler returned invalid response')
    if not resp.get('ok'):
        raise JsonRpcError(-32001, resp.get('error') or 'operation failed')
    return resp.get('data')


def _format_tool_output(data):
    if data is None:
        return '(empty result)'
    if isinstance(data, str):
        return data
    return json.dumps(data, ensure_ascii=False, indent=2)


def _tool_robot_get_joint_positions(args: dict | None):
    ip = None
    if isinstance(args, dict):
        ip = args.get('ip')
    try:
        robot_control.controller.ensure_connected(ip=ip)
        joints = robot_control.controller.get_joint_positions()
        return {
            'ip': robot_control.controller.ip_address,
            'joints': joints,
        }
    except robot_control.RobotError as exc:
        raise JsonRpcError(-32010, str(exc))


def _build_tool_specs():
    return [
        {
            'name': 'diana.read_file',
            'aliases': ['read', 'read_file'],
            'description': '读取 `src/diana_api/diana_api.py` 的全部内容。',
            'schema': {'type': 'object', 'properties': {}, 'required': []},
            'op': 'read',
        },
        {
            'name': 'diana.read_range',
            'aliases': ['read_range'],
            'description': '按行号区间读取 `src/diana_api/diana_api.py`。',
            'schema': {
                'type': 'object',
                'properties': {
                    'start': {'type': 'integer', 'minimum': 1},
                    'end': {'type': 'integer', 'minimum': 1},
                },
                'required': ['start', 'end'],
            },
            'op': 'read_range',
        },
        {
            'name': 'diana.search',
            'aliases': ['search'],
            'description': '按关键字检索 `src/diana_api/diana_api.py`。',
            'schema': {
                'type': 'object',
                'properties': {'query': {'type': 'string'}},
                'required': ['query'],
            },
            'op': 'search',
        },
        {
            'name': 'diana.symbols',
            'aliases': ['symbols'],
            'description': '获取文件中的函数与类符号信息。',
            'schema': {'type': 'object', 'properties': {}, 'required': []},
            'op': 'symbols',
        },
        {
            'name': 'diana.stats',
            'aliases': ['stats'],
            'description': '统计文件的行数、大小与 SHA1。',
            'schema': {'type': 'object', 'properties': {}, 'required': []},
            'op': 'stats',
        },
        {
            'name': 'diana.list_versions',
            'aliases': ['list_versions'],
            'description': '列出历史版本备份。',
            'schema': {'type': 'object', 'properties': {}, 'required': []},
            'op': 'list_versions',
        },
        {
            'name': 'diana.get_version',
            'aliases': ['get_version'],
            'description': '读取历史版本文件内容。',
            'schema': {
                'type': 'object',
                'properties': {'name': {'type': 'string'}},
                'required': ['name'],
            },
            'op': 'get_version',
        },
        {
            'name': 'diana.write_file',
            'aliases': ['write', 'write_file'],
            'description': '写入 `src/diana_api/diana_api.py` 并生成版本备份。',
            'schema': {
                'type': 'object',
                'properties': {
                    'content': {'type': 'string'},
                    'message': {'type': 'string'},
                    'check_syntax': {'type': 'boolean'},
                },
                'required': ['content'],
            },
            'op': 'write',
        },
        {
            'name': 'robot.get_joint_positions',
            'description': '返回当前连接的机器人关节角度。未连接时可提供 ip 建立连接。',
            'schema': {
                'type': 'object',
                'properties': {
                    'ip': {'type': 'string', 'description': '首次连接时必填的机器人 IP 地址'},
                },
                'required': [],
            },
            'handler': _tool_robot_get_joint_positions,
        },
    ]


TOOL_SPECS = _build_tool_specs()
TOOL_REGISTRY = {spec['name']: spec for spec in TOOL_SPECS}
# map known aliases to canonical tool names
TOOL_ALIASES = {alias: spec['name'] for spec in TOOL_SPECS for alias in spec.get('aliases', [])}


def _resolve_tool_spec(name: str):
    if name in TOOL_REGISTRY:
        return TOOL_REGISTRY[name]
    canonical = TOOL_ALIASES.get(name)
    if canonical:
        return TOOL_REGISTRY.get(canonical)
    return None


def list_tool_descriptions():
    out = []
    for spec in TOOL_SPECS:
        out.append(
            {
                'name': spec['name'],
                'description': spec['description'],
                'inputSchema': spec['schema'],
            }
        )
    return out


def list_resource_descriptions():
    return REGISTERED_RESOURCES


def list_prompt_descriptions():
    return REGISTERED_PROMPTS


def call_tool(name: str, arguments: dict | None = None):
    spec = _resolve_tool_spec(name)
    if not spec:
        raise JsonRpcError(-32601, f'Unknown tool: {name}')
    if arguments is not None and not isinstance(arguments, dict):
        raise JsonRpcError(-32602, 'Tool arguments must be an object')
    handler = spec.get('handler')
    if handler:
        data = handler(arguments or {})
    else:
        data = _legacy_call_data(spec['op'], arguments)
    text = _format_tool_output(data)
    return {'content': [{'type': 'text', 'text': text}]}


def handle_request(req: dict) -> dict:
    try:
        op = req.get('op')
        if op == 'read':
            return {'ok': True, 'data': read_target()}
        if op == 'read_range':
            start = req.get('start')
            end = req.get('end')
            if start is None or end is None:
                return {'ok': False, 'error': 'start and end required'}
            try:
                data = read_target_range(int(start), int(end))
            except Exception as e:
                return {'ok': False, 'error': str(e)}
            return {'ok': True, 'data': data}
        if op == 'search':
            query = req.get('query', '')
            return {'ok': True, 'data': search_target(query)}
        if op == 'symbols':
            return {'ok': True, 'data': get_symbols()}
        if op == 'stats':
            return {'ok': True, 'data': stats_target()}
        if op == 'list_versions':
            return {'ok': True, 'data': list_versions()}
        if op == 'get_version':
            name = req.get('name')
            if not name:
                return {'ok': False, 'error': 'missing name'}
            return {'ok': True, 'data': get_version(name)}
        if op == 'write':
            content = req.get('content')
            if content is None:
                return {'ok': False, 'error': 'missing content'}
            message = req.get('message')
            check_syntax = req.get('check_syntax', True)
            try:
                res = write_target(content, message, check_syntax=bool(check_syntax))
            except SyntaxError as se:
                return {'ok': False, 'error': f'syntax error: {se}'}
            except Exception as e:
                return {'ok': False, 'error': str(e)}
            return {'ok': True, 'data': res}
        return {'ok': False, 'error': f'unknown op: {op}'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def stdin_loop():
    # read JSON lines from stdin, write JSON lines to stdout
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception as e:
            resp = {'ok': False, 'error': f'invalid json: {e}'}
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + '\n')
            sys.stdout.flush()
            continue
        # Legacy protocol compatibility
        if isinstance(req, dict) and 'op' in req:
            resp = handle_request(req)
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + '\n')
            sys.stdout.flush()
            continue

        resp = handle_jsonrpc_message(req)
        if resp is None:
            continue
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + '\n')
        sys.stdout.flush()
        if shutdown_event.is_set():
            break


def make_jsonrpc_result(msg_id, result):
    if msg_id is None:
        return None
    return {'jsonrpc': '2.0', 'id': msg_id, 'result': result}


def make_jsonrpc_error(msg_id, code, message, data=None):
    err = {'code': code, 'message': message}
    if data is not None:
        err['data'] = data
    return {'jsonrpc': '2.0', 'id': msg_id, 'error': err}


def handle_jsonrpc_message(msg):
    msg_id = msg.get('id') if isinstance(msg, dict) else None
    try:
        return process_jsonrpc_request(msg)
    except JsonRpcError as exc:
        return make_jsonrpc_error(msg_id, exc.code, exc.message, exc.data)
    except Exception as exc:  # pragma: no cover - safety net
        return make_jsonrpc_error(msg_id, -32603, str(exc))


def process_jsonrpc_request(msg):
    if not isinstance(msg, dict):
        raise JsonRpcError(-32600, 'Invalid request payload')

    jsonrpc = msg.get('jsonrpc')
    method = msg.get('method')
    msg_id = msg.get('id')
    params = msg.get('params', {})

    if jsonrpc != '2.0':
        raise JsonRpcError(-32600, 'Invalid JSON-RPC version')
    if method is None:
        raise JsonRpcError(-32600, 'Missing method')

    if method == 'initialize':
        if not isinstance(params, dict):
            raise JsonRpcError(-32602, 'Params must be an object for initialize')
        client_state['initialized'] = True
        client_state['clientInfo'] = params.get('clientInfo')
        client_state['capabilities'] = params.get('capabilities', {})
        result = {
            'protocolVersion': PROTOCOL_VERSION,
            'serverInfo': SERVER_INFO,
            'capabilities': SERVER_CAPABILITIES,
        }
        return make_jsonrpc_result(msg_id, result)

    if method == 'shutdown':
        shutdown_event.set()
        return make_jsonrpc_result(msg_id, {'ack': True})

    if method == 'ping':
        return make_jsonrpc_result(msg_id, {'ack': True})

    if method == 'tools/list':
        return make_jsonrpc_result(msg_id, {'tools': list_tool_descriptions()})

    if method == 'tools/call':
        if not isinstance(params, dict):
            raise JsonRpcError(-32602, 'Params must be an object for tools/call')
        tool_name = params.get('name')
        if not tool_name:
            raise JsonRpcError(-32602, 'Missing tool name')
        arguments = params.get('arguments') or {}
        result = call_tool(tool_name, arguments)
        return make_jsonrpc_result(msg_id, result)

    if method == 'resources/list':
        return make_jsonrpc_result(msg_id, {'resources': list_resource_descriptions()})

    if method == 'prompts/list':
        return make_jsonrpc_result(msg_id, {'prompts': list_prompt_descriptions()})

    # Support direct calls using tool names for convenience.
    spec = _resolve_tool_spec(method)
    if spec:
        if params is not None and not isinstance(params, dict):
            raise JsonRpcError(-32602, 'Tool parameters must be an object')
        result = call_tool(spec['name'], params or {})
        return make_jsonrpc_result(msg_id, result)

    # Notifications are silently ignored if we do not understand them.
    if msg_id is None:
        return None

    raise JsonRpcError(-32601, f'Unknown method: {method}')


def main():
    # Ensure target exists
    if not TARGET_PATH.is_file():
        # create an empty target to avoid crashes
        TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TARGET_PATH, 'w', encoding='utf-8') as f:
            f.write('# DianaApi placeholder created by mcp_server\n')

    # Start stdio loop
    try:
        stdin_loop()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
