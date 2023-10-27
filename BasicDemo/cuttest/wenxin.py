import cv2
import numpy as np


def extract_rotated_rect(image):
    cv2.imshow('image',image)
    cv2.waitKey(0)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred_image = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary_image = cv2.threshold(blurred_image, 150, 255, cv2.THRESH_BINARY_INV)
    cv2.imshow('binary_image',binary_image)
    cv2.waitKey(0)
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    merged_contour = np.concatenate(contours)
    rect = cv2.minAreaRect(merged_contour)
    angle = rect[2]
    return rect, merged_contour
image1=cv2.imread('cut_5.jpg')
rect1, merged_contour1 = extract_rotated_rect(image1)
pat=cv2.imread('cut_5.jpg')
mat=cv2.imread('cut_9.jpg')
pat = cv2.resize(pat, (mat.shape[1], mat.shape[0]))
difference = cv2.absdiff(pat, mat)

# 转换差异图像为灰度
gray_difference = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)

# 二值化差异图像
_, binary_difference = cv2.threshold(gray_difference, 100, 255, cv2.THRESH_BINARY)
cv2.imshow('binary_difference', binary_difference)
cv2.waitKey(0)