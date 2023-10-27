import cv2
import numpy as np

def match_and_extract_region(partial_image_path, full_image_path):
    # 读取完整图片和局部图片
    full_image = cv2.imread(full_image_path)
    partial_image = cv2.imread(partial_image_path)

    if full_image is None or partial_image is None:
        raise ValueError("Failed to load one or both images.")

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

    # 根据Lowe's ratio test筛选匹配
    good_matches = []
    for m, n in matches:
        if m.distance < 0.8 * n.distance:
            good_matches.append(m)
    matched_image = cv2.drawMatches(full_image, kp1, partial_image, kp2, good_matches, None,
                                    flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

    # 显示匹配结果
    cv2.namedWindow("Good Matches", cv2.WINDOW_NORMAL)
    cv2.imshow("Good Matches", matched_image)
    if len(good_matches) < 4:
        raise ValueError("Not enough good matches for transformation.")

    # 获取局部图片和完整图片中的对应点
    partial_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    full_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    # 计算透视变换矩阵
    M = cv2.getPerspectiveTransform(partial_pts, full_pts)

    # 应用透视变换来截取匹配区域
    h, w = partial_image.shape[:2]
    matched_region = cv2.warpPerspective(full_image, M, (w, h))

    return matched_region


# 调用函数并获取匹配区域
matched_region = match_and_extract_region('cut_7copy.jpg', 'demo4.jpg')

if matched_region is not None:
    # 显示匹配区域
    cv2.imshow("Matched Region", matched_region)
    cv2.imwrite("matched_region.jpg", matched_region)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print("Matching and extraction failed.")
