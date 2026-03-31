# Head Pose Estimation with MediaPipe

基于 MediaPipe 和卡尔曼滤波的实时头部姿态估计系统。

---

## 项目概述

本项目使用 MediaPipe Face Mesh 进行人脸关键点检测，通过 PnP 算法计算头部姿态（Pitch/Yaw/Roll 欧拉角），并使用卡尔曼滤波对数据进行平滑处理。

---

## 文件说明

### 核心程序

| 文件 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `head_pose_from_webcam.py` | 实时从摄像头检测头部姿态 | 摄像头视频流 | 实时显示窗口 + 日志文件 |
| `kalman_simulator.py` | 离线卡尔曼滤波器 | 原始日志文件 | 滤波后的日志文件 + 对比图表 |
| `visual_pose_log.py` | 可视化姿态数据（折线图） | 日志文件 | Matplotlib 图表 |
| `visual_poseline.py` | 可视化姿态数据（3D方向动画） | 日志文件 | OpenCV 动画窗口 |

### 辅助工具

| 文件 | 功能 |
|------|------|
| `numpy_visual.py` | 查看 `custom_face_model.npy` 的内容 |
| `test_r.py` | 测试旋转向量与欧拉角转换（含bug） |
| `test_r2.py` | 测试旋转向量与欧拉角转换（修正版） |

### 数据文件

| 文件 | 说明 |
|------|------|
| `custom_face_model.npy` | 3D 人脸模型（6个关键点的标准3D坐标） |
| `head_pose_log1.txt` | 原始采集的头部姿态日志 |
| `head_pose_log2.txt` | 另一组采集日志 |
| `simulated_log.txt` | 卡尔曼滤波后的日志 |

---

## 依赖安装

```bash
pip install opencv-python mediapipe numpy scipy matplotlib
```

---

## 使用方法

### 1. 实时头部姿态检测

```bash
python head_pose_from_webcam.py
```

**可选参数：**
- `-f` 或 `--focal`: 相机焦距（可选，默认自动计算）
- `-s` 或 `--camsource`: 摄像头索引（默认为 0）

**示例：**
```bash
python head_pose_from_webcam.py -f 1.2 -s 0
```

**输出：**
- 实时显示窗口，展示头部姿态和方向线
- 将数据写入 `head_pose_log2.txt`
- 按 `ESC` 键退出

**日志文件格式：**
```
pitch_raw yaw_raw roll_raw pitch_filtered yaw_filtered roll_filtered
```

---

### 2. 离线卡尔曼滤波

对已有的日志文件应用卡尔曼滤波：

```bash
python kalman_simulator.py
```

**输入：** `head_pose_log1.txt`（需在代码中修改）
**输出：** `simulated_log.txt` + 对比图表

---

### 3. 可视化姿态数据

#### 方法一：折线图对比
```bash
python visual_pose_log.py
```
- 显示原始数据 vs 滤波数据的折线图对比
- 在代码中修改 `log_file_path` 变量指定要可视化的日志

#### 方法二：3D 方向动画
```bash
python visual_poseline.py
```
- 红色箭头：原始姿态方向
- 蓝色箭头：滤波后姿态方向
- 按 `q` 退出

---

## 技术原理

### 1. 人脸关键点检测

使用 MediaPipe Face Mesh 检测 6 个关键点：
- 鼻尖 (nose_tip)
- 下巴 (chin)
- 左眼 (left_eye)
- 右眼 (right_eye)
- 左嘴角 (left_mouth)
- 右嘴角 (right_mouth)

### 2. 姿态求解流程

```
1. MediaPipe 检测 2D 关键点
       ↓
2. PnP 算法求解 (cv2.solvePnP)
       ↓
3. 旋转向量 → 欧拉角 (cv2.RQDecomp3x3)
       ↓
4. 卡尔曼滤波平滑
       ↓
5. 输出结果
```

### 3. 欧拉角定义

- **Pitch**: 绕 X 轴旋转（上下点头）
- **Yaw**: 绕 Y 轴旋转（左右摇头）
- **Roll**: 绕 Z 轴旋转（左右侧头）

### 4. 卡尔曼滤波器配置

- 状态维度：6（角度 + 角速度）
- 观测维度：3（pitch, yaw, roll）
- 过程噪声协方差 Q: `1e-5`
- 观测噪声协方差 R: `1e-2`

---

## 3D 人脸模型格式

`custom_face_model.npy` 是一个 `(6, 3)` 的 numpy 数组：

```
[[  0.      0.      0.  ]   # 鼻尖（原点）
 [-170   -3216   -650 ]   # 下巴
 [-2257   1816  -1350 ]   # 左眼
 [2156   1907  -1350 ]   # 右眼
 [-1098  -1727  -1250 ]   # 左嘴角
 [1039   -1731  -1250 ]]  # 右嘴角
```

单位：毫米，以鼻尖为原点。

---

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| 摄像头无法打开 | 检查 `-s` 参数，尝试 `-s 1` 或其他索引 |
| 检测不到人脸 | 确保光线充足，正面面对摄像头 |
| 数据抖动严重 | 调整卡尔曼滤波参数（Q 和 R） |
| ImportError | 运行 `pip install -r requirements.txt` |

---

## 项目结构

```
HeadPoseEsimation_mediapipe_20250330/
├── head_pose_from_webcam.py   # 主程序
├── kalman_simulator.py         # 离线滤波器
├── visual_pose_log.py          # 折线图可视化
├── visual_poseline.py          # 方向线动画
├── numpy_visual.py             # 查看npy文件
├── test_r.py                   # 测试脚本
├── test_r2.py                  # 测试脚本（修正版）
├── custom_face_model.npy       # 3D人脸模型
├── head_pose_log1.txt          # 采集日志1
├── head_pose_log2.txt          # 采集日志2
└── simulated_log.txt           # 滤波后日志
```

---

## 参考链接

- [MediaPipe Face Mesh](https://google.github.io/mediapipe/solutions/face_mesh.html)
- [OpenCV solvePnP](https://docs.opencv.org/master/d5/d1f/calib3d_solvePnP.html)
- [Kalman Filter](https://en.wikipedia.org/wiki/Kalman_filter)
