import cv2
import numpy as np

# 读取两张图片
image1 = cv2.imread("image11.jpg", cv2.IMREAD_COLOR)
image2 = cv2.imread("image22.jpg", cv2.IMREAD_COLOR)

# 转换为灰度图像
gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

# 使用边缘检测来识别图案
edges1 = cv2.Canny(gray1, 50, 150)
edges2 = cv2.Canny(gray2, 50, 150)

# 寻找图案的轮廓
contours1, _ = cv2.findContours(edges1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
contours2, _ = cv2.findContours(edges2, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 找到包含所有矩形的最小外接矩形
rect1 = cv2.minAreaRect(np.concatenate(contours1))
rect2 = cv2.minAreaRect(np.concatenate(contours2))

# 提取旋转角度
angle1 = rect1[2]
angle2 = rect2[2]

# 计算需要旋转的角度差异
angle_diff = angle1 - angle2

# 旋转第一个图案的最小外接矩形
if abs(angle_diff) <15:
    # 顺时针旋转矩形，注意角度需要转换为弧度
    rotated_image1 = cv2.warpAffine(image1, cv2.getRotationMatrix2D((0,0), angle_diff, 1.0), (image2.shape[1], image2.shape[0]))
    rotated_image2 = cv2.warpAffine(image2, cv2.getRotationMatrix2D((0,0), 0, 1.0), (image2.shape[1], image2.shape[0]))
else:
    # 逆时针旋转矩形，注意角度需要转换为弧度
    rotated_image1 = cv2.warpAffine(image1, cv2.getRotationMatrix2D(rect1[0], 360 + angle_diff, 1.0),
                                    (image1.shape[1], image1.shape[0]))



# 现在，rotated_image1 包含了旋转后的最小外接矩形，而 image2 保持不变

# 可以继续处理或比较这两个图案

cv2.imshow("rotated_image1", rotated_image1)
cv2.imshow("image2", rotated_image2)
cv2.waitKey(0)

# 现在 image1 和 image2 的图案应该角度对齐

# 可以继续处理或比较这两个图案

# def find_and_transform_region_affine(template_path, image_path):
#     # 读取模板图片和大图
#     template = cv2.imread(template_path, 0)
#     image = cv2.imread(image_path, 0)
#
#     # 使用特征匹配
#     sift = cv2.SIFT_create()
#     kp1, des1 = sift.detectAndCompute(template, None)
#     kp2, des2 = sift.detectAndCompute(image, None)
#     bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
#     matches = bf.match(des1, des2)
#     matches = sorted(matches, key=lambda x: x.distance)
#
#     # 获取匹配点
#     src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
#     dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
#
#     # 计算仿射变换矩阵
#     M = cv2.estimateAffine2D(src_pts, dst_pts)[0]
#
#     # 使用仿射变换
#     h, w = template.shape
#     result = cv2.warpAffine(image, M, (w, h))
#
#     return result
#
# # 调用函数并获取匹配区域
# matched_region_affine = find_and_transform_region_affine('cut_7copy.jpg', 'demo4.jpg')
#
# # 显示匹配区域
# cv2.imshow("Matched Region (Affine)", matched_region_affine)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
