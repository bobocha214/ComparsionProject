import cv2
import numpy as np

# 读取图片
image = cv2.imread('../image/cut/cut_2.jpg')

# 转换为灰度图像
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# 对灰度图像进行二值化处理，白底黑字
_, binary_image = cv2.threshold(gray_image, 150, 255, cv2.THRESH_BINARY)

# 显示二值化后的图像
cv2.imshow('Binary Image (White Background, Black Text)', binary_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
