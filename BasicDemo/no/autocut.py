import cv2
import numpy as np

# 读取要搜索的图像，并进行二值化处理
search_image = cv2.imread('../cuttest/cut_4.jpg')
ret, binary_search_image = cv2.threshold(search_image, 150, 255, cv2.THRESH_BINARY)

# 读取模板图像并进行二值化处理
template_image = cv2.imread('../cuttest/cut_51.jpg')
ret, binary_template_image = cv2.threshold(template_image, 150, 255, cv2.THRESH_BINARY)

# 定义矩形切分的行数和列数
rows = 10  # 行数
cols = 10  # 列数

# 获取图像尺寸
search_height, search_width, channels1 = binary_search_image.shape
template_height, template_width, channels2 = binary_template_image.shape

# 计算每个矩形的高度和宽度
rect_height = search_height // rows
rect_width = search_width // cols

# 设定模板匹配阈值
threshold = 0.9

# 用于保存匹配结果的图像（复制原图像）
result_image = template_image.copy()

# 用于保存每张图片的匹配结果和权重
match_results = []
result_weights = []

# 设置用于凸显0.7匹配率的权重倍数
highlight_weight_multiplier = 5000

# 循环遍历矩形
for row in range(rows):
    for col in range(cols):
        # 计算矩形的位置坐标
        x_start = col * rect_width
        y_start = row * rect_height
        x_end = x_start + rect_width
        y_end = y_start + rect_height

        # 切分图像
        sub_image = binary_search_image[y_start:y_end, x_start:x_end]
        tem_image = binary_template_image[y_start:y_end, x_start:x_end]

        # 使用模板匹配函数
        result = cv2.matchTemplate(sub_image, tem_image, cv2.TM_CCOEFF_NORMED)

        # 获取匹配度高于阈值的位置
        locations = np.where(result >= threshold)

        # 在结果图像上绘制矩形框标记匹配位置
        for pt in zip(*locations[::-1]):
            top_left = (pt[0] + x_start, pt[1] + y_start)
            bottom_right = (top_left[0] + template_width, top_left[1] + template_height)
            print('top_left, bottom_right',top_left, bottom_right)
            cv2.rectangle(result_image, top_left, bottom_right, (0, 255, 0), 1)

        # 获取最大匹配值并添加到匹配结果列表
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        print(row,col,max_val)
        match_results.append(max_val)

        # 根据匹配率设置权重
        if max_val <= 0.95:  # 设置匹配率阈值
            weight = round(max_val,2) * highlight_weight_multiplier
            print(weight,'max_val <= 0.8')
        else:
            weight = 10 # 对于其他匹配率，保持原始权重或者设置为其他值
            print(weight, 'max_val > 0.8')
        result_weights.append(weight)

# 保存带有匹配标记的图像
cv2.imwrite('../matched_image.jpg', result_image)

# 计算加权平均匹配率
weighted_mean_matching_rate = np.average(match_results, weights=result_weights)

# 假设期望的匹配率阈值为 expected_threshold
expected_threshold = 0.8

# 检查加权平均匹配率与期望阈值的差异
if weighted_mean_matching_rate < expected_threshold:
    print("Error: Weighted Mean Matching Rate is below the expected threshold.")
else:
    print(f"Weighted Mean Matching Rate: {weighted_mean_matching_rate:.2f}")

