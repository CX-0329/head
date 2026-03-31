import numpy as np
import cv2

def euler_to_rotvec(yaw, pitch, roll, degrees=False):
    """
    将欧拉角转换为旋转向量（轴角表示）
    参数：
        yaw: Z轴旋转角度（yaw）
        pitch: Y轴旋转角度（pitch）
        roll: X轴旋转角度（roll）
        degrees: 输入角度是否为度数（默认为弧度）
    返回：
        rotvec: 旋转向量（轴角表示），形状为(3,)
    """
    if degrees:
        yaw = np.radians(yaw)
        pitch = np.radians(pitch)
        roll = np.radians(roll)

    # 计算各轴旋转矩阵
    Rz = np.array([
        [np.cos(yaw), -np.sin(yaw), 0],
        [np.sin(yaw), np.cos(yaw), 0],
        [0, 0, 1]
    ])

    Ry = np.array([
        [np.cos(pitch), 0, np.sin(pitch)],
        [0, 1, 0],
        [-np.sin(pitch), 0, np.cos(pitch)]
    ])

    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(roll), -np.sin(roll)],
        [0, np.sin(roll), np.cos(roll)]
    ])

    # 组合旋转矩阵 R = Rz @ Ry @ Rx
    R = Rz @ Ry @ Rx

    # 转换为旋转向量
    trace = np.trace(R)
    cos_theta = (trace - 1) / 2
    cos_theta = np.clip(cos_theta, -1.0, 1.0)  # 避免数值误差
    theta = np.arccos(cos_theta)

    if theta < 1e-10:
        return np.zeros(3)

    # 计算旋转轴
    axis = np.array([
        R[2, 1] - R[1, 2],
        R[0, 2] - R[2, 0],
        R[1, 0] - R[0, 1]
    ])
    axis /= (2 * np.sin(theta))

    # 确保归一化（处理可能的数值误差）
    axis /= np.linalg.norm(axis)

    return theta * axis


def rotvec_to_euler(rotvec, degrees=False):
    """
    将旋转向量转换为欧拉角（Z-Y-X顺序）
    参数：
        rotvec: 旋转向量（轴角表示），形状为(3,)
        degrees: 是否返回角度值（默认为弧度）
    返回：
        (yaw, pitch, roll): 欧拉角（Z-Y-X顺序）
    """
    theta = np.linalg.norm(rotvec)

    if theta < 1e-10:
        return (0.0, 0.0, 0.0)

    k = rotvec / theta
    K = np.array([
        [0, -k[2], k[1]],
        [k[2], 0, -k[0]],
        [-k[1], k[0], 0]
    ])

    # 罗德里格斯公式计算旋转矩阵
    R = np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * (K @ K)

    # 分解为Z-Y-X欧拉角
    pitch = np.arcsin(-R[2, 0])
    cos_pitch = np.cos(pitch)

    if np.abs(cos_pitch) > 1e-6:
        yaw = np.arctan2(R[1, 0] / cos_pitch, R[0, 0] / cos_pitch)
        roll = np.arctan2(R[2, 1] / cos_pitch, R[2, 2] / cos_pitch)
    else:
        # 处理万向节锁情况
        yaw = 0.0
        if R[2, 0] < 0:  # pitch = π/2
            roll = np.arctan2(R[0, 1], R[0, 2])
        else:  # pitch = -π/2
            roll = -np.arctan2(R[0, 1], R[0, 2])

    if degrees:
        yaw = np.degrees(yaw)
        pitch = np.degrees(pitch)
        roll = np.degrees(roll)

    return (yaw, pitch, roll)


if __name__ == "__main__":
    while True:
        # 生成随机旋转向量（约束角度在 [0, π]）
        theta = np.random.uniform(0, np.pi)  # 旋转角度
        axis = np.random.rand(3)
        axis /= np.linalg.norm(axis)  # 随机单位轴
        rotation_vector = theta * axis

        print("\n\n原始旋转向量:", rotation_vector)

        # 转换为欧拉角
        yaw, pitch, roll = rotvec_to_euler(rotation_vector, degrees=True)
        print('欧拉角:', yaw, pitch, roll)

        # 转换回旋转向量
        rotation_vector_re = euler_to_rotvec(yaw, pitch, roll, degrees=True)
        print("转换后旋转向量:", rotation_vector_re)

        # 比较旋转矩阵的差异
        from scipy.spatial.transform import Rotation
        R_original = Rotation.from_rotvec(rotation_vector).as_matrix()
        R_reconstructed = Rotation.from_rotvec(rotation_vector_re).as_matrix()
        difference = np.linalg.norm(R_original - R_reconstructed)

        tolerance = 1e-6
        if difference < tolerance:
            print("\n✅ 验证成功：旋转矩阵一致！")
        else:
            print("\n❌ 验证失败：矩阵差异为", difference)
