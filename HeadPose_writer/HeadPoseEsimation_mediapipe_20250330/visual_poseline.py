import cv2
import numpy as np
'''3D原始箭头与滤波箭头比较'''
def load_log_data(log_file_path):
    """加载日志数据"""
    data = np.loadtxt(log_file_path)
    angles = data[:, :3]  # 原始角度 (pitch, yaw, roll)
    filtered_angles = data[:, 3:]  # 滤波后角度 (pitch, yaw, roll)
    return angles, filtered_angles

def euler_angles_to_rotation_vec(angles):
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
    rmat_reconstructed = R_z @ R_y @ R_x

    rotation_vector_re, _ = cv2.Rodrigues(rmat_reconstructed)

    return rotation_vector_re

def draw_pose(frame, rotation_vector, translation_vector, camera_matrix, color):
    """
    在 frame 上绘制 3D 方向指向线
    :param frame: 要绘制的画布 (numpy 数组)
    :param angles: 欧拉角 (pitch, yaw, roll)
    :param rotation_vector: 旋转向量
    :param translation_vector: 平移向量
    :param camera_matrix: 相机内参矩阵
    :param color: 线条颜色 (BGR)
    """
    # 1. 将欧拉角转换为旋转矩阵
    rmat, _ = cv2.Rodrigues(rotation_vector)

    # 2. 假设鼻尖位置（一个点）在 3D 空间中的位置（单位：毫米）
    nose_end_point_3d = np.array([[0, 0, 1000.0]], dtype=np.float64)  # 鼻尖距离相机1000mm

    # 3. 计算 3D 点投影到 2D 图像平面
    nose_end_point_2d, _ = cv2.projectPoints(nose_end_point_3d,
                                              rotation_vector,  # 旋转向量
                                              translation_vector,  # 平移向量
                                              camera_matrix, np.zeros((4, 1)))  # 假设没有畸变

    # 4. 获取图像中的鼻尖位置（投影后的 2D 点）
    p1 = (int(frame.shape[1] / 2), int(frame.shape[0] / 2))  # 图像中心点，作为原点
    p2 = (int(nose_end_point_2d[0, 0, 0]), int(nose_end_point_2d[0, 0, 1]))  # 鼻尖位置（2D 投影）

    # 5. 绘制原始数据方向
    cv2.arrowedLine(frame, p1, p2, color, 3, tipLength=0.03)

def visualize(log_file_path, camera_matrix):
    """模拟播放头部姿态数据"""
    angles, filtered_angles = load_log_data(log_file_path)
    num_frames = len(angles)

    # 假设的平移向量（相机位置）
    translation_vector = np.array([0, 0, 0], dtype=np.float32)  # 这里假设相机在原点

    for i in range(num_frames):
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 255  # 白色背景

        # 1. 绘制原始数据方向（红色）
        rotation_vector = euler_angles_to_rotation_vec(angles[i])
        draw_pose(frame, rotation_vector, translation_vector, camera_matrix, (0, 0, 255))

        # 2. 绘制滤波后数据方向（蓝色）
        rotation_vector = euler_angles_to_rotation_vec(filtered_angles[i])  # 转为弧度
        draw_pose(frame, rotation_vector, translation_vector, camera_matrix, (255, 0, 0))

        # 3. 显示
        cv2.imshow("Head Pose Visualization", frame)
        if cv2.waitKey(int(1000 / 30)) & 0xFF == ord('q'):  # 每帧间隔 50ms，按 'q' 退出
            break

    cv2.destroyAllWindows()

# 相机内参矩阵（假设的）
camera_matrix = np.array([[640, 0, 320],
                          [0, 480, 240],
                          [0, 0, 1]], dtype=np.float32)

# 运行可视化
log_file_path = "head_pose_log2.txt"  # 替换为实际的日志文件路径
visualize(log_file_path, camera_matrix)
