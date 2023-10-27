import cv2

def merge_rectangle_to_image(original_image_path, cropped_image_path, output_image_path, x_position, y_position):
    # 读取原始图像和裁剪的矩形图像
    original_image = cv2.imread(original_image_path)
    cropped_image = cv2.imread(cropped_image_path)

    # 获取裁剪矩形的宽度和高度
    rectangle_height, rectangle_width, _ = cropped_image.shape

    # 将裁剪的矩形放回原始图像中
    original_image[y_position:y_position + rectangle_height, x_position:x_position + rectangle_width] = cropped_image

    # 保存合并后的图像
    cv2.imwrite(output_image_path, original_image)

# 调用示例
merge_rectangle_to_image("original_image.jpg", "cropped_rectangle.jpg", "merged_image.jpg", 100, 200)
