"""参数验证器的单元测试

测试所有验证器函数的正确性和边界情况。
"""

import pytest

from server.validators import (
    validate_acceleration,
    validate_free_driving_mode,
    validate_joints,
    validate_pose,
    validate_tcp_direction,
    validate_velocity,
)


class TestValidateJoints:
    """测试关节值验证"""

    def test_valid_joints(self):
        """测试有效的关节值"""
        joints = [0.0, 0.1, -0.2, 1.5, -0.5, 0.8, 0.0]
        result = validate_joints(joints)
        assert len(result) == 7
        assert result == joints

    def test_valid_joints_from_list(self):
        """测试从列表验证"""
        joints = [0.0] * 7
        result = validate_joints(joints)
        assert len(result) == 7

    def test_invalid_length_too_short(self):
        """测试长度不足"""
        with pytest.raises(ValueError, match="必须是7个值"):
            validate_joints([0.0] * 6)

    def test_invalid_length_too_long(self):
        """测试长度过长"""
        with pytest.raises(ValueError, match="必须是7个值"):
            validate_joints([0.0] * 8)

    def test_none_value(self):
        """测试 None 值"""
        with pytest.raises(ValueError, match="不能为 None"):
            validate_joints(None)

    def test_out_of_range_positive(self):
        """测试超出正范围"""
        with pytest.raises(ValueError):
            validate_joints([4.0] + [0.0] * 6)  # 超出 ±π

    def test_out_of_range_negative(self):
        """测试超出负范围"""
        with pytest.raises(ValueError):
            validate_joints([-4.0] + [0.0] * 6)  # 超出 ±π

    def test_json_string_input(self):
        """测试 JSON 字符串输入"""
        import json

        joints_json = json.dumps([0.0] * 7)
        result = validate_joints(joints_json)
        assert len(result) == 7


class TestValidatePose:
    """测试 TCP 姿态验证"""

    def test_valid_pose(self):
        """测试有效的姿态值"""
        pose = [0.3, 0.2, 0.5, 0.0, 1.57, 0.0]
        result = validate_pose(pose)
        assert len(result) == 6
        assert result == pose

    def test_invalid_length(self):
        """测试无效长度"""
        with pytest.raises(ValueError, match="必须是6个值"):
            validate_pose([0.0] * 5)

    def test_none_value(self):
        """测试 None 值"""
        with pytest.raises(ValueError, match="不能为 None"):
            validate_pose(None)


class TestValidateVelocity:
    """测试速度验证"""

    def test_valid_velocity(self):
        """测试有效速度"""
        assert validate_velocity(0.5) == 0.5
        assert validate_velocity(0.0) == 0.0
        assert validate_velocity(1.0) == 1.0

    def test_velocity_as_int(self):
        """测试整数速度（应转换为 float）"""
        result = validate_velocity(1)
        assert isinstance(result, float)
        assert result == 1.0

    def test_negative_velocity(self):
        """测试负速度（应被拒绝）"""
        with pytest.raises(ValueError, match="必须大于等于"):
            validate_velocity(-0.1)

    def test_too_large_velocity(self):
        """测试过大的速度"""
        with pytest.raises(ValueError, match="必须小于等于"):
            validate_velocity(2.0)

    def test_zero_velocity(self):
        """测试零速度（边界值）"""
        assert validate_velocity(0.0) == 0.0


class TestValidateAcceleration:
    """测试加速度验证"""

    def test_valid_acceleration(self):
        """测试有效加速度"""
        assert validate_acceleration(0.5) == 0.5

    def test_negative_acceleration(self):
        """测试负加速度"""
        with pytest.raises(ValueError, match="必须大于等于"):
            validate_acceleration(-0.1)

    def test_too_large_acceleration(self):
        """测试过大的加速度"""
        with pytest.raises(ValueError, match="必须小于等于"):
            validate_acceleration(2.0)


class TestValidateTcpDirection:
    """测试 TCP 方向验证"""

    def test_valid_directions(self):
        """测试有效方向"""
        for direction in range(-1, 6):
            assert validate_tcp_direction(direction) == direction

    def test_invalid_direction_too_low(self):
        """测试方向值过小"""
        with pytest.raises(ValueError):
            validate_tcp_direction(-2)

    def test_invalid_direction_too_high(self):
        """测试方向值过大"""
        with pytest.raises(ValueError):
            validate_tcp_direction(6)


class TestValidateFreeDrivingMode:
    """测试自由驱动模式验证"""

    def test_valid_modes(self):
        """测试有效模式"""
        assert validate_free_driving_mode(0) == 0  # 禁用
        assert validate_free_driving_mode(1) == 1  # 正常
        assert validate_free_driving_mode(2) == 2  # 强制

    def test_invalid_mode(self):
        """测试无效模式"""
        with pytest.raises(ValueError, match="必须是 0、1 或 2"):
            validate_free_driving_mode(3)

    def test_negative_mode(self):
        """测试负模式"""
        with pytest.raises(ValueError, match="必须是 0、1 或 2"):
            validate_free_driving_mode(-1)
