import cv2
import numpy as np
import os

# 读取图像
image = cv2.imread('image/NEW/cut_save1.jpg')

# 转换为灰度图像
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 使用Canny边缘检测
edges = cv2.Canny(gray, 100, 200)

# 查找轮廓
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 过滤掉小轮廓
filtered_contours = [contour for contour in contours if cv2.contourArea(contour) > 100]

# 保存扶正后的图像的目录
outputdir = 'output_images'

if not os.path.exists(outputdir):
    os.makedirs(outputdir)

# 旋转函数
def rotate_image(image, angle):
    height, width = image.shape[:2]
    center = (width / 2, height / 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1)
    rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height), flags=cv2.INTER_LINEAR)
    return rotated_image

# 对每个轮廓
for i, contour in enumerate(filtered_contours):
    x, y, w, h = cv2.boundingRect(contour)
    roi = image[y:y + h, x:x + w]

    # 获取轮廓的角度
    rect = cv2.minAreaRect(contour)
    angle = rect[2]

    # 角度在30度以内时，进行旋转
    if abs(angle) < 30:
        rotated_image = rotate_image(roi, angle)
        filename = os.path.join(outputdir, f'cut_{i}.jpg')
        cv2.imwrite(filename, rotated_image)
    else:
        # 如果角度大于30度，不进行旋转
        filename = os.path.join(outputdir, f'cut_{i}.jpg')
        cv2.imwrite(filename, roi)
