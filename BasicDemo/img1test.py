import cv2
import numpy as np

# 读取两张图像
image1 = cv2.imread('cuts/cut_1.jpg', 0)
image2 = cv2.imread('cuttest/cut_3.jpg', 0)

# 使用SIFT特征检测器
sift = cv2.SIFT_create()

# 计算特征点和描述子
kp1, des1 = sift.detectAndCompute(image1, None)  # 计算第一张图像的SIFT特征点和描述子
kp2, des2 = sift.detectAndCompute(image2, None)  # 计算第二张图像的SIFT特征点和描述子

# 使用BFMatcher暴力匹配
bf = cv2.BFMatcher()

# 特征匹配
matches = bf.knnMatch(des1, des2, k=2)

# 应用比率测试来筛选好的匹配点
good_matches = []
for m, n in matches:
    if m.distance < 0.75 * n.distance:
        good_matches.append(m)

# 计算图像配准变换
src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

# 应用变换将图像对齐
aligned_image = cv2.warpPerspective(image2, M, (image1.shape[1], image1.shape[0]))
cv2.imshow("aligned_image", aligned_image)
cv2.waitKey(0)
# 检测残缺的区域
difference_image = cv2.absdiff(image1, aligned_image)
cv2.imshow("difference_image", difference_image)
cv2.waitKey(0)
# 设置阈值以筛选出差异区域
threshold = 30  # 调整阈值以适应你的图像
ret, thresholded_image = cv2.threshold(difference_image, threshold, 255, cv2.THRESH_BINARY)

# 寻找差异区域的轮廓
contours, _ = cv2.findContours(thresholded_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 在原始图像上绘制残缺部分的框
for contour in contours:
    x, y, w, h = cv2.boundingRect(contour)
    cv2.rectangle(image1, (x, y), (x + w, y + h), (0, 255, 0), 2)

# 显示结果
cv2.imshow("Result", image1)
cv2.waitKey(0)
cv2.destroyAllWindows()
