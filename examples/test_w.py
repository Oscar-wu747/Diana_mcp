import time
from bin import DianaApi
import math

# --- 调试工具 ---
def debug_log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

#连接机器人
netInfo=('192.168.10.75', 0, 0, 0, 0, 0)
DianaApi.initSrv(netInfo)

ipAddress = '192.168.10.75'

# 回原点测试配置
HOME_JOINTS = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # 原点关节角度（弧度）
POSITION_TOLERANCE = 0.01  # 位置误差阈值（弧度）
MOVE_VELOCITY = 0.3  # 运动速度（弧度/秒）
MOVE_ACCELERATION = 0.2  # 运动加速度（弧度/秒²）

debug_log("--- 回原点测试程序启动 ---")

# --- 步骤 1: 连接机器人 ---
try:
    debug_log(f"正在连接机器人: {netInfo}...")
    # 初始化服务，建立连接
    if not DianaApi.initSrv(netInfo):
        # 如果连接失败，直接退出程序
        debug_log("状态: 连接失败！")
        debug_log("结果: 无法与机器人建立连接，请检查网络配置和机器人状态。")
        exit() # 退出程序
    debug_log("状态: 机器人连接成功！")

    # --- 步骤 2: 发送回原点运动指令 ---
    debug_log(f"发送指令：移动到原点位置 {HOME_JOINTS}")
    move_result = DianaApi.moveJToTarget(HOME_JOINTS, MOVE_VELOCITY, MOVE_ACCELERATION, ipAddress=netInfo)

    if not move_result:
        debug_log("状态: 运动指令发送失败")
        debug_log("结果: 回原点指令发送失败！")
    else:
        debug_log("状态: 运动指令已发送")
        debug_log("结果: 等待机械臂运动完成...")

        # --- 步骤 3: 等待运动完成 ---
        DianaApi.wait_move(ipAddress=netInfo)
        debug_log("机械臂运动已完成。")

        # --- 步骤 4: 检测是否到达目标位置 ---
        max_checks = 10
        check_interval = 0.5
        is_at_home = False
        current_joints = [0.0] * 7  # 初始化关节位置列表

        for i in range(max_checks):
            # 获取当前关节位置
            DianaApi.getJointPos(current_joints, ipAddress=netInfo)
            debug_log(f"位置检测 ({i+1}/{max_checks}): {[round(j, 4) for j in current_joints]}")

            # 检查所有关节误差
            angle_diffs = [math.fabs(c - t) for c, t in zip(current_joints, HOME_JOINTS)]
            if all(diff < POSITION_TOLERANCE for diff in angle_diffs):
                is_at_home = True
                break

            time.sleep(check_interval)

        # --- 步骤 5: 输出最终测试结果 ---
        debug_log(f"\n--- 测试结果汇总 ---")
        debug_log(f"测试结果: {'成功' if is_at_home else '失败'}")
        if is_at_home:
            debug_log(f"详情: 机械臂已成功到达原点位置，所有关节误差均在 {POSITION_TOLERANCE} 弧度内。")
        else:
            debug_log(f"详情: 机械臂未在规定时间内到达原点位置。")
            debug_log(f"目标位置: {HOME_JOINTS}")
            debug_log(f"最终位置: {[round(j, 4) for j in current_joints]}")

except Exception as e:
    debug_log(f"\n--- 程序异常 ---")
    debug_log(f"状态: 异常")
    debug_log(f"结果: 执行过程中发生严重错误: {e}")

finally:
    # --- 步骤 6: 断开与机器人的连接 ---
    # finally 块中的代码无论成功与否都会执行，确保资源被释放
    debug_log("\n正在断开与机器人的连接...")
    DianaApi.destroySrv()
    debug_log("机器人连接已断开。")

debug_log("--- 回原点测试程序结束 ---")
