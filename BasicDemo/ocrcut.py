import cv2
from cnocr import CnOcr

img = cv2.imread('image/save3.jpg')
ocr = CnOcr()
out = ocr.ocr(img)
print(out)

result_image = img.copy()

sn_data = None
for item in out:
    if 'SN:' in item['text']:
        sn_data = item
        break
position = sn_data['position']
print(position)
x, y, w, h = cv2.boundingRect(position)
cv2.rectangle(result_image, (x, y), (x + w, y + h), (0,255,0), 2)
roi = img[y+5:y+h, x+130:x+w]
# 保存框出的区域为图像文件
cv2.imwrite('boxed_region.jpg', roi)
cv2.namedWindow('roi', cv2.WINDOW_NORMAL)
cv2.imshow('roi',roi)
cv2.namedWindow('result_image', cv2.WINDOW_NORMAL)
cv2.imshow('result_image',result_image)
cv2.waitKey(0)