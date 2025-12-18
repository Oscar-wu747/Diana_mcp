from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, Optional, List, Dict, Any
import threading

from . import diana_api as api


class RobotError(RuntimeError):
    """Raised when low-level robot operations fail."""


def _tuple_net_info(net_info: Sequence) -> tuple:
    values = list(net_info)
    if len(values) != 6:
        raise RobotError('net_info must contain 6 elements: ip + 5 ports')
    return tuple(values)


def _default_net_info(ip: str) -> tuple:
    return (ip, 0, 0, 0, 0, 0)


@dataclass
class RobotController:
    """Thread-safe helper around the DianaApi ctypes bindings."""

    _lock: threading.RLock = field(default_factory=threading.RLock, init=False)
    _connected: bool = False
    _ip_address: Optional[str] = None
    _net_info: Optional[tuple] = None
    _task_counter: int = 0

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def ip_address(self) -> Optional[str]:
        return self._ip_address

    def connect(self, net_info: Sequence, *, error_cb=None, state_cb=None) -> Dict[str, Any]:
        info = _tuple_net_info(net_info)
        with self._lock:
            if self._connected:
                if info[0] != self._ip_address:
                    raise RobotError(f'Already connected to {self._ip_address}, disconnect first.')
                return {'status': 'already_connected', 'ip': self._ip_address}
            result = api.initSrv(info, error_cb, state_cb)
            if not result:
                raise RobotError('initSrv failed, please verify network and controller state.')
            self._connected = True
            self._ip_address = info[0]
            self._net_info = info
            return {'status': 'connected', 'ip': self._ip_address}

    def ensure_connected(self, *, ip: Optional[str] = None, net_info: Optional[Sequence] = None):
        if self._connected:
            if ip and ip != self._ip_address:
                raise RobotError(f'Controller already connected to {self._ip_address}, requested {ip}.')
            return
        if net_info is None:
            if not ip:
                raise RobotError('Robot is not connected; provide ip or net_info to connect.')
            net_info = _default_net_info(ip)
        self.connect(net_info)

    def disconnect(self):
        with self._lock:
            if not self._connected:
                return {'status': 'already_disconnected'}
            api.destroySrv(self._ip_address or '')
            self._connected = False
            self._ip_address = None
            self._net_info = None
            self._task_counter = 0
            return {'status': 'disconnected'}

    def stop_motion(self):
        self._require_connection()
        if not api.stop(self._ip_address or ''):
            raise RobotError('stop command failed.')
        return {'status': 'stopped'}

    def resume_motion(self):
        self._require_connection()
        if not api.resume(self._ip_address or ''):
            raise RobotError('resume command failed.')
        return {'status': 'resumed'}

    def enable_free_driving(self, mode: int):
        self._require_connection()
        if not api.freeDriving(mode, self._ip_address or ''):
            raise RobotError('freeDriving command failed.')
        return {'status': 'free_driving_enabled', 'mode': mode}

    def move_tcp_direction(self, direction: int, velocity: float, acceleration: float):
        self._require_connection()
        task_id = self._next_task_id()
        if not api.moveTCP(direction, velocity, acceleration, self._ip_address or ''):
            raise RobotError('moveTCP failed.')
        return {'status': 'queued', 'taskId': task_id}

    def rotate_tcp_direction(self, direction: int, velocity: float, acceleration: float):
        self._require_connection()
        task_id = self._next_task_id()
        if not api.rotationTCP(direction, velocity, acceleration, self._ip_address or ''):
            raise RobotError('rotationTCP failed.')
        return {'status': 'queued', 'taskId': task_id}

    def move_joint_positions(
        self,
        joints: Sequence[float],
        velocity: float,
        acceleration: float,
        *,
        zv_shaper_order: int = 0,
        zv_shaper_frequency: float = 0.0,
        zv_shaper_damping_ratio: float = 0.0,
    ):
        self._require_connection()
        if len(joints) != 7:
            raise RobotError('move_joint_positions expects 7 joint values.')
        task_id = self._next_task_id()
        if not api.moveJToTarget(
            list(joints),
            velocity,
            acceleration,
            zv_shaper_order,
            zv_shaper_frequency,
            zv_shaper_damping_ratio,
            self._ip_address or '',
        ):
            raise RobotError('moveJToTarget failed.')
        return {'status': 'moving', 'taskId': task_id, 'mode': 'joint'}

    def move_linear_pose(
        self,
        pose: Sequence[float],
        velocity: float,
        acceleration: float,
        *,
        zv_shaper_order: int = 0,
        zv_shaper_frequency: float = 0.0,
        zv_shaper_damping_ratio: float = 0.0,
    ):
        self._require_connection()
        if len(pose) != 6:
            raise RobotError('move_linear_pose expects 6 pose values.')
        task_id = self._next_task_id()
        if not api.moveLToPose(
            list(pose),
            velocity,
            acceleration,
            zv_shaper_order,
            zv_shaper_frequency,
            zv_shaper_damping_ratio,
            self._ip_address or '',
        ):
            raise RobotError('moveLToPose failed.')
        return {'status': 'moving', 'taskId': task_id, 'mode': 'linear'}

    def execute_joint_sequence(
        self,
        path: Sequence[Sequence[float]],
        velocity: float,
        acceleration: float,
    ):
        self._require_connection()
        if not path:
            raise RobotError('Path is empty.')
        task_id = self._next_task_id()
        for idx, joints in enumerate(path):
            if len(joints) != 7:
                raise RobotError(f'Path point #{idx} must contain 7 joints.')
            if not api.moveJToTarget(list(joints), velocity, acceleration, 0, 0.0, 0.0, self._ip_address or ''):
                raise RobotError(f'moveJToTarget failed at waypoint #{idx}.')
        return {'status': 'queued', 'taskId': task_id, 'points': len(path)}

    def get_joint_positions(self) -> List[float]:
        self._require_connection()
        joints = [0.0] * 7
        if not api.getJointPos(joints, ipAddress=self._ip_address or ''):
            raise RobotError('getJointPos failed.')
        return joints

    def get_tcp_pose(self) -> List[float]:
        self._require_connection()
        pose = [0.0] * 6
        if not api.getTcpPos(pose, ipAddress=self._ip_address or ''):
            raise RobotError('getTcpPos failed.')
        return pose

    def get_robot_state(self) -> Dict[str, Any]:
        self._require_connection()
        state = api.getRobotState(self._ip_address or '')
        if state is None:
            raise RobotError('getRobotState failed.')
        return state

    def status(self) -> Dict[str, Any]:
        if not self._connected:
            return {'connected': False}
        try:
            state = self.get_robot_state()
            return {
                'connected': True,
                'ip': self._ip_address,
                'taskCounter': self._task_counter,
                'robotState': state
            }
        except RobotError:
            return {
                'connected': True,
                'ip': self._ip_address,
                'taskCounter': self._task_counter,
                'robotState': None
            }

    def _require_connection(self):
        if not self._connected:
            raise RobotError('Robot is not connected.')

    def _next_task_id(self) -> int:
        with self._lock:
            self._task_counter += 1
            return self._task_counter


controller = RobotController()

__all__ = ['RobotController', 'RobotError', 'controller']

