import os
from functools import partial

import cv2
import numpy as np
from PIL import Image, ImageTk
from multiprocessing import Pool

def process_and_display_difference_images(partial_image, matched_region, threshold=130):

    partial_image = cv2.resize(partial_image, (matched_region.shape[1], matched_region.shape[0]))
    cv2.imshow("matched_region11", matched_region)
    cv2.imshow("partial_image11", partial_image)
    gray_matched_region = cv2.cvtColor(matched_region, cv2.COLOR_BGR2GRAY)
    _, binary_matched_region = cv2.threshold(gray_matched_region, 200, 255, cv2.THRESH_BINARY_INV)
    cv2.imshow("binary_matched_region", binary_matched_region)
    # 计算两图像的差异
    difference = cv2.absdiff(matched_region, partial_image)
    cv2.imshow("difference", difference)
    # 转换差异图像为灰度
    gray_difference = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)

    try:
        # 二值化差异图像
        _, binary_difference = cv2.threshold(gray_difference, threshold, 255, cv2.THRESH_BINARY)
        cv2.imshow("binary_difference", binary_difference)
        cv2.waitKey(0)
        white_pixel_count = np.sum(binary_difference == 255)
        print(white_pixel_count, 'white_pixel_count', 'all_pixel_count')
        # 寻找差异区域的轮廓
        # 寻找差异区域的轮廓
        contours, _ = cv2.findContours(binary_difference, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 对轮廓进行排序，按照轮廓的 x 坐标进行排序
        contours = sorted(contours, key=lambda x: cv2.boundingRect(x)[0])

        # 创建一个空列表，用于存储合并后的轮廓
        merged_contours = []

        # 初始化一个空轮廓，用于存储当前合并的轮廓
        current_contour = None

        # 合并相邻的轮廓
        for contour in contours:
            if current_contour is None:
                current_contour = contour
            else:
                # 获取当前轮廓的边界框
                x1, y1, w1, h1 = cv2.boundingRect(current_contour)

                # 获取下一个轮廓的边界框
                x2, y2, w2, h2 = cv2.boundingRect(contour)

                # 判断两个边界框是否相邻
                if x2 - (x1 + w1) < threshold:  # 这里的 threshold 是相邻的阈值，可以根据需要调整
                    # 如果相邻，则合并两个轮廓
                    current_contour = np.concatenate((current_contour, contour))
                else:
                    # 如果不相邻，则将当前轮廓添加到合并列表中，并更新当前轮廓为下一个轮廓
                    merged_contours.append(current_contour)
                    current_contour = contour

        # 将最后一个轮廓添加到合并列表中
        if current_contour is not None:
            merged_contours.append(current_contour)

        # 在matched_region上绘制合并后的边界框
        result = matched_region.copy()
        for contour in merged_contours:
            area = cv2.contourArea(contour)
            print(area, 'area')  # and percent > 0.15
            x, y, w, h = cv2.boundingRect(contour)
            # 绘制方框
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 1)
        return result
    except:
        pass


def process_and_insert_cropped_region(image1, image2):
    def extract_rotated_rect(image):
        cv2.imshow("image", image)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred_image = cv2.GaussianBlur(gray, (5, 5), 0)
        cv2.imshow("blurred_image", blurred_image)
        cv2.waitKey(0)
        _, binary_image = cv2.threshold(blurred_image, 200, 255, cv2.THRESH_BINARY_INV)
        cv2.imshow("binary_image", binary_image)
        cv2.waitKey(0)
        # kernel = np.ones((3, 3), np.uint8)
        # opening = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel)
        # cv2.imshow("opening", opening)
        # cv2.waitKey(0)
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        imagegray=image.copy()
        for contour in contours:
            area=cv2.minAreaRect(contour)
            print(area)
            x,y,w,h = cv2.boundingRect(contour)
            cv2.rectangle(imagegray, (x, y), (x + w, y + h), (0, 255, 0),2)
        cv2.imshow("imagegray", imagegray)
        cv2.waitKey(0)
        print(contours)
        merged_contour = np.concatenate(contours)
        rect = cv2.minAreaRect(merged_contour)
        angle = rect[2]
        return rect, merged_contour

    def rotate_image(image, angle, rect):
        center_x, center_y = image.shape[1] // 2, image.shape[0] // 2
        rotation_matrix = cv2.getRotationMatrix2D(rect, angle, 1)
        rotated_image = cv2.warpAffine(image, rotation_matrix, (image.shape[1], image.shape[0]),
                                       borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
        return rotated_image
    rect1, merged_contour1 = extract_rotated_rect(image1)
    rect2, merged_contour2 = extract_rotated_rect(image2)
    box1 = cv2.boxPoints(cv2.minAreaRect(merged_contour1))
    box2 = cv2.boxPoints(cv2.minAreaRect(merged_contour2))
    box1 = np.int0(box1)
    box2 = np.int0(box2)
    angle1 = rect1[2]
    angle2 = rect2[2]
    print(angle1, angle2)
    if (angle1 > 45):
        angle1 = angle1 - 90
    if (angle2 > 45):
        angle2 = angle2 - 90
    print(angle1, angle2)
    angle_diff = angle1 - angle2

    # 旋转其中一个图案以与另一个对齐
    if abs(angle_diff) < 45:
        center_x, center_y = image1.shape[1] // 2, image1.shape[0] // 2
        # 顺时针旋转 image1，注意角度需要转换为弧度
        rotated_image1 = cv2.warpAffine(image1, cv2.getRotationMatrix2D((center_x, center_y), angle_diff, 1.0),
                                        (image2.shape[1], image2.shape[0]),borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    else:
        # 逆时针旋转 image1，注意角度需要转换为弧度
        rotated_image1 = cv2.warpAffine(image1, cv2.getRotationMatrix2D(rect1[0], 360 + angle_diff, 1.0),
                                        (image2.shape[1], image2.shape[0]),borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))

    cv2.imshow("rotated_image1", rotated_image1)
    cv2.imshow("image2", image2)
    cv2.waitKey(0)

    mask1 = np.ones_like(image1) * 255
    mask2 = np.ones_like(image2) * 255
    cv2.fillPoly(mask1, [box1], (255, 255, 255))
    cv2.fillPoly(mask2, [box2], (255, 255, 255))
    result1 = cv2.bitwise_and(image1, mask1)
    result2 = cv2.bitwise_and(image2, mask2)
    cv2.imshow("result1", result1)
    cv2.imshow("result2", result2)
    cv2.waitKey(0)

    x1, y1, w1, h1 = cv2.boundingRect(box1)
    x2, y2, w2, h2 = cv2.boundingRect(box2)

    try:
        image3 = result1[y1:y1 + h1, x1:x1 + w1]
        image4 = result2[y2:y2 + h2, x2:x2 + w2]
    except:
        image3 = result1
        image4 = result2
    # cv2.imshow('image3', image3)
    # cv2.imshow('image4', image4)
    # cv2.waitKey(0)
    angle1 = rect1[2]
    angle2 = rect2[2]
    print(angle1, angle2)
    if (angle1 > 45):
        angle1 = angle1 - 90
    if (angle2 > 45):
        angle2 = angle2 - 90
    print(angle1, angle2)
    #
    if abs(angle1) < 15:
        # print(angle1 - angle2)
        # print('1111')
        image3 = rotate_image(image3, angle1, rect1[0])
    else:
        x2, y2, w2, h2 = cv2.boundingRect(merged_contour2)
        image3 = image1[y1:y1 + h1, x1:x1 + w1]
    if abs(angle2) < 15:
        image4 = rotate_image(image4, angle2, rect2[0])
    else:
        x2, y2, w2, h2 = cv2.boundingRect(merged_contour2)
        image4 = image2[y2:y2 + h2, x2:x2 + w2]

    gray3 = cv2.cvtColor(image3, cv2.COLOR_BGR2GRAY)
    gray4 = cv2.cvtColor(image4, cv2.COLOR_BGR2GRAY)
    _, binary_image3 = cv2.threshold(gray3, 200, 255, cv2.THRESH_BINARY_INV)
    _, binary_image4 = cv2.threshold(gray4, 200, 255, cv2.THRESH_BINARY_INV)
    cv2.imshow('binary_image3', binary_image3)
    cv2.imshow('binary_image4', binary_image4)
    cv2.waitKey(0)
    contours3, _ = cv2.findContours(binary_image3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours4, _ = cv2.findContours(binary_image4, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    merged_contour3 = np.concatenate(contours3)
    merged_contour4 = np.concatenate(contours4)

    x3, y3, w3, h3 = cv2.boundingRect(merged_contour3)
    x4, y4, w4, h4 = cv2.boundingRect(merged_contour4)

    image5 = image3.copy()
    image6 = image4.copy()

    cv2.rectangle(image5, (x3, y3), (x3 + w3, y3 + h3), (0, 255, 0), 1)
    cv2.rectangle(image6, (x4, y4), (x4 + w4, y4 + h4), (0, 255, 0), 1)

    roi1 = image3[y3:y3 + h3, x3:x3 + w3]
    roi2 = image4[y4:y4 + h4, x4:x4 + w4]

    roi1 = cv2.resize(roi1, (roi2.shape[1], roi2.shape[0]))

    # cv2.imwrite('cuttest/roi1', roi1)
    # cv2.imwrite('cuttest/roi2', roi2)
    # cv2.waitKey(0)
    image7 =process_and_display_difference_images(roi1, roi2)
    # cv2.imshow('image7', image7)
    image4[y4:y4 + h4, x4:x4 + w4] = image7
    # cv2.imshow('image4', image4)
    # image8=rotate_image(image4, -angle2,rect2[0])
    result2[y2:y2 + h2, x2:x2 + w2] = image4
    # cv2.imshow('result2', result2)
    return result2



def match_and_extract_region(partial_image, full_image):
    # 读取完整图片和局部图片
    full_image = cv2.imread('demo40.jpg')
    partial_image = cv2.imread('cut_8.jpg')
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

    # 创建BFMatcher（暴力匹配器）对象
    # bf = cv2.BFMatcher()
    #
    # # 使用KNN匹配
    # matches = bf.knnMatch(des1, des2, k=2)

    good_matches = []
    for m, n in matches:
        if m.distance < 0.5 * n.distance:
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
    H, _ = cv2.findHomography(partial_pts, full_pts, cv2.RANSAC, 100.0)

    # 使用透视变换来截取匹配区域
    h, w = partial_image.shape[:2]
    corners = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
    transformed_corners = cv2.perspectiveTransform(corners, H)

    # 计算匹配区域的尺寸
    min_x = np.min(transformed_corners[:, :, 0])
    max_x = np.max(transformed_corners[:, :, 0])
    min_y = np.min(transformed_corners[:, :, 1])
    max_y = np.max(transformed_corners[:, :, 1])
    min_x = np.clip(min_x, 0, None)
    max_x = np.clip(max_x, 0, None)
    min_y = np.clip(min_y, 0, None)
    max_y = np.clip(max_y, 0, None)
    # 裁剪匹配区域
    matched_region = full_image[int(min_y):int(max_y), int(min_x):int(max_x)]
    cv2.imshow("Matched Region0", matched_region)
    cv2.imshow("partial_image0", partial_image)
    cv2.imwrite("partial_image0.jpg", partial_image)
    cv2.imwrite("matched_image0.jpg", matched_region)
    cv2.waitKey(0)

    # # 计算旋转角度
    # angle = np.degrees(np.arctan2(H[0, 1], H[0, 0]))
    # print(angle)
    # # 确定旋转方向
    # if angle < 0:
    #     angle += 360  # 将负角度转为正值
    # if abs(angle) < 10:
    #     center = (partial_image.shape[1] // 2, partial_image.shape[0] // 2)
    #     rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    #     partial_image = cv2.warpAffine(partial_image, rotation_matrix,
    #                                    (matched_region.shape[1], matched_region.shape[0]),
    #                                    borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))




    cv2.waitKey(0)
    image7 = process_and_insert_cropped_region(partial_image, matched_region)
    # cv2.imshow("image7", image7)
    full_image[int(min_y):int(max_y), int(min_x):int(max_x)] = image7
    cv2.imshow("full_image", full_image)
    cv2.imwrite('marked_difference.jpg', full_image)

    return full_image

folder_path = '../cuts'
image_list=[]
def read_all_img():
    for filename1 in os.listdir(folder_path):
        if filename1.endswith(('.jpg', '.jpeg', '.png')):  # 确保文件是图片文件
            filepath1 = os.path.join(folder_path, filename1)
            image = cv2.imread(filepath1)
            image_list.append(image)


if __name__ == '__main__':
    # 在主模块中执行的代码
    pool = Pool()
    folder_path = '../cuts'
    image_list = []

    def read_all_img():
        for filename1 in os.listdir(folder_path):
            if filename1.endswith(('.jpg', '.jpeg', '.png')):
                filepath1 = os.path.join(folder_path, filename1)
                image = cv2.imread(filepath1)
                image_list.append(image)


    # 使用进程池并行执行匹配和粘贴操作

    input_image_path1 = 'cut_0.jpg'  # 请将路径替换为实际路径
    input_image_path2 = 'demo15.jpg'  # 请将路径替换为实际路径
    partial_image = cv2.imread('cut_0.jpg')


    full_image = match_and_extract_region(input_image_path1, partial_image)
    cv2.imshow("full_image", full_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

