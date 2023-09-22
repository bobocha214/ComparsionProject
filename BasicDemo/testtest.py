import os

import cv2
import numpy as np

image = cv2.imread('boxed_region.jpg')

# 转换为灰度图像
gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
threshold = 145
# 对灰度图像进行二值化处理
_, binary_image = cv2.threshold(gray_image, threshold, 255, cv2.THRESH_BINARY)
cv2.imshow('binary_image', binary_image)
cv2.waitKey(0)
edges = cv2.Canny(binary_image, 127, 255)
contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
output_folder = 'image/boxs'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
for i, contour in enumerate(contours):
    img=image.copy()
    x, y, w, h = cv2.boundingRect(contour)
    cv2.rectangle(img, (x - 5, y - 5), (x + w + 5, y + h + 5), (0, 255, 0), 2)  # 使用绿色(0, 255, 0)绘制方框
    cv2.imshow('img', img)
    cv2.waitKey(0)
    roi = image[y-5:y + h+5, x-5:x + w+5]  # 这里的偏移值可以根据需求进行调整
    # 保存框出的区域为图像文件
    print(roi.size)
    # 绘制方框
    # 生成不同的文件名以避免冲突
    output_filename = os.path.join(output_folder, f'boxed_{i}.jpg')
    if roi.size > 2000:
        # 保存框出的区域为图像文件
        cv2.imwrite(output_filename, roi)


