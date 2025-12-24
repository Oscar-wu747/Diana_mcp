"""参数校验模块

提供严格的参数类型和范围校验，确保输入参数的安全性和有效性。
"""

from typing import List, Optional, Tuple, Union

# 延迟导入，避免循环依赖
try:
    from .robot_loader import robot_control
    from .utils import _parse_array_param
except ImportError:
    robot_control = None
    _parse_array_param = None


# 默认的安全范围（如果无法从机器人获取实际限位，使用这些保守值）
# 这些值基于典型的7自由度机械臂
DEFAULT_JOINT_LIMITS = [
    (-3.14, 3.14),  # 关节1: ±180度
    (-2.09, 2.09),  # 关节2: ±120度
    (-3.14, 3.14),  # 关节3: ±180度
    (-3.14, 3.14),  # 关节4: ±180度
    (-2.09, 2.09),  # 关节5: ±120度
    (-3.14, 3.14),  # 关节6: ±180度
    (-3.14, 3.14),  # 关节7: ±180度
]

# 速度和加速度的默认范围
DEFAULT_VELOCITY_MIN = 0.0
DEFAULT_VELOCITY_MAX = 1.0
DEFAULT_ACCELERATION_MIN = 0.0
DEFAULT_ACCELERATION_MAX = 1.0

# TCP 方向的取值范围（通常 0-5 或 -1 到某个值）
TCP_DIRECTION_MIN = -1
TCP_DIRECTION_MAX = 5


def _get_joint_limits() -> List[Tuple[float, float]]:
    """获取关节限位（从机器人或使用默认值）"""
    try:
        if robot_control and robot_control.controller.is_connected:
            # 尝试从机器人获取实际限位
            from .utils import SuppressRobotOutput

            with SuppressRobotOutput():
                # 这里可以调用 getJointsPositionRange，但需要先实现
                # 暂时使用默认值
                pass
    except Exception:
        pass

    return DEFAULT_JOINT_LIMITS


def _validate_numeric(
    value: Union[int, float],
    name: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
) -> float:
    """验证数值类型和范围

    Args:
        value: 要验证的值
        name: 参数名称（用于错误信息）
        min_val: 最小值（可选）
        max_val: 最大值（可选）

    Returns:
        转换为 float 的值

    Raises:
        ValueError: 如果类型或范围无效
    """
    # 检查类型
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} 必须是数字类型，当前类型: {type(value).__name__}")

    # 转换为 float
    float_value = float(value)

    # 检查是否为 NaN 或 Inf
    if not (float("-inf") < float_value < float("inf")):
        raise ValueError(f"{name} 必须是有限数值，当前值: {float_value}")

    # 检查范围
    if min_val is not None and float_value < min_val:
        raise ValueError(f"{name} 必须 >= {min_val}，当前值: {float_value}")

    if max_val is not None and float_value > max_val:
        raise ValueError(f"{name} 必须 <= {max_val}，当前值: {float_value}")

    return float_value


def validate_joints(joints: Optional[Union[List, str]], param_name: str = "joints") -> List[float]:
    """验证关节位置参数

    Args:
        joints: 关节角度数组（弧度），可以是 list 或 JSON 字符串
        param_name: 参数名称（用于错误信息）

    Returns:
        验证后的关节数组（float 列表）

    Raises:
        ValueError: 如果参数无效
    """
    # 检查是否为 None
    if joints is None:
        raise ValueError(f"{param_name} 不能为 None")

    # 如果是字符串，尝试解析为 JSON
    if isinstance(joints, str):
        if _parse_array_param is None:
            raise ValueError(f"{param_name} JSON 解析功能不可用")
        try:
            joints = _parse_array_param(joints, param_name)
        except ValueError as e:
            raise ValueError(f"{param_name} JSON 格式错误: {str(e)}")

    # 检查是否为列表
    if not isinstance(joints, list):
        raise ValueError(
            f"{param_name} 必须是列表类型或 JSON 字符串，当前类型: {type(joints).__name__}"
        )

    # 检查是否为空
    if not joints:
        raise ValueError(f"{param_name} 不能为空")

    # 检查长度
    if len(joints) != 7:
        raise ValueError(f"{param_name} 必须包含 7 个关节值，当前数量: {len(joints)}")

    # 验证每个关节值
    validated_joints = []
    joint_limits = _get_joint_limits()

    for i, joint in enumerate(joints):
        # 验证类型和范围
        try:
            joint_value = _validate_numeric(
                joint, f"{param_name}[{i}]", min_val=joint_limits[i][0], max_val=joint_limits[i][1]
            )
            validated_joints.append(joint_value)
        except ValueError as e:
            raise ValueError(f"关节 {i+1} 验证失败: {str(e)}")

    return validated_joints


def validate_pose(pose: Optional[List], param_name: str = "pose") -> List[float]:
    """验证 TCP 姿态参数

    Args:
        pose: TCP 姿态数组 [x, y, z, rx, ry, rz]
        param_name: 参数名称（用于错误信息）

    Returns:
        验证后的姿态数组（float 列表）

    Raises:
        ValueError: 如果参数无效
    """
    # 检查是否为 None 或空
    if not pose:
        raise ValueError(f"{param_name} 不能为空")

    # 检查是否为列表
    if not isinstance(pose, list):
        raise ValueError(f"{param_name} 必须是列表类型，当前类型: {type(pose).__name__}")

    # 检查长度
    if len(pose) != 6:
        raise ValueError(
            f"{param_name} 必须包含 6 个值 [x, y, z, rx, ry, rz]，当前数量: {len(pose)}"
        )

    # 验证每个值
    validated_pose = []
    for i, value in enumerate(pose):
        # 位置值 (x, y, z) 通常没有严格限制，但应该是有限数值
        # 角度值 (rx, ry, rz) 通常在 ±π 范围内
        try:
            if i < 3:
                # 位置值：只检查是否为有限数值
                pose_value = _validate_numeric(value, f"{param_name}[{i}]")
            else:
                # 角度值：检查是否在合理范围内（±π）
                pose_value = _validate_numeric(
                    value,
                    f"{param_name}[{i}]",
                    min_val=-3.15,  # 略大于 -π
                    max_val=3.15,  # 略大于 π
                )
            validated_pose.append(pose_value)
        except ValueError as e:
            raise ValueError(
                f"姿态值 {i+1} ({'xyz'[i] if i < 3 else 'rxryrz'[i-3]}) 验证失败: {str(e)}"
            )

    return validated_pose


def validate_velocity(velocity: Union[int, float], param_name: str = "velocity") -> float:
    """验证速度参数

    Args:
        velocity: 速度值
        param_name: 参数名称（用于错误信息）

    Returns:
        验证后的速度值（float）

    Raises:
        ValueError: 如果参数无效
    """
    return _validate_numeric(
        velocity, param_name, min_val=DEFAULT_VELOCITY_MIN, max_val=DEFAULT_VELOCITY_MAX
    )


def validate_acceleration(
    acceleration: Union[int, float], param_name: str = "acceleration"
) -> float:
    """验证加速度参数

    Args:
        acceleration: 加速度值
        param_name: 参数名称（用于错误信息）

    Returns:
        验证后的加速度值（float）

    Raises:
        ValueError: 如果参数无效
    """
    return _validate_numeric(
        acceleration, param_name, min_val=DEFAULT_ACCELERATION_MIN, max_val=DEFAULT_ACCELERATION_MAX
    )


def validate_tcp_direction(direction: int, param_name: str = "direction") -> int:
    """验证 TCP 方向参数

    Args:
        direction: 方向值（通常是 0-5 或 -1）
        param_name: 参数名称（用于错误信息）

    Returns:
        验证后的方向值（int）

    Raises:
        ValueError: 如果参数无效
    """
    if not isinstance(direction, int):
        raise ValueError(f"{param_name} 必须是整数类型，当前类型: {type(direction).__name__}")

    if direction < TCP_DIRECTION_MIN or direction > TCP_DIRECTION_MAX:
        raise ValueError(
            f"{param_name} 必须在 [{TCP_DIRECTION_MIN}, {TCP_DIRECTION_MAX}] 范围内，"
            f"当前值: {direction}"
        )

    return direction


def validate_free_driving_mode(mode: int, param_name: str = "mode") -> int:
    """验证自由驱动模式参数

    Args:
        mode: 模式值 (0: 禁用, 1: 正常, 2: 强制)
        param_name: 参数名称（用于错误信息）

    Returns:
        验证后的模式值（int）

    Raises:
        ValueError: 如果参数无效
    """
    if not isinstance(mode, int):
        raise ValueError(f"{param_name} 必须是整数类型，当前类型: {type(mode).__name__}")

    if mode not in (0, 1, 2):
        raise ValueError(f"{param_name} 必须是 0（禁用）、1（正常）或 2（强制），当前值: {mode}")

    return mode
