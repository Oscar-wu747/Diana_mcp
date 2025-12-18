"""Diana API Python绑定。

该包封装 `diana_api.py` 中的底层 ctypes 封装，方便后续进一步模块化。

为了在没有底层 C 库（`libDianaApi.so`）的开发/测试环境中也能导入
此包，本文件在无法加载真实绑定时会提供一个最小的替代模块（stub），
以便上层 `control` 模块可以被测试或被 monkeypatch。真正运行时应优先使用
真实的 `diana_api.py`。
"""

try:
	from .diana_api import *  # noqa: F401,F403
except Exception:
	# 构造最小 stub 模块，包含 control.py 可能会调用或被 monkeypatch 的符号
	import sys
	import types

	_stub = types.ModuleType('diana_api.diana_api')

	def _stub_true(*args, **kwargs):
		return True

	def _stub_get_robot_state(ipAddress=''):
		# default to non-zero (idle/finished) state
		return 1

	# 列出 control.py 里常用的函数（足以在单元测试里被 monkeypatch）
	for _name in (
		'initSrv', 'destroySrv', 'moveJToTarget', 'moveLToPose', 'moveJoint',
		'getJointPos', 'getTcpPos', 'stop', 'resume',
	):
		setattr(_stub, _name, _stub_true)
	_stub.getRobotState = _stub_get_robot_state

	sys.modules['diana_api.diana_api'] = _stub

from . import control  # noqa: F401

