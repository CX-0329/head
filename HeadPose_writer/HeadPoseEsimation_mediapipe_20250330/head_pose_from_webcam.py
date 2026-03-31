import cv2
import argparse
import numpy as np
import mediapipe as mp
from scipy.spatial.transform import Rotation as R
'''实时采集+滤波+记录数据存head_pose_log.txt'''
class KalmanFilter:
    def __init__(self):
        self.kf = cv2.KalmanFilter(6, 3)  # 6个状态变量（角度+角速度），3个观测变量（pitch, yaw, roll）

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
        self.kf.measurementNoiseCov = np.eye(3, dtype=np.float32) * 1e-2

        # 先验误差协方差矩阵 P
        self.kf.errorCovPost = np.eye(6, dtype=np.float32)

        # 初始状态
        self.kf.statePost = np.zeros((6, 1), dtype=np.float32)

    def update(self, angles):
        measurement = np.array(angles, dtype=np.float32).reshape(3, 1)
        self.kf.correct(measurement)
        prediction = self.kf.predict()
        return prediction[:3].flatten()


def extract_face_landmarks(face_landmarks):
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
    return np.load('custom_face_model.npy')


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


def cameraMatrix_fn(fl, center):
    return np.array([
        [fl, 1, center[0]],
        [0, fl, center[1]],
        [0, 0, 1]
    ], dtype=np.float64)


def main():
    cap = cv2.VideoCapture(args["camsource"])
    kf = KalmanFilter()

    while True:
        ret, img = cap.read()
        if not ret:
            print(f'[ERROR] Cannot read from source: {args["camsource"]}')
            break

        img = cv2.flip(img, 1)
        image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, c = img.shape
        results = face_mesh.process(image_rgb)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                refImgPts = extract_face_landmarks(face_landmarks.landmark)
                refImgPts[:, 0] *= w
                refImgPts[:, 1] *= h

                focalLength = args["focal"] * w if args["focal"] else max(w, h)
                cameraMatrix = cameraMatrix_fn(focalLength, (w / 2, h / 2))
                mdists = np.zeros((4, 1), dtype=np.float64)

                success, rotationVector, translationVector = cv2.solvePnP(
                    face3Dmodel, refImgPts, cameraMatrix, mdists)

                # 将 `rotationVector` 转换为欧拉角
                rmat, _ = cv2.Rodrigues(rotationVector)
                angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)

                # 卡尔曼滤波
                measurement = np.array([[angles[0]], [angles[1]], [angles[2]]], dtype=np.float32)
                filtered_angles = kf.update(measurement)  # 更新滤波器状态
                with open("head_pose_log2.txt", "a") as log_file:
                    log_file.write(f"{angles[0]} {angles[1]} {angles[2]} {filtered_angles[0]} {filtered_angles[1]} {filtered_angles[2]}\n")

                # translationVector_fittled = euler_angles_to_rotation_vec(filtered_angles)
                # rotationMatrix_fittled = R.from_euler('yzx', filtered_angles, degrees=True).as_matrix()


                # 计算鼻尖方向
                noseEndPoints3D = np.array([[0, 0, 1000.0]], dtype=np.float64)
                noseEndPoint2D, _ = cv2.projectPoints(noseEndPoints3D, rotationVector,  translationVector, cameraMatrix, mdists)

                p1 = (int(refImgPts[0, 0]), int(refImgPts[0, 1]))
                p2 = (int(noseEndPoint2D[0, 0, 0]), int(noseEndPoint2D[0, 0, 1]))
                cv2.line(img, p1, p2, (110, 220, 0), thickness=2, lineType=cv2.LINE_AA)

                cv2.putText(img, f"Pitch: {filtered_angles[0]:.2f},{angles[0]:.2f}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (0, 255, 0), 2)
                cv2.putText(img, f"Yaw: {filtered_angles[1]:.2f},{angles[1]:.2f}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0),
                            2)
                cv2.putText(img, f"Roll: {filtered_angles[2]:.2f},{angles[2]:.2f}", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                            (0, 255, 0), 2)

        cv2.imshow("Head Pose", img)
        if cv2.waitKey(10) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--focal", type=float, help="Calibrated Focal Length of the camera")
    parser.add_argument("-s", "--camsource", type=int, default=0, help="Enter the camera source")
    args = vars(parser.parse_args())

    face3Dmodel = ref3DModel()
    MP_LANDMARKS = {"nose_tip": 1, "chin": 199, "left_eye": 263, "right_eye": 33, "left_mouth": 291, "right_mouth": 61}
    main()
