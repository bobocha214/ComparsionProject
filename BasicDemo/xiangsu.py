import cv2
import numpy as np
import time


def binarize_image(image):
    """
    将图像二值化
    :param image: 输入图像
    :return: 二值化后的图像
    """
    # Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply binary thresholding
    _, binary_image = cv2.threshold(gray_image, 95, 255, cv2.THRESH_BINARY)

    return binary_image


def filter_image(image):
    """
    对图像进行滤波
    :param image: 输入图像
    :return: 滤波后的图像
    """
    # Apply a Gaussian blur filter
    filtered_image = cv2.bilateralFilter(image, 20, 20, 20)
    # filtered_image = cv2.bilateralFilter(image, 60, 100, 20)
    return filtered_image


def pixel_equal(image1, image2, x, y):
    """
    判断两个像素是否相同
    :param image1: 图片1
    :param image2: 图片2
    :param x: 位置x
    :param y: 位置y
    :return: 像素是否相同
    """
    # 取两个图片像素点
    piex1 = image1[y, x]
    piex2 = image2[y, x]
    print(piex1, piex2)
    threshold = 255
    # 比较每个像素点的值是否在阈值范围内，若两张图片的像素值都在某一阈值内，则认为它的像素点是一样的
    if abs(int(piex1) - int(piex2)) < threshold:
        return True
    else:
        return False


def compare(image1, image2):
    """
    进行比较
    :param image1: 图片1
    :param image2: 图片2
    :return:
    """
    left = 40  # 坐标起始位置
    right_num = 0  # 记录相同像素点个数
    false_num = 0  # 记录不同像素点个数
    all_num = 0  # 记录所有像素点个数

    binary_image1 = binarize_image(image1)
    binary_image2 = binarize_image(image2)
    cv2.imshow("Binary Image 1", binary_image1)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    cv2.imshow("Binary Image 2", binary_image2)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    filter_image1 = filter_image(binary_image1)
    filter_image2 = filter_image(binary_image2)
    diff_image = image1.copy()

    for i in range(left, binary_image1.shape[1]):
        for j in range(binary_image1.shape[0]):
            if pixel_equal(filter_image1, filter_image2, i, j):
                right_num += 1
            else:
                false_num += 1
                cv2.rectangle(diff_image, (i, j), (i + 1, j + 1), (0, 0, 255), -1)  # 使用红色 (0, 0, 255)
            all_num += 1

    same_rate = right_num / all_num  # 相同像素点比例
    nosame_rate = false_num / all_num  # 不同像素点比例
    print("same_rate: ", same_rate)
    print("nosame_rate: ", nosame_rate)
    cv2.imwrite("image/diff_image.jpg", diff_image)


if __name__ == "__main__":
    t1 = time.time()
    image1 = cv2.imread("image/cut.jpg")
    image2 = cv2.imread("image/cut1.jpg")
    compare(image1, image2)
    t2 = time.time()
    print("t=", t2 - t1)
