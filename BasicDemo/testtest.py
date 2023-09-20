import cv2
import time,PIL,os
from PIL import ImageGrab
import numpy as np
#截图
def cut():
    global img
    scrren_cut()
    img = cv2.imread('screen.jpg')
    cv2.namedWindow('image')
    cv2.setMouseCallback('image', on_mouse)
    cv2.imshow('image', img)
    cv2.waitKey(0)
    os.remove('screen.jpg')
def scrren_cut():
    beg = time.time()
    debug = False
    # img = ImageGrab.grab(bbox=(250, 161, 1141, 610))
    image = ImageGrab.grab()
    image.save("screen.jpg")
    # PIL image to OpenCV image
def on_mouse(event, x, y, flags, param):
    global img, point1, point2
    img2 = img.copy()
    if event == cv2.EVENT_LBUTTONDOWN:         #左键点击
        point1 = (x,y)
        cv2.circle(img2, point1, 10, (0,255,0), 5)
        cv2.imshow('image', img2)
    elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):               #按住左键拖曳
        cv2.rectangle(img2, point1, (x,y), (255,0,0), 5)
        cv2.imshow('image', img2)
    elif event == cv2.EVENT_LBUTTONUP:         #左键释放
        point2 = (x,y)
        cv2.rectangle(img2, point1, point2, (0,0,255), 5)
        cv2.imshow('image', img2)
        min_x = min(point1[0],point2[0])
        min_y = min(point1[1],point2[1])
        width = abs(point1[0] - point2[0])
        height = abs(point1[1] -point2[1])
        cut_img = img[min_y:min_y+height, min_x:min_x+width]
        cv2.imwrite('cut.jpg', cut_img)


cut()