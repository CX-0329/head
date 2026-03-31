import numpy as np

"""
用来比较经验模型和生成模型的差异
"""

exp_model = np.array([[0.0, 0.0, 0.0],  # 鼻尖
                        [0.0, -330.0, -65.0],  # 下巴
                        [-225.0, 170.0, -135.0],  # 左眼
                        [225.0, 170.0, -135.0],  # 右眼
                        [-150.0, -150.0, -125.0],  # 左嘴角
                        [150.0, -150.0, -125.0]])  # 右嘴角

media_model = np.load('./custom_face_model_test.npy')

np.set_printoptions(precision=2, suppress=True)

print('经验模型:\n',exp_model)
print('生成模型:\n',media_model)