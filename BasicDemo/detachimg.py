import cv2
import numpy as np

# 加载图像
image_path = "image/test.jpg"  # 替换为实际图像路径
image = cv2.imread(image_path)


# 将截图转换为OpenCV图像格式
screenshot_cv = np.array(image)
screenshot_cv = cv2.cvtColor(screenshot_cv, cv2.COLOR_RGB2BGR)

# 在目标图像中查找截图内容
result = cv2.matchTemplate(image, screenshot_cv, cv2.TM_CCOEFF_NORMED)
min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

# 获取匹配位置的坐标
match_x, match_y = max_loc
match_w, match_h = screenshot_cv.shape[1], screenshot_cv.shape[0]

# 绘制矩形框标记匹配位置
cv2.rectangle(image, (match_x, match_y), (match_x + match_w, match_y + match_h), (0, 255, 0), 2)

# 显示结果
cv2.imshow("Result", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
