import asyncio
from fastmcp import Client

# 机器人 IP 地址
ROBOT_IP = "192.168.10.75"  # 请替换为您实际的机器人 IP 地址

async def main():
    async with Client("server.mcp_server") as client:
        print("已连接到 Diana MCP 服务器")

        # 列出可用工具
        tools = await client.list_tools()
        print(f"可用工具: {', '.join([tool.name for tool in tools])}")

        # 连接到机器人
        print(f"\n正在连接到机器人 {ROBOT_IP}...")
        connect_result = await client.call_tool("connect_robot", {"ip": ROBOT_IP})
        print(f"连接结果: {connect_result.text}")

        # 如果连接成功，继续执行其他操作
        if "success\": true" in connect_result.text:
            # 获取关节位置
            print("\n获取关节位置...")
            joint_pos = await client.call_tool("get_joint_positions", {})
            print(f"关节位置: {joint_pos.text}")

            # 获取 TCP 位置
            print("\n获取 TCP 位置...")
            tcp_pos = await client.call_tool("get_tcp_pose", {})
            print(f"TCP 位置: {tcp_pos.text}")

            # 获取机器人状态
            print("\n获取机器人状态...")
            robot_state = await client.call_tool("get_robot_state", {})
            print(f"机器人状态: {robot_state.text}")

            # 启用自由驱动模式
            print("\n启用普通自由驱动模式...")
            freedrive_result = await client.call_tool("enable_free_driving", {"mode": 1})
            print(f"自由驱动结果: {freedrive_result.text}")

            # 等待 5 秒让用户手动移动机器人
            print("请在 5 秒内手动移动机器人...")
            await asyncio.sleep(5)

            # 禁用自由驱动模式
            print("\n禁用自由驱动模式...")
            disable_result = await client.call_tool("enable_free_driving", {"mode": 0})
            print(f"禁用自由驱动结果: {disable_result.text}")

            # 示例：移动关节
            print("\n移动关节到零位...")
            zero_position = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            move_result = await client.call_tool("move_joint_positions", {
                "joints": zero_position,
                "velocity": 0.2,
                "acceleration": 0.1
            })
            print(f"移动结果: {move_result.text}")

            # 等待机器人完成移动
            print("等待机器人完成移动...")
            await asyncio.sleep(5)

            # 断开与机器人的连接
            print("\n断开与机器人的连接...")
            disconnect_result = await client.call_tool("disconnect_robot", {})
            print(f"断开连接结果: {disconnect_result.text}")

        print("\n示例完成!")

if __name__ == "__main__":
    asyncio.run(main())
