import cv2
import numpy as np





def euler_angles_to_rotation_matrix(angles):
    """从欧拉角计算旋转矩阵 (Z-Y-X 顺序)"""
    angles = np.radians(angles)  # 转换为弧度
    R_x = np.array([[1, 0, 0],
                    [0, np.cos(angles[0]), -np.sin(angles[0])],
                    [0, np.sin(angles[0]), np.cos(angles[0])]])

    R_y = np.array([[np.cos(angles[1]), 0, np.sin(angles[1])],
                    [0, 1, 0],
                    [-np.sin(angles[1]), 0, np.cos(angles[1])]])

    R_z = np.array([[np.cos(angles[2]), -np.sin(angles[2]), 0],
                    [np.sin(angles[2]), np.cos(angles[2]), 0],
                    [0, 0, 1]])

    # 旋转矩阵（ZYX 旋转顺序）

    rmat_reconstructed = R_z @ R_y @ R_y

    rotation_vector_re, _ = cv2.Rodrigues(rmat_reconstructed)

    return rotation_vector_re

while True:
    # 1. 生成一个随机旋转向量
    rotation_vector = np.random.rand(3, 1) * 2 * np.pi - np.pi  # [-π, π] 范围
    rmat_original, _ = cv2.Rodrigues(rotation_vector)  # 生成旋转矩阵

    # 2. 计算欧拉角
    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat_original)

    data = (angles[0], angles[1], angles[2])

    # 3. 用欧拉角逆推旋转矩阵
    rotation_vector_re = euler_angles_to_rotation_matrix(data)


    # 4. 误差计算（判断是否接近原vec）
    difference = np.linalg.norm(rotation_vector - rotation_vector_re)

    # 结果输出
    print("Original Rotation Vec:\n", rotation_vector)

    print("\nReconstructed Rotation Vec:\n", rotation_vector_re)
    print("\nDifference:", difference)

    # 判断是否近似相等
    tolerance = 1e-1
    if difference < tolerance :
        print("\n✅ 验证成功：逆推的旋转矩阵与原始矩阵一致！")
    else:
        print("\n❌ 验证失败：矩阵不匹配，可能有数值误差或旋转顺序问题。")
