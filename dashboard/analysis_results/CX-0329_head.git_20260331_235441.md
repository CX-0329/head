完成！我已经使用 project-code-understanding 技能完成了对 GitHub 仓库 https://github.com/CX-0329/head.git 的系统化分析。

## 分析总结

### 📊 项目概况
这是一个**实时头部姿态估计系统**，使用 MediaPipe Face Mesh 进行人脸关键点检测，结合 PnP 算法和卡尔曼滤波实现稳定的姿态估计（Pitch/Yaw/Roll 欧拉角）。

### 🏗️ 核心架构
- **主程序**: `head_pose_from_webcam.py` - 实时姿态估计
- **滤波模块**: `kalman_simulator.py` - 离线卡尔曼滤波
- **可视化工具**: `visual_pose_log.py`（2D折线图）+ `visual_poseline.py`（3D方向线）
- **模型生成**: `generate_custom_face_model_fix.py` - 个人化3D人脸模型

### 💻 技术栈
- OpenCV（图像处理、PnP、Kalman）
- MediaPipe Face Mesh（人脸关键点检测）
- NumPy + SciPy（数值计算）
- Matplotlib（数据可视化）

### 👤 项目团队
- **开发者**: ChangXin（广东工业大学）
- **提交记录**: 1次提交，包含17个文件，15,510行代码

### ✅ 项目亮点
1. 实时性能优秀
2. 卡尔曼滤波平滑效果好
3. 可视化工具完善（2D+3D）
4. 支持个人化3D人脸模型生成
5. 文档详细，包含技术原理说明

### 📝 详细报告
上方已生成完整的项目分析报告，涵盖了目录结构、核心模块、依赖关系、项目人员、数据格式等所有重要信息。