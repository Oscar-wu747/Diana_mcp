import time
from bin import DianaApi
import math

# --- 调试工具 ---
def debug_log(msg):
    """打印带时间戳的调试消息"""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

# --- 核心配置 ---
# 机器人网络信息
ROBOT_IP = '192.168.10.75'
netInfo = (ROBOT_IP, 0, 0, 0, 0, 0)

# 位置检测配置
CHECK_TIMES = 1  # 总共检测的次数
CHECK_INTERVAL = 1.0  # 每次检测的间隔时间（秒）

debug_log("--- 位置检测程序启动---")

# --- 步骤 1: 连接机器人 ---
try:
    debug_log(f"正在连接机器人: {ROBOT_IP}...")
    if not DianaApi.initSrv(netInfo):
        debug_log("状态: 连接失败！")
        debug_log("结果: 无法与机器人建立连接，请检查网络配置和机器人状态。")
        exit()
    debug_log("状态: 机器人连接成功！")

    # --- 步骤 2: 循环检测并输出位置信息 ---
    debug_log(f"\n开始进行 {CHECK_TIMES} 次位置检测，间隔 {CHECK_INTERVAL} 秒...")
    for i in range(CHECK_TIMES):
        current_joints = [0.0] * 7  # 初始化关节位置列表
        DianaApi.getJointPos(current_joints, ipAddress=ROBOT_IP)

        current_tcp = [0.0] * 6  # 初始化TCP位置列表
        DianaApi.getTcpPos(current_tcp, ipAddress=ROBOT_IP)

        debug_log(f"\n=== 第 {i+1}/{CHECK_TIMES} 次检测 ===")
        debug_log(f"当前关节位置（弧度）: {[round(j, 4) for j in current_joints]}")
        debug_log(f"当前TCP位置（米/弧度）: {[round(p, 4) for p in current_tcp]}")

        if i < CHECK_TIMES - 1:
            debug_log(f"等待 {CHECK_INTERVAL} 秒后进行下一次检测...")
            time.sleep(CHECK_INTERVAL)

    debug_log("\n--- 位置检测完成 ---")

except Exception as e:
    debug_log(f"\n--- 程序异常 ---")
    debug_log(f"状态: 异常")
    debug_log(f"结果: 执行过程中发生严重错误: {e}")

finally:
    # --- 步骤 3: 断开与机器人的连接 ---
    debug_log("\n正在断开与机器人的连接...")
    DianaApi.destroySrv()
    debug_log("机器人连接已断开。")

debug_log("--- 位置检测程序结束 ---")
