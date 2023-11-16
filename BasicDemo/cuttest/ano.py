import multiprocessing
import os
import threading
import time
from math import fabs, sin, cos, radians
from concurrent.futures import ThreadPoolExecutor
import functools
import cv2
import numpy as np
from PIL import Image, ImageTk
from multiprocessing import Pool,Manager


def process_and_display_difference_images(partial_image, matched_region, threshold=155):
    global image_rectangle
    try:
        # 确保partial_image与matched_region具有相同的尺寸
        partial_image = cv2.resize(partial_image, (matched_region.shape[1], matched_region.shape[0]))
        gray_matched_region = cv2.cvtColor(matched_region, cv2.COLOR_BGR2GRAY)
        _, binary_matched_region = cv2.threshold(matched_region, 200, 255, cv2.THRESH_BINARY_INV)
        # cv2.imshow('binary_matched_region', binary_matched_region)
        # cv2.waitKey(0)
        all_pixel_count = np.sum(binary_matched_region == 255)
        # 计算两图像的差异
        difference = cv2.absdiff(matched_region, partial_image)

        # 转换差异图像为灰度
        gray_difference = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)
        # cv2.imshow('gray_difference', gray_difference)
        # cv2.waitKey(0)
        # 二值化差异图像
        _, binary_difference = cv2.threshold(gray_difference, threshold, 255, cv2.THRESH_BINARY)
        # cv2.imshow('binary_difference', binary_difference)
        # cv2.waitKey(0)
        white_pixel_count = np.sum(binary_difference == 255)
        # percent = (white_pixel_count * weight_threshold_NUM) / all_pixel_count
        # print(white_pixel_count, 'white_pixel_count',compare_threshold_NUM,all_pixel_count,'all_pixel_count',percent)
        # 寻找差异区域的轮廓
        contours, _ = cv2.findContours(binary_difference, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 合并相邻的轮廓
        merged_contours = []
        current_contour = None
        for contour in contours:
            if current_contour is None:
                current_contour = contour
            else:
                # 获取当前轮廓的边界框
                x1, y1, w1, h1 = cv2.boundingRect(current_contour)
                # 获取下一个轮廓的边界框
                x2, y2, w2, h2 = cv2.boundingRect(contour)

                # 判断两个边界框是否相邻
                if x2 - (x1 + w1) < 20:  # 这里的 threshold 是相邻的阈值，可以根据需要调整
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
        # cv2.imshow('result', result)
        # cv2.waitKey(0)
        try:
            for contour in merged_contours:
                area = cv2.contourArea(contour)
                # print(area, 'area') #and percent > 0.15
                if area > 10:
                    image_rectangle = True
                    x, y, w, h = cv2.boundingRect(contour)
                    # 绘制方框
                    cv2.rectangle(result, (x, y), (x + w, y + h), (0, 0, 255), 2)
        except:
            result=result
        # cv2.imshow('result_bgr', result_bgr)
        # cv2.waitKey(0)
        return result
    except Exception as e:
        # print(f"An exception occurred: {str(e)}")
        # return None
        pass

def process_and_insert_cropped_region(image1, image2):
    # cv2.imshow('image1',image1)
    # cv2.imshow('image2',image2)
    def extract_rotated_rect(image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred_image = cv2.GaussianBlur(gray, (5, 5), 0)
        _, binary_image = cv2.threshold(blurred_image, 200, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        merged_contour = np.concatenate(contours)
        rect = cv2.minAreaRect(merged_contour)
        angle = rect[2]
        return rect, merged_contour

    def rotate_image(image, angle, rect2):
        center_x, center_y = image.shape[1] // 2, image.shape[0] // 2
        h, w = image.shape[:2]
        rotation_matrix = cv2.getRotationMatrix2D((center_x, center_y), angle, 1)
        new_H = int(w * fabs(sin(radians(angle))) + h * fabs(cos(radians(angle))))
        new_W = int(h * fabs(sin(radians(angle))) + w * fabs(cos(radians(angle))))
        # 2.3 平移
        rotation_matrix[0, 2] += (new_W - w) / 2
        rotation_matrix[1, 2] += (new_H - h) / 2
        rotated_image = cv2.warpAffine(image, rotation_matrix, (new_W, new_H),
                                       borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))

        return rotated_image

    rect1, merged_contour1 = extract_rotated_rect(image1)
    rect2, merged_contour2 = extract_rotated_rect(image2)

    box1 = cv2.boxPoints(cv2.minAreaRect(merged_contour1))
    box2 = cv2.boxPoints(cv2.minAreaRect(merged_contour2))

    mask1 = np.ones_like(image1) * 255
    mask2 = np.ones_like(image2) * 255

    cv2.fillPoly(mask1, [np.int0(box1)], (255, 255, 255))
    cv2.fillPoly(mask2, [np.int0(box2)], (255, 255, 255))

    result1 = cv2.bitwise_and(image1, mask1)
    result2 = cv2.bitwise_and(image2, mask2)





    angle1 = rect1[2]
    angle2 = rect2[2]
    # print(angle1, angle2)
    if (angle1 > 45):
        angle1 = angle1 - 90
    if (angle2 > 45):
        angle2 = angle2 - 90
    # print(angle1, angle2)
    if abs(angle1 - angle2) < 25:
        # print(angle1 - angle2)
        # print('1111')
        image3 = rotate_image(result1, angle1 - angle2, rect1[0])
    else:
        # print(angle1 - angle2)
        # print('2222')
        x1, y1, w1, h1 = cv2.boundingRect(merged_contour1)
        image3 = result1[y1:y1 + h1, x1:x1 + w1]
    # time.sleep(0.2)
    gray3 = cv2.cvtColor(image3, cv2.COLOR_BGR2GRAY)
    gray4 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
    _, binary_image3 = cv2.threshold(gray3, 200, 255, cv2.THRESH_BINARY_INV)
    _, binary_image4 = cv2.threshold(gray4, 200, 255, cv2.THRESH_BINARY_INV)
    # cv2.imshow('binary_image3', binary_image3)
    # cv2.imshow('binary_image4', binary_image4)
    contours3, _ = cv2.findContours(binary_image3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours4, _ = cv2.findContours(binary_image4, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    merged_contour3 = np.concatenate(contours3)
    merged_contour4 = np.concatenate(contours4)

    x3, y3, w3, h3 = cv2.boundingRect(merged_contour3)
    x4, y4, w4, h4 = cv2.boundingRect(merged_contour4)

    image5 = image3.copy()
    image6 = image2.copy()

    cv2.rectangle(image5, (x3, y3), (x3 + w3, y3 + h3), (0, 255, 0), 1)
    cv2.rectangle(image6, (x4, y4), (x4 + w4, y4 + h4), (0, 255, 0), 1)
    # cv2.imshow('image5', image5)
    # cv2.imshow('image6', image6)
    roi1 = image3[y3:y3 + h3, x3:x3 + w3]
    roi2 = image2[y4:y4 + h4, x4:x4 + w4]
    cv2.imshow('roi1', roi1)
    cv2.imshow('roi2', roi2)
    cv2.waitKey(0)
    roi1 = cv2.resize(roi1, (roi2.shape[1], roi2.shape[0]))

    # cv2.imwrite('cuttest/roi1', roi1)
    # cv2.imwrite('cuttest/roi2', roi2)
    # cv2.waitKey(0)
    # image7 = process_and_display_difference_images(roi1, roi2)
    # # cv2.imshow('image7', image7)
    # image4[y4:y4 + h4, x4:x4 + w4] = image7
    # # cv2.imshow('image4', image4)
    # result2[y2:y2 + h2, x2:x2 + w2] = image4
    # cv2.imshow('result2', result2)
    return roi1,roi2,image2,x4,y4,w4,h4

start = time.time()
def match_and_extract_region(partial_image, full_image):
    # partial_image = cv2.imread(partial_image)
    # image = cv2.imread(input_image_path)

    cv2.imshow('partial_image', partial_image)
    cv2.imshow("full_image", full_image)
    cv2.waitKey(0)
    # 转换图像为灰度
    gray_full_image = cv2.cvtColor(full_image, cv2.COLOR_BGR2GRAY)
    gray_partial_image = cv2.cvtColor(partial_image, cv2.COLOR_BGR2GRAY)

    # 使用SIFT特征检测和匹配
    sift = cv2.SIFT_create()
    kp1, des1 = sift.detectAndCompute(gray_partial_image, None)
    kp2, des2 = sift.detectAndCompute(gray_full_image, None)

    # # 使用FLANN匹配器进行特征匹配
    # FLANN_INDEX_KDTREE = 0
    # index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    # search_params = dict(checks=50)
    # flann = cv2.FlannBasedMatcher(index_params, search_params)
    # matches = flann.knnMatch(des1, des2, k=2)
    # 创建BFMatcher（暴力匹配器）对象
    bf = cv2.BFMatcher()

    # 使用KNN匹配
    matches = bf.knnMatch(des1, des2, k=2)
    # 选择良好的匹配项
    good_matches = [m for m, n in matches if m.distance < 0.9 * n.distance]

    # 绘制匹配结果
    # matched_image = cv2.drawMatches(full_image, kp1, partial_image, kp2, good_matches, None,
    #                                 flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)

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
    min_x = np.clip(min_x, 0, None)
    max_x = np.clip(max_x, 0, None)
    min_y = np.clip(min_y, 0, None)
    max_y = np.clip(max_y, 0, None)
    # 裁剪匹配区域
    matched_region = full_image[int(min_y):int(max_y), int(min_x):int(max_x)]

    # 调用函数处理和插入裁剪区域
    # image7 = process_and_insert_cropped_region(partial_image, matched_region)
    # # with image_lock:
    # # 将处理后的区域放回原始图像
    # full_image[int(min_y):int(max_y), int(min_x):int(max_x)] = image7
    # 保存结果图像
    # cv2.imwrite(full_image_path, full_image)
    # cv2.imshow('full_image_path', full_image)
    # cv2.waitKey(0)
    return matched_region,int(min_y),int(max_y),int(min_x),int(max_x)

def process_image(image, template_image, results_to_match):
    global start
    cv2.imshow('image', image)
    # cv2.imshow('images_to_match', images_to_match)
    # cv2.imshow('template_image', template_image)
    cv2.waitKey(0)
    # template_image=cv2.imread('demo17.jpg')
    # image, template_image, index, template_images_list = args
    matched_region, min_y, max_y, min_x, max_x = match_and_extract_region(images_to_match, template_image)
    # print(matched_region.shape[1],matched_region.shape[0], min_y, max_y, min_x, max_x )
    cv2.imshow('matched_region',matched_region)
    cv2.waitKey(0)
    roi1, roi2, image4, x4, y4, w4, h4 = process_and_insert_cropped_region(images_to_match, matched_region)
    result = process_and_display_difference_images(roi1, roi2)
    image4[y4:y4 + h4, x4:x4 + w4] = result
    image_info = (image4, min_y, max_y, min_x, max_x)
    results_to_match.append(image_info)
    # end = time.time()
    # print('process_image time: %s Seconds' % (end - start))
    # return image_info

if __name__ == '__main__':

    template_image = cv2.imread('demo30.jpg')
    images_to_match = []
    results_to_match = []
    for i in range(0, 8):
       image = cv2.imread(f'cut_{i}.jpg')
       images_to_match.append(image)
    # 创建线程
    threads = []
    num_threads = len(images_to_match)
    # manager = Manager()
    # result_list = manager.list()  # 创建共享列表
    # partial_func = functools.partial(process_image, template_image)
    # num_cores = multiprocessing.cpu_count()
    # print("可用的CPU核心数：", num_cores)
    # pool = Pool()
    # for result in pool.map(partial_func, images_to_match):
    #     result_list.append(result)  #s 将处理结果添加到共享列表中
    #
    # pool.close()
    # pool.join()
    for image in images_to_match:
        thread = threading.Thread(target=process_image, args=(image, template_image, results_to_match))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    print(len(results_to_match))

    for image_info in results_to_match:
        image4, min_y, max_y, min_x, max_x = image_info
        template_image[min_y:max_y, min_x:max_x] = image4
    cv2.imshow('template_image',template_image)
    cv2.imwrite('result_template_image.jpg',template_image)
    cv2.waitKey(0)
    end = time.time()
    print('thread_pool time: %s Seconds' % (end - start))