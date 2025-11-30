#!/usr/bin/env python3
"""直接调用 MCP 工具获取机械臂位置"""

import sys
import json
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def call_get_joint_positions(ip=None):
    """调用 get_joint_positions 工具"""
    try:
        # 导入 MCP 服务器模块
        from server.mcp_server import get_joint_positions
        
        print("=" * 60)
        print("调用 MCP 工具: get_joint_positions")
        print("=" * 60)
        
        if ip:
            print(f"使用指定 IP: {ip}")
        else:
            print("使用默认 IP (从配置读取)")
        
        print("\n正在获取机械臂关节位置...")
        result = get_joint_positions(ip=ip)
        
        print("\n" + "=" * 60)
        print("✅ 获取成功！")
        print("=" * 60)
        print(f"\n机械臂 IP: {result.get('ip', 'N/A')}")
        print(f"关节数量: {result.get('joint_count', 0)}")
        print(f"\n关节位置 (弧度):")
        joints = result.get('joints', [])
        for i, joint in enumerate(joints, 1):
            print(f"  关节 {i}: {joint:.6f} rad ({joint * 180 / 3.14159265359:.4f}°)")
        
        print("\n" + "=" * 60)
        print("JSON 格式输出:")
        print("=" * 60)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return result
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ 获取失败")
        print("=" * 60)
        print(f"错误信息: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='调用 MCP 工具获取机械臂位置')
    parser.add_argument('--ip', type=str, help='机械臂 IP 地址（可选）')
    args = parser.parse_args()
    
    result = call_get_joint_positions(ip=args.ip)
    sys.exit(0 if result else 1)


