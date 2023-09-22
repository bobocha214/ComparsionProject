import cv2
import numpy as np
from skimage.metrics import structural_similarity as compare_ssim
# 读取要搜索的图像
search_image = cv2.imread('cuts/cut_1.jpg', cv2.IMREAD_GRAYSCALE)

# 读取模板图像
template_image = cv2.imread('cuts/cut_6.jpg', cv2.IMREAD_GRAYSCALE)
print('TM_CCOEFF_NORMED')
print('cut_5.jpg')

# 检查图像尺寸是否匹配
if search_image.shape != template_image.shape:
    print('图像尺寸不匹配')
    # 如果尺寸不匹配，调整模板图像的尺寸为主图像的尺寸
    template_image = cv2.resize(template_image, (search_image.shape[1], search_image.shape[0]))
    cv2.imshow('template_image', template_image)
    cv2.waitKey(0)
# 对要搜索的图像进行二值化处理
ret, search_image_bin = cv2.threshold(search_image, 150, 255, cv2.THRESH_BINARY)
cv2.imshow('search_image_bin', search_image_bin)
cv2.waitKey(0)
# 对模板图像进行二值化处理
ret, template_image_bin = cv2.threshold(template_image, 150, 255, cv2.THRESH_BINARY)
cv2.imshow('template_image_bin', template_image_bin)
cv2.waitKey(0)
# 使用模板匹配函数
result = cv2.matchTemplate(search_image_bin, template_image_bin, cv2.TM_CCOEFF_NORMED)
threshold = 0.7
# 获取匹配度高于阈值的位置
locations = np.where(result >= threshold)

# 在主图像上绘制矩形框标记匹配位置
for pt in zip(*locations[::-1]):
    cv2.rectangle(search_image_bin, pt, (pt[0] + template_image_bin.shape[1], pt[1] + template_image_bin.shape[0]), (0, 255, 0), 2)


# 保存带有匹配标记的图像
ssim = compare_ssim(search_image_bin, template_image_bin)
# 输出SSIM相似度值
print("SSIM相似度:", ssim)

# 保存带有匹配标记的图像
cv2.imwrite('matched_image.jpg', search_image_bin)
# 获取匹配度最大的位置
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
print(min_val, max_val, min_loc, max_loc)
template_width, template_height = template_image_bin.shape[1], template_image_bin.shape[0]
# 计算矩形框的坐标
top_left = max_loc
bottom_right = (top_left[0] + template_width, top_left[1] + template_height)

# 在主图像上绘制矩形框
cv2.rectangle(search_image_bin, top_left, bottom_right, (0, 255, 0), 2)
# 获取模板图像的宽度和高度
cv2.imwrite('search_image_bin.jpg', search_image_bin)