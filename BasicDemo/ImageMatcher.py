from math import sin, radians, cos

import cv2
import numpy as np
import time
import logging

class ImageMatcher:

    def process_all_image(self, template_image, image):
        start = time.time()
        matched_region, min_y, max_y, min_x, max_x = self.match_and_extract_region(image, template_image)
        roi1, roi2, image4, x4, y4, w4, h4 = self.process_and_insert_cropped_region(image, matched_region)
        result = self.process_and_display_difference_images(roi1, roi2)
        image4[y4:y4 + h4, x4:x4 + w4] = result
        image_info = (image4, min_y, max_y, min_x, max_x)
        end1 = time.time()
        print('process_all_image: %s Seconds' % (end1 - start))
        return image_info

    def match_and_extract_region(self, partial_image, full_image):
        start = time.time()
        gray_full_image = cv2.cvtColor(full_image, cv2.COLOR_BGR2GRAY)
        gray_partial_image = cv2.cvtColor(partial_image, cv2.COLOR_BGR2GRAY)

        sift = cv2.SIFT_create()
        kp1, des1 = sift.detectAndCompute(gray_partial_image, None)
        kp2, des2 = sift.detectAndCompute(gray_full_image, None)

        FLANN_INDEX_KDTREE = 0
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        matches = flann.knnMatch(des1, des2, k=2)

        good_matches = [m for m, n in matches if m.distance < 0.85 * n.distance]

        partial_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        full_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        H, _ = cv2.findHomography(partial_pts, full_pts, cv2.RANSAC, 5.0)

        h, w = partial_image.shape[:2]
        corners = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
        transformed_corners = cv2.perspectiveTransform(corners, H)

        min_x = np.min(transformed_corners[:, :, 0])
        max_x = np.max(transformed_corners[:, :, 0])
        min_y = np.min(transformed_corners[:, :, 1])
        max_y = np.max(transformed_corners[:, :, 1])

        matched_region = full_image[int(min_y):int(max_y), int(min_x):int(max_x)]
        end1 = time.time()
        print('match_and_extract_region: %s Seconds' % (end1 - start))
        return matched_region, int(min_y), int(max_y), int(min_x), int(max_x)



    def process_and_insert_cropped_region(self, image1, image2, process_threshold_NUM):
        def extract_rotated_rect(image):
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred_image = cv2.GaussianBlur(gray, (5, 5), 0)
            _, binary_image = cv2.threshold(blurred_image, process_threshold_NUM, 255, cv2.THRESH_BINARY_INV)
            kernel = np.ones((3, 3), np.uint8)
            opening = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel)
            contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            merged_contour = np.concatenate(contours)
            rect = cv2.minAreaRect(merged_contour)
            angle = rect[2]
            return rect, merged_contour

        def rotate_image(image, angle, rect2):
            center_x, center_y = image.shape[1] // 2, image.shape[0] // 2
            h, w = image.shape[:2]
            rotation_matrix = cv2.getRotationMatrix2D(rect2, angle, 1)
            new_H = int(w * abs(sin(radians(angle))) + h * abs(cos(radians(angle))))
            new_W = int(h * abs(sin(radians(angle))) + w * abs(cos(radians(angle))))
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

        image3 = result1
        image4 = result2

        angle1 = rect1[2]
        angle2 = rect2[2]

        if angle1 > 45:
            angle1 = angle1 - 90
        if angle2 > 45:
            angle2 = angle2 - 90

        if abs(angle1 - angle2) < 25:
            image3 = rotate_image(image3, angle1 - angle2, rect1[0])
        else:
            x1, y1, w1, h1 = cv2.boundingRect(merged_contour1)
        image3 = image3[y1:y1 + h1, x1:x1 + w1]

        gray3 = cv2.cvtColor(image3, cv2.COLOR_BGR2GRAY)
        gray4 = cv2.cvtColor(image4, cv2.COLOR_BGR2GRAY)
        _, binary_image3 = cv2.threshold(gray3, process_threshold_NUM, 255, cv2.THRESH_BINARY_INV)
        _, binary_image4 = cv2.threshold(gray4, process_threshold_NUM, 255, cv2.THRESH_BINARY_INV)

        contours3, _ = cv2.findContours(binary_image3, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours4, _ = cv2.findContours(binary_image4, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        merged_contour3 = np.concatenate(contours3)
        merged_contour4 = np.concatenate(contours4)

        x3, y3, w3, h3 = cv2.boundingRect(merged_contour3)
        x4, y4, w4, h4 = cv2.boundingRect(merged_contour4)

        roi1 = image3[y3:y3 + h3, x3:x3 + w3]
        roi2 = image2[y4:y4 + h4, x4:x4 + w4]
        roi1 = cv2.resize(roi1, (roi2.shape[1], roi2.shape[0]))

        return roi1, roi2, image2, x4, y4, w4, h4

    def process_and_display_difference_images(self,partial_image, matched_region, process_threshold_NUM,compare_threshold_NUM,pattern_compare_threshold_NUM,weight_threshold_NUM):
        global image_rectangle
        try:
            # 确保partial_image与matched_region具有相同的尺寸
            partial_image = cv2.resize(partial_image, (matched_region.shape[1], matched_region.shape[0]))
            gray_matched_region = cv2.cvtColor(matched_region, cv2.COLOR_BGR2GRAY)
            _, binary_matched_region = cv2.threshold(gray_matched_region, process_threshold_NUM, 255,
                                                     cv2.THRESH_BINARY_INV)
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
            _, binary_difference = cv2.threshold(gray_difference, compare_threshold_NUM, 255, cv2.THRESH_BINARY)
            # cv2.imshow('binary_difference', binary_difference)
            # cv2.waitKey(0)
            white_pixel_count = np.sum(binary_difference == 255)
            percent = (white_pixel_count * weight_threshold_NUM) / all_pixel_count
            # print(white_pixel_count, 'white_pixel_count',compare_threshold_NUM,all_pixel_count,'all_pixel_count',percent)
            # 寻找差异区域的轮廓
            contours, _ = cv2.findContours(binary_difference, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 合并相邻的轮廓
            merged_contours = []
            current_contour = None
            # 合并相邻的轮廓
            for contour in contours:
                area = cv2.contourArea(contour)
                # print(area, 'area')
                if area > 20:
                    x1, y1, w1, h1 = cv2.boundingRect(current_contour)
                    x2, y2, w2, h2 = cv2.boundingRect(contour)
                    if current_contour is None:
                        current_contour = contour
                    elif x2 - (x1 + w1) < 100:
                        # 如果相邻，则合并两个轮廓
                        current_contour = np.concatenate((current_contour, contour))
                    else:
                        # 如果不相邻，则将当前轮廓添加到合并列表中，并更新当前轮廓为下一个轮廓
                        merged_contours.append(current_contour)
                        current_contour = contour
                else:
                    pass

            # 将最后一个轮廓添加到合并列表中
            if current_contour is not None:
                merged_contours.append(current_contour)
            try:
                for contour in merged_contours:
                    area = cv2.contourArea(contour)
                    # print(area, 'area') #and percent > 0.15
                    if area > pattern_compare_threshold_NUM:
                        image_rectangle = True
                        x, y, w, h = cv2.boundingRect(contour)
                        # 绘制方框
                        cv2.rectangle(matched_region, (x, y), (x + w, y + h), (0, 0, 255), 6)
            except:
                image_rectangle = True
                matched_region = matched_region
            return matched_region

        except Exception as e:
            # print(f"An exception occurred: {str(e)}")
            # return None
            pass

# Usage example:
# matcher = ImageMatcher()
# template_image = cv2.imread('template_image.jpg')
# image = cv2.imread('image.jpg')
# result = matcher.process_all_image(template_image, image)
