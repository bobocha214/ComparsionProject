# 生成一个测试用例，包含5个ROI坐标
test_case = [
    (165, 46, 30, 20),
    (201, 315, 30, 20),
    (1216, 318, 30, 20),
    (933, 327, 30, 20),
    (0, 622, 30, 20)
]

# 定义排序函数，以ROI的左上角坐标 (x, y) 作为关键字，考虑y坐标和x坐标
def roi_sort_key(roi):
    x, y, _, _ = roi
    y_threshold = 50
    y_group = y // y_threshold
    return (y_group, x, y)

# 使用排序函数对测试用例中的ROI进行排序
sorted_rois = sorted(test_case, key=roi_sort_key)

# 打印排序结果
for roi in sorted_rois:
    print(roi)
