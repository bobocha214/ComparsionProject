import cv2
import numpy as np


def compare_images(imageA_path, imageB_path, threshold=30):
    # 读取两张图片
    image1 = cv2.imread(imageA_path)
    image2 = cv2.imread(imageB_path)

    # 确保两张图片具有相同的尺寸
    if image1.shape != image2.shape:
        image1 = cv2.resize(image1, (image2.shape[1], image2.shape[0]))

    # 将两张图片转换为灰度图像
    gray_image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray_image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    # 比较两张灰度图像的每个像素，找出不同之处
    difference = cv2.absdiff(gray_image1, gray_image2)

    # 根据阈值创建二值图像
    _, thresholded_difference = cv2.threshold(difference, threshold, 255, cv2.THRESH_BINARY)

    # 计算白色像素数量
    white_pixel_count = np.sum(thresholded_difference == 255)
    image_area = gray_image1.shape[0] * gray_image1.shape[1]

    if white_pixel_count < 10:
        weighted_white_pixel_count = white_pixel_count
    else:
        white_pixel_weight = 1
        weighted_white_pixel_count = white_pixel_count * white_pixel_weight

    # 获取整张图片的像素数量
    total_pixel_count = thresholded_difference.size

    # 计算加权后的比例
    weighted_white_to_black_ratio = 1 - weighted_white_pixel_count / total_pixel_count

    # 查找轮廓
    contours, _ = cv2.findContours(thresholded_difference, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 在一张新的图像上绘制圆圈以标记不同之处
    marked_image = image2.copy()
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(marked_image, (x, y), (x + w, y + h), (0, 255, 0), 2)  # 使用红色绘制方框

    return {
        "white_pixel_count": white_pixel_count,
        "weighted_white_pixel_count": weighted_white_pixel_count,
        "weighted_white_to_black_ratio": weighted_white_to_black_ratio,
        "marked_image": marked_image
    }


# 调用示例
imageA = 'cut1/cut_5.jpg'
imageB = 'cuts/cut_6.jpg'
result = compare_images(imageA, imageB, threshold=30)
# 保存标记了不同之处的图片
cv2.imwrite('marked_difference.jpg', result["marked_image"])
print(result["weighted_white_to_black_ratio"])

# import cv2
# import numpy as np
#
# imageA = 'image/NEW/cut_save1.jpg'
# imageB = 'image/NEW/cut_save3.jpg'
#
#
# def compare_images(imageA, imageB):
#     # 读取两张图片
#     image1 = cv2.imread(imageA)
#     image2 = cv2.imread(imageB)
#
#     # 确保两张图片具有相同的尺寸
#     if image1.shape != image2.shape:
#         image1 = cv2.resize(image1, (image2.shape[1], image2.shape[0]))
#
#     # 将两张图片转换为灰度图像
#     gray_image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
#     gray_image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
#
#     # 比较两张灰度图像的每个像素，找出不同之处
#     difference = cv2.absdiff(gray_image1, gray_image2)
#     print(difference.size)
#     cv2.namedWindow('difference', cv2.WINDOW_NORMAL)
#     cv2.imshow('difference', difference)
#     cv2.waitKey(0)
#
#     # 根据阈值创建二值图像
#     _, thresholded_difference = cv2.threshold(difference, 30, 255, cv2.THRESH_BINARY)
#     cv2.namedWindow('thresholded_difference', cv2.WINDOW_NORMAL)
#     cv2.imshow('thresholded_difference', thresholded_difference)
#     cv2.waitKey(0)
#
#     # 计算白色像素数量
#     white_pixel_count = np.sum(thresholded_difference == 255)
#     print(white_pixel_count)
#     image_area = gray_image1.shape[0] * gray_image1.shape[1]
#     print(image_area)
#     if white_pixel_count < 10:
#         # 设置白色像素和黑色像素的权重
#         print('没有错误')
#         weighted_white_pixel_count = white_pixel_count
#     else:
#         white_pixel_weight = 1
#         # 计算加权后的像素数量
#         weighted_white_pixel_count = white_pixel_count * white_pixel_weight
#
#     # 获取整张图片的像素数量
#     total_pixel_count = thresholded_difference.size
#
#     # 计算加权后的比例
#     weighted_white_to_black_ratio = 1 - weighted_white_pixel_count / total_pixel_count
#
#     print(f"白色像素数量: {white_pixel_count}")
#     print(f"加权后的白色像素数量: {weighted_white_pixel_count}")
#     print(f"加权后的白色像素与整图的比例: {weighted_white_to_black_ratio:.4f}")
#
#     # 查找轮廓
#     contours, _ = cv2.findContours(thresholded_difference, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#
#     # 在一张新的图像上绘制圆圈以标记不同之处
#     marked_image = image2.copy()
#     for contour in contours:
#         x, y, w, h = cv2.boundingRect(contour)
#         cv2.rectangle(marked_image, (x, y), (x + w, y + h), (0, 255, 0), 2)  # 使用红色绘制方框
#
#     # 保存标记了不同之处的图片
#     cv2.imwrite('marked_difference.jpg', marked_image)
#
#
# compare_images(imageA, imageB)
