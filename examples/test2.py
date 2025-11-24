import time
from bin import DianaApi
import math
import testArm

# 调试工具：打印带时间戳的消息
def debug_log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

# 连接机器人
try:
    netInfo = ('192.168.10.75', 0, 0, 0, 0, 0)
    DianaApi.initSrv(netInfo)
    debug_log("网络连接成功")
except Exception as e:
    debug_log(f"连接失败: {str(e)}")
    exit()

ipAddress = '192.168.10.75'

# 添加网络状态检查
link_state = DianaApi.getLinkState(ipAddress)
debug_log(f"网络链路状态: {'正常' if link_state else '断开'}")

# 获取并打印初始状态
try:
    #获取当前抱闸状态
    brake_state = DianaApi.getBrakeState(ipAddress)  
    debug_log(f"抱闸初始状态: {'释放' if brake_state else '抱紧'}")
    
    # 初始关节力矩检测
    joints_torque = [0.0] * 7
    DianaApi.getJointTorque(joints_torque, ipAddress)
    debug_log(f"初始关节力矩: {joints_torque}")
    # 初始关节速度检测
    joint_vel = [0.0] * 7
    DianaApi.getJointAngularVel(joint_vel, ipAddress)
    debug_log(f"初始关节速度: {joint_vel}")
except Exception as e:
    debug_log(f"状态获取异常: {str(e)}")

# 打开抱闸 
debug_log("尝试释放抱闸...")
DianaApi.releaseBrake(ipAddress)
time.sleep(1)  # 确保抱闸完全释放

# 验证抱闸释放（假设有反馈）
# if DianaApi.getBrakeState(ipAddress):
#     debug_log("抱闸释放成功")
# else:
#     debug_log("抱闸释放失败!!!")

# 运动前状态检查
error_code = DianaApi.getLastError(ipAddress)
debug_log(f"运动前错误代码: {error_code} ({DianaApi.errorCodeMessage.get(error_code, '未知错误')})")

# 定义目标位姿
x, y, z = 0.5755, 0.42893, 0.55184
row, pitch, yaw = -1.280, 1.982, 40.282
Rx, Ry, Rz = [angle * (math.pi/180) for angle in [row, pitch, yaw]]
target_pose = [x, y, z, Rx, Ry, Rz]

x, y, z = 0.363121, 0.357399, 0.502707
row, pitch, yaw = -0.158, -3.552, 42.120
Rx, Ry, Rz = [angle * (math.pi/180) for angle in [row, pitch, yaw]]
target_init = [x, y, z, Rx, Ry, Rz]

x, y, z = 0.3644661, 0.370191, 0.231344
row, pitch, yaw = -0.348, 0.195, 43.379
Rx, Ry, Rz = [angle * (math.pi/180) for angle in [row, pitch, yaw]]
target_end = [x, y, z, Rx, Ry, Rz]

# 执行运动
debug_log("开始运动指令...")
try:
    v = 0.2  # 速度参数名对应API中的v
    a = 0.2  # 加速度参数名对应API中的a
    DianaApi.moveJToPose(target_init, v, a, 0, 0, 0, ipAddress)
    DianaApi.wait_move()
    debug_log("运动指令已发送")
    
    # 实时监控运动状态
    while True:
        state = DianaApi.getRobotState(ipAddress)
        torque = [0.0]*7
        DianaApi.getJointTorque(torque, ipAddress)
        joint_vel = [0.0] * 7
        DianaApi.getJointAngularVel(joint_vel, ipAddress)
        debug_log(f"运动状态: {state} | 实时力矩: {[round(t,2) for t in torque]}")
        debug_log(f"实时关节速度: {joint_vel}")
        if state != 0:  # 非运动中状态
            break
        time.sleep(0.5)
        
except Exception as e:
    debug_log(f"运动执行异常: {str(e)}")

# 运动后诊断
debug_log("===== 运动后诊断 =====")
collision = DianaApi.isCollision(ipAddress)
debug_log(f"碰撞检测: {'有碰撞!' if collision else '无碰撞'}")

final_error = DianaApi.getLastError(ipAddress)
debug_log(f"最终错误代码: {final_error} ({DianaApi.errorCodeMessage.get(final_error, '未知错误')})")

# 关闭连接前保持抱闸释放
debug_log("保持抱闸释放状态2秒...")
time.sleep(2)

DianaApi.stop(ipAddress)
DianaApi.destroySrv(ipAddress)
debug_log("连接已关闭")