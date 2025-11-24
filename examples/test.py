import time
from bin import DianaApi
import math
import testArm

from ControlGripper import SetCmd
from ControlGripper import ReadStatus
from ControlRoot import ControlRoot

#连接机器人
netInfo=('192.168.10.75', 0, 0, 0, 0, 0)
DianaApi.initSrv(netInfo)

ipAddress = '192.168.10.75'

# #get robot current pose
poses = [0.0] * 6
joints = [0.0] * 7
DianaApi.getTcpPos(poses, ipAddress)
print(f'Arm Pose:{poses}')
DianaApi.getJointPos(joints, ipAddress)
print(f'Arm Joints:{joints}')
vel = 0.2
acc = 0.2

# # dan_wei:m
x = 0.44596987714819386
y = 0.4380707749872163
z = 0.25774713695461066
# angel
row = 0
pitch = 0
yaw =  0
# hu_du
Rx = row*(3.14/180)
Ry = pitch*(3.14/180)
Rz = yaw*(3.14/180)

CR = ControlRoot()
cs = SetCmd(CR)
re = ReadStatus(CR)
cs.HandInit()
cs.Force(20)
time.sleep(0.1)

cs.Velocity(500)
time.sleep(0.1)

cs.Position(1000)
time.sleep(2)

# poses = [0.5616596670908373, 0.3771046268671877, 0.21291467307440456, Rx, Ry, Rz]
# DianaApi.moveJToPose(poses, vel, acc, 0, 0, 0, ipAddress)

# testArm.arm_pose_init(vel,acc,ipAddress)
DianaApi.wait_move()

# #初始化夹爪

# #设置夹爪
cs.Position(200)
time.sleep(2)
print('夹爪闭合')
cs.Position(1000)
time.sleep(2)
print('夹爪打开')

# INtialpose = [0.41187,0.42784,0.46556, Rx, Ry, Rz]
# DianaApi.moveJToPose(INtialpose, vel, acc, 0, 0, 0, ipAddress)
# DianaApi.wait_move()

DianaApi.stop(ipAddress)
DianaApi.destroySrv(ipAddress)

# #打开抱闸
DianaApi.releaseBrake()
time.sleep(1)

# #关闭抱闸
# DianaApi.holdBrake()
# time.sleep(1)