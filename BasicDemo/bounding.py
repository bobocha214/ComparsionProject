import os

import cv2
import numpy as np

# 读取图像
image = cv2.imread('image/TEST/TE3.jpg')

# 转换为灰度图像
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 对灰度图像进行二值化处理
_, binary_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# 执行边缘检测，例如使用Canny算法
edges = cv2.Canny(binary_image, 127, 255)

# 使用形态学操作来连接相邻的轮廓
kernel = np.ones((45, 45), np.uint8)
closed_image = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

cv2.imshow('image', closed_image)
cv2.waitKey(0)
# 寻找轮廓
contours, _ = cv2.findContours(closed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 创建一个副本以绘制方框
image_with_boxes = image.copy()

# 定义面积阈值，用于过滤小的轮廓
area_threshold = 3000

# 创建一个列表来存储满足面积阈值条件的轮廓
filtered_contours = []

# 遍历轮廓
for contour in contours:
    # 计算轮廓的面积
    area = cv2.contourArea(contour)

    # 如果面积大于阈值，则添加到列表中
    if area > area_threshold:
        filtered_contours.append(contour)
        x, y, w, h = cv2.boundingRect(contour)
        # 绘制方框
        cv2.rectangle(image_with_boxes, (x, y), (x + w, y + h), (0, 255, 0), 2)  # 这里使用绿色(0, 255, 0)绘制方框

# 按照面积从大到小排序轮廓
filtered_contours.sort(key=lambda x: cv2.contourArea(x), reverse=True)

# 指定要保存的后4个轮廓数量
num_contours_to_save = min(4, len(filtered_contours))  # 在这里保存后4个轮廓，可以根据需要更改数量

# 创建目录以保存图像
output_directory = 'cuts'
os.makedirs(output_directory, exist_ok=True)

# 保存后4个轮廓
# for i in range(len(filtered_contours) - num_contours_to_save, len(filtered_contours)):
    # 获取轮廓
for i in range(1, 2):
    contour = filtered_contours[i]
    # 提取并保存框出来的图形
    x, y, w, h = cv2.boundingRect(contour)
    roi = image[y:y + h, x:x + w]
    # 生成唯一的文件名，以防覆盖
    filename = os.path.join(output_directory, f'cut_{i}.jpg')
    # 保存轮廓图像
    cv2.imwrite(filename, roi)
# 保存带有方框的图像
cv2.imwrite('image/image_with_boxes.jpg', image_with_boxes)