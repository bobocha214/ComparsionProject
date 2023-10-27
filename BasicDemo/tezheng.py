import cv2

# 读取目标图像和待匹配图像
target_image = cv2.imread('cuts/cut_0.jpg', 0)
query_image = cv2.imread('cuts/cut_0.jpg', 0)

# 初始化特征检测器（这里使用SIFT）
sift = cv2.SIFT_create()

# 在目标图像和待匹配图像上检测关键点和描述符
keypoints1, descriptors1 = sift.detectAndCompute(target_image, None)
keypoints2, descriptors2 = sift.detectAndCompute(query_image, None)

# 初始化暴力匹配器
bf = cv2.BFMatcher()

# 使用KNN算法进行特征匹配
matches = bf.knnMatch(descriptors1, descriptors2, k=2)

# 应用比率测试来筛选好的匹配点
good_matches = []
for m, n in matches:
    if m.distance < 0.75 * n.distance:
        good_matches.append(m)

# 画出匹配结果
matched_image = cv2.drawMatches(target_image, keypoints1, query_image, keypoints2, good_matches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

# 显示匹配结果
cv2.imshow('Matched Image', matched_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
