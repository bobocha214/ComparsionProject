import cv2
import numpy as np
from matplotlib import pyplot as plt

img = cv2.imread('image/TEST/TE2.jpg')
img2 = img.copy()
template = cv2.imread('image/TEST/TE2.jpg')
if template is not None:
    h, w, _ = template.shape  # 获取模板的高度和宽度
    print("模板图像的宽度和高度：", w, h)
else:
    print("无法加载模板图像")
# 所有的匹配方法
# 定义匹配结果的阈值
threshold = 0.7  # 根据需要调整阈值
methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR',
           'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']
for meth in methods:
    img = img2.copy()
    print(meth,'meth')
    method = eval(meth)  # 去掉字符串的引号
    # 匹配
    res = cv2.matchTemplate(img, template, method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    print(min_val, max_val, min_loc, max_loc)
    # 使用不同的比较方法，对结果的解释不同
    # 如果方法是 TM_SQDIFF or TM_SQDIFF_NORMED, 取最小值
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        top_left = min_loc
    else:
        top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)
    if threshold < max_val < 1:
        cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 4)
        plt.subplot(121), plt.imshow(res, cmap='gray'),
        plt.title('Matching Result'), plt.axis('off')
        plt.subplot(122), plt.imshow(img),
        plt.title('Detected Point'), plt.axis('off')
        plt.suptitle(f"{meth}, Max Value: {max_val}")
        plt.show()
        print(f"{meth} - 找到位置")
    else:
        cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 4)
        plt.subplot(121), plt.imshow(res, cmap='gray'),
        plt.title('Matching Result'), plt.axis('off')
        plt.subplot(122), plt.imshow(img, cmap='gray'),
        plt.title('Detected Point'), plt.axis('off')
        plt.suptitle(f"{meth}, Max Value: {max_val}")
        plt.show()
        print(f"{meth} - 未找到准确位置")

