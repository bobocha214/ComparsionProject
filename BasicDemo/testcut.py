import os
import cv2
import numpy as np
from matplotlib import pyplot as plt


# 定义一个函数来比较两个图片的大小是否相似
def are_images_similar(image1, image2, threshold=3):
    img1 = cv2.imread(image1)
    img2 = cv2.imread(image2)
    print(image1,image2)
    # 获取图片的宽度和高度
    height1, width1, _ = img1.shape
    height2, width2, _ = img2.shape
    print(height1,width1)
    print(height2,width2)
    # 计算宽度和高度差异
    width_difference = abs(width1 - width2)
    height_difference = abs(height1 - height2)
    print(width_difference,height_difference)
    # 如果宽度和高度差异都小于阈值，则认为图片大小相近
    if width_difference < threshold and height_difference < threshold:
        return True
    else:
        return False


def compare_images(imageA_path, imageB_path, threshold=30):
    # 读取两张图片
    image1 = cv2.imread(imageA_path)
    image2 = cv2.imread(imageB_path)
    plt.subplot(121), plt.imshow(image1),
    plt.title('Matching Result'), plt.axis('off')
    plt.subplot(122), plt.imshow(image2),
    plt.title('Detected Point'), plt.axis('off')
    plt.show()

    # 检查是否成功读取了图片
    if image1 is None or image2 is None:
        return False

    # 确保两张图片具有相同的尺寸
    if image1.shape != image2.shape:
        image1 = cv2.resize(image1, (image2.shape[1], image2.shape[0]))

    # 将两张图片转换为灰度图像
    gray_image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    gray_image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

    # 比较两张灰度图像的每个像素，找出不同之处
    difference = cv2.absdiff(gray_image1, gray_image2)

    # 根据阈值创建二值图像
    _, thresholded_difference = cv2.threshold(difference, threshold, 255, cv2.THRESH_BINARY)
    # 计算白色像素数量
    white_pixel_count = np.sum(thresholded_difference == 255)
    black_pixel_count=np.sum(thresholded_difference == 0)
    image_area = gray_image1.shape[0] * gray_image1.shape[1]
    print(white_pixel_count,black_pixel_count,'blacnandwhite')
    if white_pixel_count < 100:
        weighted_white_pixel_count = white_pixel_count
    else:
        white_pixel_weight = 10
        weighted_white_pixel_count = white_pixel_count * white_pixel_weight

    # 获取整张图片的像素数量
    total_pixel_count = thresholded_difference.size

    # 计算加权后的比例
    weighted_white_to_black_ratio = 1 - weighted_white_pixel_count / total_pixel_count

    # 查找轮廓
    contours, _ = cv2.findContours(thresholded_difference, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 在一张新的图像上绘制圆圈以标记不同之处
    marked_image = image1.copy()
    for contour in contours:
        area = cv2.contourArea(contour)
        print(area)
        if area > 100:
            x, y, w, h = cv2.boundingRect(contour)
            print(x, y, w, h, 'counter')
            cv2.rectangle(image2, (x, y), (x + w, y + h), (0, 0, 255), 2)  # 使用红色绘制方框
            cv2.imwrite(imageB_path, image2)
    # cv2.imwrite('marked_difference.jpg', marked_image)
    print('weighted_white_to_black_ratio',weighted_white_to_black_ratio)


# 定义两个文件夹的路径
folder1 = 'cuts'
folder2 = 'cuttest'

# 遍历文件夹1中的图片
for filename1 in os.listdir(folder1):
    if filename1.endswith(('.jpg', '.jpeg', '.png')):  # 确保文件是图片文件
        filepath1 = os.path.join(folder1, filename1)

        # 遍历文件夹2中的图片
        for filename2 in os.listdir(folder2):
            if filename2.endswith(('.jpg', '.jpeg', '.png')):  # 确保文件是图片文件
                filepath2 = os.path.join(folder2, filename2)

                # 检查图片大小是否相似
                if are_images_similar(filepath1, filepath2):
                    # 执行某个方法，例如打印文件路径
                    compare_images(filepath1, filepath2, threshold=30)
