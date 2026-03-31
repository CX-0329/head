import cv2
import argparse
import numpy as np
import mediapipe as mp
import time

"""
先运行这个录脸程序，运行结束后会在目录下生成个人脸部建模信息，然后webcam推理我已经改成了load目录下的脸部文件了。
使用方法：运行，然后程序一开始会使用经验模型辅助你判断当前的脸部朝向信息。然后按键盘a键进行拍照(每次会拍5张，每0.5s拍一次)，程序设置了5次按a的机会，建议分别拍正脸，微微向左，微微向右，微微向上和微微向下。
然后拍摄完成后会计算模型输出的均值，并归一化到一个合适的区间内然后输出。
tips；如果按a没反应，点击一下cv2的窗口，那个按键检测是绑定那个窗口的(同时检查一下输入法)
"""



exp_model = np.array([[0.0, 0.0, 0.0],  # 鼻尖
                      [0.0, -330.0, -65.0],  # 下巴
                      [-225.0, 170.0, -135.0],  # 左眼
                      [225.0, 170.0, -135.0],  # 右眼
                      [-150.0, -150.0, -125.0],  # 左嘴角
                      [150.0, -150.0, -125.0]])  # 右嘴角

# **MediaPipe 关键点索引（基于 478 关键点）**
KEYPOINTS_IDX = {
    "nose": 1,  # 鼻尖
    "chin": 199,  # 下巴
    "left_eye": 33,  # 左眼角（内侧）
    "right_eye": 263,  # 右眼角（内侧）
    "left_mouth": 61,  # 左嘴角
    "right_mouth": 291  # 右嘴角
}


def extract_face_landmarks(face_landmarks):
    """ 提取6个关键点 (nose_tip, chin, left_eye, right_eye, left_mouth, right_mouth) """
    image_points = [
        (face_landmarks[MP_LANDMARKS["nose_tip"]].x, face_landmarks[MP_LANDMARKS["nose_tip"]].y),
        (face_landmarks[MP_LANDMARKS["chin"]].x, face_landmarks[MP_LANDMARKS["chin"]].y),
        (face_landmarks[MP_LANDMARKS["left_eye"]].x, face_landmarks[MP_LANDMARKS["left_eye"]].y),
        (face_landmarks[MP_LANDMARKS["right_eye"]].x, face_landmarks[MP_LANDMARKS["right_eye"]].y),
        (face_landmarks[MP_LANDMARKS["left_mouth"]].x, face_landmarks[MP_LANDMARKS["left_mouth"]].y),
        (face_landmarks[MP_LANDMARKS["right_mouth"]].x, face_landmarks[MP_LANDMARKS["right_mouth"]].y),
    ]
    return np.array(image_points, dtype=np.float64)


def ref3DModel():
    # modelPoints = np.load('custom_face_model.npy')
    modelPoints = exp_model
    return np.array(modelPoints, dtype=np.float64)


def cameraMatrix_fn(fl, center):
    mat = [[fl, 1, center[0]],
           [0, fl, center[1]],
           [0, 0, 1]]
    return np.array(mat, dtype=np.float64)


def get_keypoints(h, w, face_landmarks):
    keypoints = []
    for name, idx in KEYPOINTS_IDX.items():
        landmark = face_landmarks.landmark[idx]
        x, y = int(landmark.x * w), int(landmark.y * h)  # **转换到图像坐标**
        keypoints.append([landmark.x, landmark.y, landmark.z])

    return keypoints


def generate_custom_model(keypoints_list):
    # **计算 10 张图片的均值**
    keypoints_array = np.array(keypoints_list)  # (10, 6, 3)
    avg_keypoints = np.mean(keypoints_array, axis=0)  # (6, 3)

    # **修正 1：对齐鼻尖 (0,0,0)**
    nose_position = avg_keypoints[0]  # 鼻尖坐标
    aligned_keypoints = avg_keypoints - nose_position  # **让鼻尖变成 (0,0,0)**

    # **修正 2：翻转 Y 轴**
    aligned_keypoints[:, 1] *= -1  # **翻转 y 轴方向**

    # **修正 3：计算缩放因子**
    scale_x = np.linalg.norm(exp_model[3] - exp_model[2]) / np.linalg.norm(
        aligned_keypoints[3] - aligned_keypoints[2])
    scale_y = np.linalg.norm(exp_model[1] - exp_model[0]) / np.linalg.norm(
        aligned_keypoints[1] - aligned_keypoints[0])

    # **修正 4：应用缩放**
    scaled_keypoints = np.copy(aligned_keypoints)
    scaled_keypoints[:, 0] *= scale_x
    scaled_keypoints[:, 1] *= scale_y

    # **🚀 关键修正：保留 modelPoints 的 z 轴**
    scaled_keypoints[:, 2] = exp_model[:, 2]  # **直接使用标准模型的 Z 轴**

    return scaled_keypoints


def main():
    # cap = cv2.VideoCapture(args["camsource"])
    #cap = cv2.VideoCapture("head_pose1.MP4")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("❌ Failed to open video file")
    model_list = []
    mode = 0
    # 提前初始化，避免在进入采集模式前变量未定义导致编辑器或静态检查标红
    keypoints_list = []

    while True:
        GAZE = "Face Not Found"
        ret, frame = cap.read()
        if not ret:
            print("[INFO] Video finished (no more frames).")
            break

        # 缩放比例
        scale_percent = 30  # 原始尺寸的30%
        width = int(frame.shape[1] * scale_percent / 100)
        height = int(frame.shape[0] * scale_percent / 100)
        img = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

        img = cv2.flip(img, 1)

        image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, c = img.shape

        # 处理人脸检测和关键点提取
        results = face_mesh.process(image_rgb)

        if results.multi_face_landmarks:
            if mode == 0:
                for face_landmarks in results.multi_face_landmarks:
                    # 提取6个关键点
                    refImgPts = extract_face_landmarks(face_landmarks.landmark)

                    # 还原到像素坐标
                    refImgPts[:, 0] *= w
                    refImgPts[:, 1] *= h

                    height, width, _ = img.shape
                    focalLength = args["focal"] * width if args["focal"] else max(width, height)
                    cameraMatrix = cameraMatrix_fn(focalLength, (width / 2, height / 2))
                    mdists = np.zeros((4, 1), dtype=np.float64)

                    # 计算姿态
                    success, rotationVector, translationVector = cv2.solvePnP(
                        face3Dmodel, refImgPts, cameraMatrix, mdists)

                    # 计算朝向
                    noseEndPoints3D = np.array([[0, 0, 1000.0]], dtype=np.float64)
                    noseEndPoint2D, _ = cv2.projectPoints(noseEndPoints3D, rotationVector, translationVector, cameraMatrix,
                                                          mdists)

                    # 绘制鼻尖方向线
                    p1 = (int(refImgPts[0, 0]), int(refImgPts[0, 1]))
                    p2 = (int(noseEndPoint2D[0, 0, 0]), int(noseEndPoint2D[0, 0, 1]))
                    cv2.line(img, p1, p2, (110, 220, 0), thickness=2, lineType=cv2.LINE_AA)

                    # 计算欧拉角
                    rmat, _ = cv2.Rodrigues(rotationVector)
                    angles, _, _, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)
                    # angles[0] → 俯仰角（Pitch）（围绕X轴旋转）
                    # angles[1] → 偏航角（Yaw）（围绕Y轴旋转）
                    # angles[2] → 滚转角（Roll）（围绕Z轴旋转）

                    Pitch_thr = 10
                    Yaw_thr = 15

                    if angles[1] < -Yaw_thr:
                        GAZE = "Looking: Right"
                    elif angles[1] > Yaw_thr:
                        GAZE = "Looking: Left"
                    elif angles[0] > Pitch_thr:
                        GAZE = "Looking: Down"
                    elif angles[0] < -Pitch_thr:
                        GAZE = "Looking: Up"
                    else:
                        GAZE = "Looking: Forward"

                    # print(GAZE, "左右转头角度:", angles[1], "上下转头角度", angles[0])

                # 显示方向
                cv2.putText(img, GAZE, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 80), 2)
                cv2.imshow("Head Pose", img)

            if mode == 1:
                if len(keypoints_list) < 5:
                    for face_landmarks in results.multi_face_landmarks:
                        keypoints_list.append(get_keypoints(h, w, face_landmarks))
                        print(f"[INFO] Captured {len(keypoints_list)} images")
                        time.sleep(0.5)
                        break
                elif len(keypoints_list) >= 5:
                    model = generate_custom_model(keypoints_list)
                    model_list.append(model)
                    mode = 0
                    print('采集完成')

        if len(model_list) >= 5:
            # 对models_list进行均值处理
            models_array = np.array(model_list)  # (10, 6, 3)
            avg_model = np.mean(models_array, axis=0)

            np.save("custom_face_model_cx.npy", avg_model)
            print("[INFO] Scaled Custom 3D face model saved as 'custom_face_model_cx.npy'")

            # **最终数据对比**
            print(avg_model)
            print('--------------------------------------------')
            print(exp_model)
            break

        key = cv2.waitKey(10) & 0xFF
        if key == 27:  # ESC 退出
            break
        elif key == ord('a'):
            print('进入采集模式')
            keypoints_list = []
            mode = 1  # 进入采集模式

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # MediaPipe 设置
    mp_face_mesh = mp.solutions.face_mesh
    mp_drawing = mp.solutions.drawing_utils
    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--focal", type=float, help="Callibrated Focal Length of the camera")
    parser.add_argument("-s", "--camsource", type=int, default=0, help="Enter the camera source")
    args = vars(parser.parse_args())

    face3Dmodel = ref3DModel()

    # **MediaPipe 关键点索引（替代 dlib）**
    MP_LANDMARKS = {
        "nose_tip": 1,  # 鼻尖 (原dlib 30)
        "chin": 199,  # 下巴 (原dlib 8)
        "left_eye": 263,  # 左眼角 (原dlib 36)
        "right_eye": 33,  # 右眼角 (原dlib 45)
        "left_mouth": 291,  # 左嘴角 (原dlib 48)
        "right_mouth": 61  # 右嘴角 (原dlib 54)
    }
    main()