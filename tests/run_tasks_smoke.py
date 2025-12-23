#!/usr/bin/env python3
from diana_api.control import controller, RobotError
import time

print('Running task lifecycle smoke tests')

# Test 1: move and wait complete
controller._connected = True
controller._ip_address = '127.0.0.1'

# patch moveJToTarget
controller_api = __import__('diana_api.control', fromlist=['api']).api
controller_api.moveJToTarget = lambda *args, **kwargs: True

states = iter([0, 0, 1])
def fake_get_robot_state():
    return next(states, 1)
controller.get_robot_state = fake_get_robot_state

res = controller.move_joint_positions([0.0]*7, 0.1, 0.1)
print('move returned:', res)
task_id = res['task_id']
print('waiting for task to complete...')
final = controller.wait_task(task_id, timeout=2)
print('final task state:', final)
assert final['status'] == 'completed'
print('Test 1 passed')

# Test 2: cancel task
controller._connected = True
controller._ip_address = '127.0.0.1'
controller_api.moveJToTarget = lambda *args, **kwargs: True
controller.get_robot_state = lambda: 0
res = controller.move_joint_positions([0.0]*7, 0.1, 0.1)
print('move returned:', res)
task_id = res['task_id']
print('cancelling task...')
canceled = controller.cancel_task(task_id)
print('canceled:', canceled)
assert canceled['status'] == 'aborted'
print('Test 2 passed')

# Test 3: wait timeout
controller._connected = True
controller._ip_address = '127.0.0.1'
controller_api.moveJToTarget = lambda *args, **kwargs: True
controller.get_robot_state = lambda: 0
res = controller.move_joint_positions([0.0]*7, 0.1, 0.1)
print('move returned:', res)
task_id = res['task_id']
print('waiting with short timeout...')
try:
    controller.wait_task(task_id, timeout=0.2)
    print('ERROR: expected timeout but wait_task returned')
    raise SystemExit(2)
except RobotError:
    print('timeout correctly raised RobotError')
    print('Test 3 passed')

print('ALL SMOKE TESTS PASSED')
