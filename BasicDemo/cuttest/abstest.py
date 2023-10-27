import cv2
import numpy as np

def process_and_display_difference_images(image_path1, image_path2, threshold=50):
    # 读取图像
    partial_image = cv2.imread(image_path1)
    matched_region = cv2.imread(image_path2)

    # 显示原始图像
    cv2.imshow("partial_image", partial_image)
    cv2.imshow("matched_region", matched_region)

    # 调整matched_region的大小以匹配partial_image1
    matched_region = cv2.resize(matched_region, (partial_image.shape[1], partial_image.shape[0]))
    cv2.imshow("matched_region1", matched_region)
    # 计算两图像的差异
    difference = cv2.absdiff(matched_region, partial_image)
    cv2.imshow("Difference", difference)

    # 转换差异图像为灰度
    gray_difference = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)

    try:
        # 二值化差异图像
        _, binary_difference = cv2.threshold(gray_difference, threshold, 255, cv2.THRESH_BINARY)
        cv2.imshow("binary_difference", binary_difference)
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
            x, y, w, h = cv2.boundingRect(contour)
            # 绘制方框
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)

    except:
        pass

    # 显示带有边界框的结果
    cv2.imshow("Matched Region with Differences", result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# 使用示例
image_path1 = 'partial_image0copy.jpg'
image_path2 = 'matched_image00copy.jpg'
process_and_display_difference_images(image_path1, image_path2)
