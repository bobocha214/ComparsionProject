import cv2
import numpy as np


def contour_sort_key(contour):
    x, y, w, h = cv2.boundingRect(contour)
    return x
# 读取 matched_region 和 partial_image
matched_region = cv2.imread('matched_region.jpg')
partial_image = cv2.imread('cut_0.jpg')

# 转换为灰度图
partial_image_gray = cv2.cvtColor(partial_image, cv2.COLOR_BGR2GRAY)
matched_image_gray = cv2.cvtColor(matched_region, cv2.COLOR_BGR2GRAY)

# 二值化 partial_image
_, partial_image_binary = cv2.threshold(partial_image_gray, 145, 255, cv2.THRESH_BINARY_INV)

# 二值化 full_image
_, full_image_binary = cv2.threshold(matched_image_gray, 180, 255, cv2.THRESH_BINARY_INV)

# 查找轮廓
contours_partial, _ = cv2.findContours(partial_image_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours_full, _ = cv2.findContours(full_image_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
image_with_boxes = matched_region.copy()
image_with_boxes1 = partial_image.copy()
filtered_contours=[]
filtered_contours1=[]
merged_contour_x, merged_contour_y = [], []
# sorted_contours = sorted(filtered_contours, key=contour_sort_key)
# # 遍历轮廓
# for contour in contours_full:
#     area = cv2.contourArea(contour)
#     filtered_contours.append(contour)
#     print(area,'contours_full')
#     rect = cv2.minAreaRect(contour)
#     box = cv2.boxPoints(rect)
#     box = np.int0(box)
#     cv2.drawContours(image_with_boxes, [box], 0, (0, 0, 255), 2)
#     cv2.imshow("image_with_boxes", image_with_boxes)
#
#
# for contour in contours_partial:
#     area = cv2.contourArea(contour)
#     filtered_contours1.append(contour)
#     print(area,'contours_partial')
# sorted_contours = sorted(filtered_contours, key=contour_sort_key)
#
# sorted_contours1 = sorted(filtered_contours1, key=contour_sort_key)
#
# for contour in sorted_contours:
#     x, y, w, h = cv2.boundingRect(contour)
#     merged_contour_x.append(x)
#     merged_contour_x.append(x + w)
#     merged_contour_y.append(y)
#     merged_contour_y.append(y + h)
#
#
#
# for contour in sorted_contours1:
#     x, y, w, h = cv2.boundingRect(contour)
#     merged_contour_x.append(x)
#     merged_contour_x.append(x + w)
#     merged_contour_y.append(y)
#     merged_contour_y.append(y + h)
#     cv2.rectangle(image_with_boxes1, (x, y), (x + w, y + h), (0, 255, 0), 2)
#     cv2.imshow("image_with_boxes1", image_with_boxes1)
#
# # 计算包围所有矩形的大边界框
# x = min(merged_contour_x)
# y = min(merged_contour_y)
# w = max(merged_contour_x) - x
# h = max(merged_contour_y) - y
# # 在原图中截取该区域
# # 绘制方框
# # cv2.rectangle(image_with_boxes, (x, y), (x + w, y + h), (0, 255, 0), 2)
# # cv2.imshow("image_with_boxes", image_with_boxes)
# cv2.rectangle(image_with_boxes1, (x, y), (x + w, y + h), (0, 255, 0), 2)
# cv2.imshow("image_with_boxes1", image_with_boxes1)
# 合并contours_full中的所有轮廓
# 合并contours_full中的所有轮廓
merged_contour = np.concatenate(contours_full)
# 计算包围所有轮廓的大边界框
x, y, w, h = cv2.boundingRect(merged_contour)
# 在原图中截取该区域
cropped_area = matched_region[y:y+h, x:x+w]

merged_contour1 = np.concatenate(contours_partial)
# 计算包围所有轮廓的大边界框
x1, y1, w1, h1 = cv2.boundingRect(merged_contour1)
# 在原图中截取该区域
cropped_area1 = partial_image[y1:y1+h1, x1:x1+w1]
cv2.rectangle(image_with_boxes, (x, y), (x + w, y + h), (0, 255, 0), 2)
cv2.imshow("image_with_boxes", image_with_boxes)
cropped_area1 = cv2.resize(cropped_area1, (cropped_area.shape[1], cropped_area.shape[0]))

cv2.rectangle(image_with_boxes1, (x1, y1), (x1 + w1, y1 + h1), (0, 255, 0), 2)
cv2.imshow("image_with_boxes1", image_with_boxes1)
# 显示截取的区域
cv2.imshow("Cropped Area", cropped_area)
cv2.imshow("Cropped Area1", cropped_area1)
# 显示二值化图像
cv2.imshow("Partial Image Binary", partial_image_binary)
cv2.imshow("Full Image Binary", full_image_binary)

# 显示带有矩形的图像
cv2.imshow("Partial Image with Rectangle", partial_image)
cv2.imshow("Full Image with Rectangle", matched_region)


cv2.waitKey(0)
cv2.destroyAllWindows()
