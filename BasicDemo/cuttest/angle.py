import cv2
import numpy as np

def process_and_rotate_image(input_image_path, output_image_path):
    # 读取图像
    image = cv2.imread(input_image_path)

    # 转换图像为灰度
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred_image = cv2.GaussianBlur(gray, (5, 5), 0)
    # 二值化图像
    _, binary_image = cv2.threshold(blurred_image, 200, 255, cv2.THRESH_BINARY_INV)
    kernel = np.ones((5, 5), np.uint8)
    opening = cv2.morphologyEx(binary_image, cv2.MORPH_OPEN, kernel)
    # 寻找轮廓
    contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    merged_contour = np.concatenate(contours)
    image4 = image.copy()
    # 计算包围所有轮廓的大旋转矩形
    rect = cv2.minAreaRect(merged_contour)
    box = cv2.boxPoints(rect)
    box = np.int0(box)
    cv2.drawContours(image4, [box], 0, (0, 0, 255), 2)
    cv2.imshow("image4", image4)
    # 创建一个掩码图像
    mask = np.ones_like(image)*255

    # 填充矩阵坐标对应的区域
    cv2.fillPoly(mask, [box], (255, 255, 255))
    # 使用掩码提取图像的指定区域
    result = cv2.bitwise_and(image, mask)
    cv2.imshow("result", result)
    # 寻找提取区域的边界框
    x, y, w, h = cv2.boundingRect(box)

    # 截取提取的区域
    cropped_area = result[y:y+h, x:x+w]
    cv2.imshow("cropped_area", cropped_area)
    # 计算包围所有轮廓的大旋转矩形
    rect = cv2.minAreaRect(merged_contour)

    # 获取旋转矩形的角度
    angle = rect[2]
    print(angle)

    if abs(angle) < 10:
        center_x, center_y = image.shape[1] // 2, image.shape[0] // 2  # 计算图像中心坐标
        rotation_matrix = cv2.getRotationMatrix2D((0, 0), angle, 1)

        # 旋转图像
        rotated_image = cv2.warpAffine(cropped_area, rotation_matrix, (image.shape[1], image.shape[0]),
                                       borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    else:
        rotated_image = image
    cv2.imshow("rotated_image", rotated_image)
    gray1 = cv2.cvtColor(rotated_image, cv2.COLOR_BGR2GRAY)
    _, binary_image1 = cv2.threshold(gray1, 200, 255, cv2.THRESH_BINARY_INV)
    cv2.imshow("binary_image1", binary_image1)

    # 寻找轮廓
    contours1, _ = cv2.findContours(binary_image1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    merged_contour1 = np.concatenate(contours1)

    x, y, w, h = cv2.boundingRect(merged_contour1)

    # 在原图中截取该区域
    image3 = rotated_image.copy()
    cv2.rectangle(image3, (x, y), (x+w, y+h), (0, 255, 0), 1)
    roi = rotated_image[y:y + h, x:x + w]
    cv2.imshow("roi1", roi)
    if abs(angle) < 10:
        rotation_matrix = cv2.getRotationMatrix2D((0, 0), -angle, 1)
        #rect[0]
        # 旋转图像
        rotated_image = cv2.warpAffine(roi, rotation_matrix, (image.shape[1], image.shape[0]),
                                       borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    else:
        rotated_image = image
    cv2.imshow("roi1", roi)
    # 显示旋转后的图像
    cv2.imshow("Rotated Image", rotated_image)
    cv2.imshow("image3", image3)
    cv2.imwrite(output_image_path, roi)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

# 使用示例
input_image_path = 'matched_image0.jpg'
output_image_path = 'matched_image00copy.jpg'
process_and_rotate_image(input_image_path, output_image_path)
