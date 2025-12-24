import time

import pytest

from diana_api.control import RobotError, controller


def test_move_and_wait_complete(monkeypatch):
    # Prepare controller as connected
    controller._connected = True
    controller._ip_address = "127.0.0.1"

    # Patch moveJToTarget to succeed
    monkeypatch.setattr("diana_api.control.api.moveJToTarget", lambda *args, **kwargs: True)

    # Simulate robot state: running (0) a few times then finished (1)
    states = iter([0, 0, 1])

    def fake_get_robot_state():
        return next(states, 1)

    monkeypatch.setattr(controller, "get_robot_state", fake_get_robot_state)

    res = controller.move_joint_positions([0.0] * 7, 0.1, 0.1)
    assert "task_id" in res
    task_id = res["task_id"]

    # wait for completion
    final = controller.wait_task(task_id, timeout=2)
    assert final["status"] == "completed"


def test_cancel_task(monkeypatch):
    controller._connected = True
    controller._ip_address = "127.0.0.1"
    monkeypatch.setattr("diana_api.control.api.moveJToTarget", lambda *args, **kwargs: True)

    # robot keeps running (0)
    def always_running():
        return 0

    monkeypatch.setattr(controller, "get_robot_state", always_running)

    res = controller.move_joint_positions([0.0] * 7, 0.1, 0.1)
    task_id = res["task_id"]

    # cancel the task
    canceled = controller.cancel_task(task_id)
    assert canceled["status"] == "aborted"


def test_wait_timeout(monkeypatch):
    controller._connected = True
    controller._ip_address = "127.0.0.1"
    monkeypatch.setattr("diana_api.control.api.moveJToTarget", lambda *args, **kwargs: True)

    # robot keeps running
    def always_running():
        return 0

    monkeypatch.setattr(controller, "get_robot_state", always_running)

    res = controller.move_joint_positions([0.0] * 7, 0.1, 0.1)
    task_id = res["task_id"]

    with pytest.raises(RobotError):
        controller.wait_task(task_id, timeout=0.2)
