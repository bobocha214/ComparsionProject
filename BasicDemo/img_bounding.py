# import os
# import cv2
# import numpy as np
#
# def process_image(input_image_path, output_directory, threshold=150, kernel_threshold=80, area_threshold=4000, area_threshold_high=150000):
#     # 读取图像
#     image = cv2.imread(input_image_path)
#
#     # 转换为灰度图像
#     gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
#
#     # 对灰度图像进行二值化处理
#     _, binary_image = cv2.threshold(gray_image, threshold, 255, cv2.THRESH_BINARY)
#
#     # 执行边缘检测，例如使用Canny算法
#     edges = cv2.Canny(binary_image, 30, 255)
#
#     # 使用形态学操作来连接相邻的轮廓
#     kernel = np.ones((1, kernel_threshold), np.uint8)
#     closed_image = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
#
#     # 寻找轮廓
#     contours, _ = cv2.findContours(closed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#
#     # 创建一个副本以绘制方框
#     image_with_boxes = image.copy()
#
#     # 创建目录以保存图像
#     os.makedirs(output_directory, exist_ok=True)
#
#     # 创建一个列表来存储满足面积阈值条件的轮廓
#     filtered_contours = []
#
#     # 遍历轮廓
#     for contour in contours:
#         # 计算轮廓的面积
#         area = cv2.contourArea(contour)
#
#         # 如果面积在阈值范围内，则添加到列表中
#         if area_threshold < area < area_threshold_high:
#             filtered_contours.append(contour)
#             x, y, w, h = cv2.boundingRect(contour)
#             # 绘制方框
#             cv2.rectangle(image_with_boxes, (x, y), (x + w, y + h), (0, 255, 0), 2)
#
#     # 保存带有方框的图像
#     output_image_path = os.path.join(output_directory, 'image_with_boxes.jpg')
#     cv2.imwrite(output_image_path, image_with_boxes)
#
#     # 保存满足条件的轮廓图像
#     for i, contour in enumerate(filtered_contours):
#         x, y, w, h = cv2.boundingRect(contour)
#         roi = image[y:y + h, x:x + w]
#         filename = os.path.join(output_directory, f'cut_{i}.jpg')
#         cv2.imwrite(filename, roi)
#
# # 示例调用
# input_image_path = 'image/test.jpg'
# output_directory = 'cuts'
# process_image(input_image_path, output_directory)


import os

import cv2
import numpy as np
from matplotlib import pyplot as plt

# 读取图像
image = cv2.imread('image/demo.jpg')

# 转换为灰度图像
gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
threshold = 200
# 对灰度图像进行二值化处理
_, binary_image = cv2.threshold(gray_image, threshold, 255, cv2.THRESH_BINARY)
cv2.namedWindow('binary_image', cv2.WINDOW_NORMAL)
cv2.imshow('binary_image', binary_image)
cv2.waitKey(0)
# 执行边缘检测，例如使用Canny算法
edges = cv2.Canny(binary_image, 30, 255)
# 使用形态学操作来连接相邻的轮廓
kernel_threshold = 50
kernel = np.ones((1, kernel_threshold), np.uint8)
cv2.namedWindow('edges', cv2.WINDOW_NORMAL)
cv2.imshow('edges', edges)
cv2.waitKey(0)

closed_image = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
cv2.namedWindow('closed_image', cv2.WINDOW_NORMAL)
cv2.imshow('closed_image', closed_image)
cv2.waitKey(0)
# 寻找轮廓
contours, _ = cv2.findContours(closed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
# 创建一个副本以绘制方框
image_with_boxes = image.copy()

# 定义面积阈值，用于过滤小的轮廓
area_threshold = 4000
area_threshold_high = 150000

# 创建一个列表来存储满足面积阈值条件的轮廓
filtered_contours = []
print(len(contours))

# 遍历轮廓
for contour in contours:
    # 计算轮廓的面积
    area = cv2.contourArea(contour)
    print(area)

    # 如果面积大于阈值，则添加到列表中
    if area_threshold < area < area_threshold_high:
        filtered_contours.append(contour)
        x, y, w, h = cv2.boundingRect(contour)
        # 绘制方框
        cv2.rectangle(image_with_boxes, (x, y), (x + w, y + h), (0, 255, 0), 2)  # 这里使用绿色(0, 255, 0)绘制方框

# 按照面积从大到小排序轮廓
filtered_contours.sort(key=lambda x: cv2.contourArea(x), reverse=True)



# 创建目录以保存图像
output_directory = 'cuts'
os.makedirs(output_directory, exist_ok=True)

# 保存后4个轮廓
# for i in range(len(filtered_contours) - num_contours_to_save, len(filtered_contours)):
# 获取轮廓
for i in range(0, len(filtered_contours)):
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
