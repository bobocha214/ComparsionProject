import cv2
import numpy as np

def match_and_extract_region(partial_image_path, full_image_path):
    # 读取完整图片和局部图片
    full_image = cv2.imread(full_image_path)
    partial_image = cv2.imread(partial_image_path)
    gray_full_image = cv2.cvtColor(full_image, cv2.COLOR_BGR2GRAY)
    gray_partial_image = cv2.cvtColor(partial_image, cv2.COLOR_BGR2GRAY)
    # 使用SIFT特征检测和匹配
    sift = cv2.SIFT_create()
    kp1, des1 = sift.detectAndCompute(gray_partial_image, None)
    kp2, des2 = sift.detectAndCompute(gray_full_image, None)

    # 使用FLANN匹配器进行特征匹配
    FLANN_INDEX_KDTREE = 0
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)
    flann = cv2.FlannBasedMatcher(index_params, search_params)
    matches = flann.knnMatch(des1, des2, k=2)

    # # 创建BFMatcher（暴力匹配器）对象
    # bf = cv2.BFMatcher()
    #
    # # 使用KNN匹配
    # matches = bf.knnMatch(des1, des2, k=2)

    good_matches = []
    for m, n in matches:
        if m.distance < 0.8 * n.distance:
            good_matches.append(m)
    matched_image = cv2.drawMatches(full_image, kp1, partial_image, kp2, good_matches, None,
                                    flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

    # 显示匹配结果
    cv2.namedWindow("Good Matches", cv2.WINDOW_NORMAL)
    cv2.imshow("Good Matches", matched_image)
    # 获取局部图片和完整图片中的对应点
    partial_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    full_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    # 计算单映射变换矩阵H
    H, _ = cv2.findHomography(partial_pts, full_pts, cv2.RANSAC, 5.0)

    # 使用透视变换来截取匹配区域
    h, w = partial_image.shape[:2]
    corners = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
    transformed_corners = cv2.perspectiveTransform(corners, H)

    # 计算匹配区域的尺寸
    min_x = np.min(transformed_corners[:, :, 0])
    max_x = np.max(transformed_corners[:, :, 0])
    min_y = np.min(transformed_corners[:, :, 1])
    max_y = np.max(transformed_corners[:, :, 1])
    # 裁剪匹配区域
    matched_region = full_image[int(min_y):int(max_y), int(min_x):int(max_x)]
    cv2.imshow("Matched Region0", matched_region)
    cv2.imshow("partial_image", partial_image)


    # 计算旋转角度
    angle = np.degrees(np.arctan2(H[0, 1], H[0, 0]))
    print(angle)


    if abs(angle) < 10:
        center = (partial_image.shape[1] // 2, partial_image.shape[0] // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        partial_image = cv2.warpAffine(partial_image, rotation_matrix,
                                        (matched_region.shape[1], matched_region.shape[0]),
                                        borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    cv2.imshow("partial_image", partial_image)
    cv2.imwrite("cuttest/cut_0or.jpg", partial_image)

    return matched_region


# 调用函数并获取匹配区域和差异图像
matched_region = match_and_extract_region('cuttest/cut_0.jpg', 'cuttest/demo2.jpg')
# 显示匹配区域和差异图像
cv2.imshow("Matched Region", matched_region)
cv2.imwrite("cuttest/matched_region.jpg", matched_region)
cv2.waitKey(0)
cv2.destroyAllWindows()
