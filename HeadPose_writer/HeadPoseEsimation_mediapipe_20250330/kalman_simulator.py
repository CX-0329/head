import cv2
import numpy as np
import matplotlib.pyplot as plt
"""
读取一个log，读取其中的采样数据，用for循环模拟视频流效果，展示滤波效果
重新滤波，生成滤波后数据存simulated_log.txt，滤波前后对比图
"""

class KalmanFilter:
    def __init__(self):
        self.kf = cv2.KalmanFilter(6, 3)  # 6状态变量（角度+角速度），3观测变量（pitch, yaw, roll）

        self.kf.transitionMatrix = np.array([
            [1, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 1],
            [0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1]
        ], dtype=np.float32)

        self.kf.measurementMatrix = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0]
        ], dtype=np.float32)

        # 过程噪声协方差矩阵 Q（越大越相信预测值，越小越相信观测值）
        self.kf.processNoiseCov = np.eye(6, dtype=np.float32) * 1e-5

        # 观测噪声协方差矩阵 R（决定信任测量的程度，越小越信任测量数据）
        self.kf.measurementNoiseCov = np.eye(3, dtype=np.float32) * 1e-2 # 1e-1 1e-3

        # 先验误差协方差矩阵 P
        self.kf.errorCovPost = np.eye(6, dtype=np.float32)

        # 初始状态
        self.kf.statePost = np.zeros((6, 1), dtype=np.float32)

    def update(self, angles):
        measurement = np.array(angles, dtype=np.float32).reshape(3, 1)
        self.kf.correct(measurement)
        prediction = self.kf.predict()
        return prediction[:3].flatten()


# 读取 log.txt 数据
log_file = "head_pose_log1.txt"
filtered_log_file = "simulated_log.txt"
pitch_list, yaw_list, roll_list = [], [], []
filtered_pitch, filtered_yaw, filtered_roll = [], [], []

kf = KalmanFilter()

with open(log_file, "r") as f, open(filtered_log_file, "w") as fw:
    for line in f:
        values = list(map(float, line.strip().split()))
        pitch, yaw, roll = values[:3]

        filtered_angles = kf.update([pitch, yaw, roll])

        pitch_list.append(pitch)
        yaw_list.append(yaw)
        roll_list.append(roll)

        filtered_pitch.append(filtered_angles[0])
        filtered_yaw.append(filtered_angles[1])
        filtered_roll.append(filtered_angles[2])

        fw.write(f"{pitch} {yaw} {roll} {filtered_angles[0]} {filtered_angles[1]} {filtered_angles[2]}\n")


# 绘制图像
def plot_comparison(original, filtered, title):
    plt.figure()
    plt.plot(original, label="Original", linestyle="dashed", alpha=0.7)
    plt.plot(filtered, label="Filtered", linewidth=2)
    plt.legend()
    plt.title(title)
    plt.xlabel("Frame")
    plt.ylabel("Angle (degrees)")
    plt.grid()
    plt.show()


plot_comparison(pitch_list, filtered_pitch, "Pitch")
plot_comparison(yaw_list, filtered_yaw, "Yaw")
plot_comparison(roll_list, filtered_roll, "Roll")
