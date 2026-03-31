import matplotlib.pyplot as plt
import numpy as np
'''2D给数据作图不处理'''

"""
Visual Pose Log
可视化log，可视化其中的采集和滤波后效果
"""


def load_log_data(log_file_path):
    data = np.loadtxt(log_file_path)
    angles = data[:, :3]  # 原始角度 (pitch, yaw, roll)
    filtered_angles = data[:, 3:]  # 滤波后角度 (pitch, yaw, roll)
    return angles, filtered_angles

def plot_angles(angles, filtered_angles, title, index):
    plt.figure(title)
    plt.plot(angles[:, index], label='Original', linestyle='dashed', color='red')
    plt.plot(filtered_angles[:, index], label='Filtered', linestyle='solid', color='blue')
    plt.xlabel('Frame')
    plt.ylabel('Angle (degrees)')
    plt.title(title)
    plt.legend()
    plt.grid(True)

def visualize(log_file_path):
    angles, filtered_angles = load_log_data(log_file_path)
    plot_angles(angles, filtered_angles, 'Pitch Angle', 0)
    plot_angles(angles, filtered_angles, 'Yaw Angle', 1)
    plot_angles(angles, filtered_angles, 'Roll Angle', 2)
    plt.show()

# 调用可视化函数
log_file_path = "head_pose_log1.txt"  # 替换为实际的日志文件路径
# log_file_path = "simulated_log.txt"
visualize(log_file_path)
