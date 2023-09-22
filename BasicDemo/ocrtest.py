import os

import cv2
import numpy as np
from cnocr import CnOcr

# 定义图像文件夹的路径
image_folder = 'image/boxs'  # 替换为实际的文件夹路径
ocr = CnOcr()
# 获取文件夹中所有文件的列表
image_files = [f for f in os.listdir(image_folder) if f.endswith(('.jpg', '.jpeg', '.png', '.bmp'))]

# 遍历图像文件并处理
for i, image_file in enumerate(image_files):
    # 构建图像文件的完整路径
    image_path = os.path.join(image_folder, image_file)

    # 读取图像
    image = cv2.imread(image_path)

    out = ocr.ocr_for_single_line(image)
    print(image_file,out)

