import cv2
import numpy as np

global img
# global point1,point2
cut_Pos = np.zeros((2, 2), int)
def on_mouse(event, x, y, flags, param):
    global img, point1, point2
    img2 = img.copy()
    if event == cv2.EVENT_LBUTTONDOWN:
        point1 = (x, y)
        cv2.circle(img2, point1, 10, (0, 255, 0), 2)  # 点击左键，显示绿色圆圈
        cv2.imshow('image', img2)
    elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):
        cv2.rectangle(img2, point1, (x, y), (255, 0, 0), 2)  # 移动点击下的左键，画出蓝色截图框
        cv2.imshow('image', img2)
    elif event == cv2.EVENT_LBUTTONUP:
        point2 = (x, y)
        cv2.rectangle(img2, point1, point2, (0, 0, 255), 2)  # 松开左键，显示最终的红色截图框
        cv2.imshow('image', img2)

        cut_Pos[0][0] = min(point1[0], point2[0])
        cut_Pos[0][1] = max(point1[0], point2[0])
        cut_Pos[1][0] = min(point1[1], point2[1])
        cut_Pos[1][1] = max(point1[1], point2[1])
        cv2.imshow('image', img[cut_Pos[1][0]:cut_Pos[1][1], cut_Pos[0][0]:cut_Pos[0][1]])


def main():
    global img
    img = cv2.imread('image/111.jpg')
    cv2.namedWindow('image')
    cv2.setMouseCallback('image', on_mouse)
    cv2.imshow('image', img)
    cv2.waitKey(0)


if __name__ == '__main__':
    main()