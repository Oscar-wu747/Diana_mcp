"""机器人控制模块加载器"""

import sys
import importlib.util
import types
from .utils import SuppressRobotOutput
from .config import SRC_DIR
from .error_handler import log_exception


def _load_robot_control():
    """加载机械臂控制模块，失败时返回备用存根"""
    init_file = SRC_DIR / 'diana_api' / '__init__.py'
    spec = importlib.util.spec_from_file_location('diana_api', init_file)
    if spec is None or spec.loader is None:
        raise RuntimeError('无法定位diana_api包')
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault('diana_api', module)
    try:
        # 加载时抑制输出
        with SuppressRobotOutput():
            spec.loader.exec_module(module)
        return module.control
    except Exception as exc:
        log_exception(exc, prefix='加载diana_api控制模块失败: ')

        class RobotError(RuntimeError):
            pass

        class _StubController:
            def __init__(self):
                self._ip = None
                self._connected = False

            @property
            def ip_address(self):
                return self._ip

            @property
            def is_connected(self):
                return self._connected

            def connect(self, net_info, *, error_cb=None, state_cb=None):
                raise RobotError('机械臂库不可用')

            def disconnect(self):
                if not self._connected:
                    return {'status': 'already_disconnected'}
                self._connected = False
                self._ip = None
                return {'status': 'disconnected'}

            def ensure_connected(self, *, ip=None, net_info=None):
                raise RobotError('机械臂库不可用')

            def get_joint_positions(self):
                raise RobotError('机械臂库不可用')

        ctrl_mod = types.SimpleNamespace(RobotError=RobotError, controller=_StubController())
        return ctrl_mod


# 加载机械臂控制模块
robot_control = _load_robot_control()