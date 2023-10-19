# -- coding: utf-8 --
import time
import tkinter.messagebox
from functools import partial
from multiprocessing import Pool, Manager
from tkinter import messagebox
from CamOperation_class import *
from PIL import Image, ImageTk
import serial
import csv
from cnocr import CnOcr
import threading
import pickle
import win32event
import win32api
import winerror
import pandas as pd
from loguru import logger
import serial.tools.list_ports
import matplotlib
import cv2
import numpy as np
# from bounding import bounding
import concurrent.futures
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
from image_diff import match_and_extract_region


def custom_filter(record):
    # 如果消息与上一条消息相同，返回False，表示丢弃该消息
    if hasattr(custom_filter, "last_message") and custom_filter.last_message == record["message"]:
        return False
    custom_filter.last_message = record["message"]
    return True


logger.add('log\\runtime_{time}.log', rotation='00:00', retention='2 days', backtrace=True, diagnose=True,
           filter=custom_filter)


# 获取选取设备信息的索引，通过[]之间的字符去解析
def TxtWrapBy(start_str, end, all):
    start = all.find(start_str)
    if start >= 0:
        start += len(start_str)
        end = all.find(end, start)
        if end >= 0:
            return all[start:end].strip()


# 将返回的错误码转换为十六进制显示
def ToHexStr(num):
    chaDic = {10: 'a', 11: 'b', 12: 'c', 13: 'd', 14: 'e', 15: 'f'}
    hexStr = ""
    if num < 0:
        num = num + 2 ** 32
    while num >= 16:
        digit = num % 16
        hexStr = chaDic.get(digit, str(digit)) + hexStr
        num //= 16
    hexStr = chaDic.get(num, str(num)) + hexStr
    return hexStr


@logger.catch
def show_frame(frame):
    frame.tkraise()


@logger.catch
def show_mianframe(frame):
    global loginflag
    loginflag = True
    # 需要解开
    stop_grabbing()
    show_frame(frame)
    start_grabbing1()


# 返回登陆结果信息

loginflag = True


@logger.catch
def do_login(login_win, account_va, password_va, frame2):
    global loginflag
    username = account_va.get()
    password = password_va.get()
    if (username or password):
        if (username == 'admin' and password == '12345678'):
            tk.messagebox.showinfo("登陆成功", "欢迎您，管理员！")
            login_win.destroy()
            loginflag = True
            # 需要解开
            stop_grabbing()
            show_frame(frame2)
            start_grabbing()
        else:
            tk.messagebox.showerror("登录失败", "用户名或密码错误！")
            login_win.destroy()
            loginflag = True
            show_frame(frame1)
    else:
        tk.messagebox.showerror("登录失败", "请填写用户名和密码！")
        login_win.destroy()
        loginflag = True
        show_frame(frame1)


# 登陆取消

@logger.catch
def do_cancel(login_win):
    global loginflag
    login_win.destroy()
    loginflag = True


@logger.catch
def on_exit(login_win):
    global loginflag
    loginflag = True
    login_win.destroy()


# 显示登陆页面
@logger.catch
def show_login_page(frame2):
    global loginflag
    if loginflag:
        login_win = tk.Toplevel()
        login_win.title('登陆')
        login_win.iconbitmap(current_file + 'logo.ico')
        login_win.geometry('300x200')
        login_win.protocol("WM_DELETE_WINDOW", lambda: on_exit(login_win))
        # 用户登陆
        tk.Label(login_win, text='用户登陆', font=('微软雅黑', 20)).grid(row=0, column=0, columnspan=10)
        # 登陆账号
        tk.Label(login_win, text='登陆账号:', font=('微软雅黑', 15)).grid(row=1, column=0, padx=10)
        # 账号输入框
        account_va = tk.StringVar()
        tk.Entry(login_win, textvariable=account_va).grid(row=1, column=1, padx=5)

        # 登陆密码
        tk.Label(login_win, text='登陆密码:', font=('微软雅黑', 15)).grid(row=2, column=0, padx=10)
        # 密码输入框
        password_va = tk.StringVar()
        tk.Entry(login_win, textvariable=password_va, show='*').grid(row=2, column=1, padx=5)
        # 登陆按钮
        tk.Button(login_win, text='登陆', font='微软雅黑', bg='red', fg='white', width=10, relief="flat",
                  command=lambda: do_login(login_win, account_va, password_va, frame2)).grid(row=3, column=0,
                                                                                             columnspan=5)
        tk.Button(login_win, text='取消', font='微软雅黑', bg='green', fg='white', width=10, relief="flat",
                  command=lambda: do_cancel(login_win)).grid(row=5, column=0, columnspan=5)
        loginflag = False
    else:
        pass


@logger.catch
def show_label(show):
    if show:
        labelORIGIN.grid(row=6, column=0, columnspan=2, sticky='wens', padx=30, pady=10)
        time.sleep(0.1)
        labelORIGIN.grid_forget()
        labelNG.grid_forget()
        labelOK.grid(row=6, column=0, columnspan=2, sticky='wens', padx=30, pady=10)
    else:
        labelORIGIN.grid(row=6, column=0, columnspan=2, sticky='wens', padx=30, pady=10)
        time.sleep(0.1)
        labelORIGIN.grid_forget()
        labelOK.grid_forget()
        labelNG.grid(row=6, column=0, columnspan=2, sticky='wens', padx=30, pady=10)


@logger.catch
def handle_space(event):
    labelORIGIN.grid_forget()
    labelOK.grid_forget()
    labelNG.grid_forget()
    labelORIGIN.grid(row=6, column=0, columnspan=2, sticky='wens', padx=30, pady=10)


@logger.catch
def base_path(path):
    if getattr(sys, 'frozen', None):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)


if __name__ == "__main__":
    mutex = win32event.CreateMutex(None, False, 'MyMutexName')
    if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
        mutex = None
    else:
        global deviceList
        deviceList = MV_CC_DEVICE_INFO_LIST()
        global tlayerType
        tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
        global cam
        cam = MvCamera()
        global nSelCamIndex
        nSelCamIndex = 0
        global obj_cam_operation
        obj_cam_operation = 0
        global b_is_run
        global ser1
        b_is_run = False
        last_result = None
        threadflag = None
        COMGUNNUM = ""
        COMSIGNALNUM = ""
        previous_COMGUNNUM = ""
        previous_COMSIGNALNUM = ""
        contour_info_list = []
        signalbuttonup = ''
        signalbuttondown = ''
        left_left_NUM = 0
        left_upper_NUM = 0
        right_left_NUM = 0
        right_lower_NUM = 0
        process_threshold_NUM = 0
        compare_threshold_NUM = 0
        process_kernel_x_threshold_NUM = 0
        process_kernel_y_threshold_NUM = 0
        process_area_low_threshold_NUM = 0
        process_area_threshold_high_NUM = 0
        weight_threshold_NUM = 0
        pattern_compare_threshold_NUM = 0
        image_threading_NUM=0
        different_threshold_NUM=0
        COM_sharedata = {'sedata': None}
        current_file = base_path('')
        parentdir = current_file + 'image\\test.jpg'
        parentdirsign = current_file + 'image\\sign.jpg'
        parentdirdemo = current_file + 'image\\demo.jpg'
        folder_path = current_file + 'cuts'
        folder_path1 = current_file + 'cut1'
        imagepath = current_file + 'image'
        csvpath = current_file + 'csv'
        # 界面设计代码
        window = tk.Tk()
        window.title('条码比对系统')
        window.iconbitmap(current_file + 'logo.ico')
        window.geometry('1400x800')
        main_menu = tk.Menu(window)
        picklename = 'settings.dat'
        picklename1 = 'parameter.dat'
        compickle = 'comport.dat'
        signaldata = 'signal.dat'
        imagepickle = 'imagepickle.dat'
        screenshot = 'screenshot.dat'
        saveImg = 'saveImg.dat'
        thresholdpickle = 'thresholdpickle.dat'
        comparea = 'comparea.dat'
        # 创建一个空列表以存储所有图片
        image_list = []
        pool = Pool()
        image_lock = threading.Lock()
        cut_Pos = np.zeros((2, 2), int)
        global screenshotNum
        screenshotNum = 0
        global screen_img
        event = threading.Event()
        try:
            with open(thresholdpickle, "rb") as f:
                loaded_params = pickle.load(f)
                param1_loaded, param2_loaded, param3_loaded, param4_loaded, param5_loaded, param6_loaded, param7_loaded,param8_loaded,param9_loaded,param10_loaded = loaded_params
                process_threshold_NUM = int(param1_loaded)
                compare_threshold_NUM = int(param2_loaded)
                process_kernel_x_threshold_NUM = int(param3_loaded)
                process_kernel_y_threshold_NUM = int(param4_loaded)
                process_area_low_threshold_NUM = int(param5_loaded)
                process_area_threshold_high_NUM = int(param6_loaded)
                weight_threshold_NUM = int(param7_loaded)
                pattern_compare_threshold_NUM=int(param8_loaded)
                image_threading_NUM = int(param9_loaded)
                different_threshold_NUM = int(param10_loaded)

        except:
            process_threshold_NUM = 200
            compare_threshold_NUM = 60
            process_kernel_x_threshold_NUM = 75
            process_kernel_y_threshold_NUM = 1
            process_area_low_threshold_NUM = 4000
            process_area_threshold_high_NUM = 250000
            weight_threshold_NUM = 10
            pattern_compare_threshold_NUM=30
            image_threading_NUM = 9
            different_threshold_NUM = 200
        thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=image_threading_NUM)
        try:
            with open(signaldata, 'rb') as f:
                signalbuttonup = pickle.load(f)
                signalbuttondown = pickle.load(f)
                # print(checked,'withwith')
        except:
            signalbuttonup = ''
            signalbuttondown = ''
        try:
            with open(comparea, 'rb') as f:
                left_left_NUM = int(pickle.load(f))
                left_upper_NUM = int(pickle.load(f))
                right_left_NUM = int(pickle.load(f))
                right_lower_NUM = int(pickle.load(f))
        except:
            left_left_NUM = 100
            left_upper_NUM = 100
            right_left_NUM = 200
            right_lower_NUM = 200
        try:
            with open(picklename, 'rb') as f:
                checked = pickle.load(f)
                # print(checked,'withwith')
        except:
            checked = False
        try:
            with open(saveImg, 'rb') as f:
                img_checked = pickle.load(f)
        except:
            img_checked = False
        try:
            with open(compickle, 'rb') as f:
                COMGUNNUM = pickle.load(f)
                # COMSIGNALNUM=pickle.load(f)
        except:
            COMGUNNUM = ""
        try:
            with open(screenshot, 'rb') as f:
                screenshotNum = int(pickle.load(f))
        except:
            screenshotNum = 0

        # try:
        #     with open(imagepickle, 'rb') as f:
        #         IMAGEMatchValue = pickle.load(f)
        # except:
        #     IMAGEMatchValue = "TM_CCOEFF_NORMED"

        output_directory1 = 'image'
        if not os.path.exists(imagepath):
            # 如果不存在，创建文件夹
            os.makedirs(output_directory1, exist_ok=True)
        output_directory2 = 'csv'
        if not os.path.exists(csvpath):
            # 如果不存在，创建文件夹
            os.makedirs(output_directory2, exist_ok=True)
        # 创建目录以保存图像
        output_directory3 = 'cuts'
        if not os.path.exists(folder_path):
            # 如果不存在，创建文件夹
            os.makedirs(output_directory3, exist_ok=True)
        output_directory4 = 'cut1'
        if not os.path.exists(folder_path1):
            # 如果不存在，创建文件夹
            os.makedirs(output_directory4, exist_ok=True)
        global frame1
        try:
            ser1 = serial.Serial(COMGUNNUM, 9600, timeout=0.5)
        except serial.SerialException as e:
            tkinter.messagebox.showinfo('show info', '串口打开失败，请选择端口后重试！')
        except Exception as e:
            tkinter.messagebox.showinfo('show info', '有异常，请检查设备！')


        frame1 = tk.Frame(window)
        frame2 = tk.Frame(window)
        main_menu.add_command(label="比对界面", command=lambda: show_mianframe(frame1))
        main_menu.add_command(label="管理员界面", command=lambda: show_login_page(frame2))
        window.config(menu=main_menu)
        window.grid_rowconfigure(0, weight=1)
        window.grid_columnconfigure(0, weight=1)
        frame1.grid(row=0, column=0, sticky="nsew")
        frame2.grid(row=0, column=0, sticky="nsew")
        frame1.grid_columnconfigure(0, weight=0)
        frame1.grid_columnconfigure(1, weight=0)
        frame1.grid_columnconfigure(2, weight=1)
        frame1.grid_columnconfigure(3, weight=1)
        frame1.grid_rowconfigure(0, weight=1)
        frame1.grid_rowconfigure(1, weight=1)
        frame1.grid_rowconfigure(2, weight=1)
        frame1.grid_rowconfigure(3, weight=1)
        frame1.grid_rowconfigure(4, weight=1)
        frame1.grid_rowconfigure(5, weight=1)
        frame1.grid_rowconfigure(6, weight=1)
        frame1.grid_rowconfigure(7, weight=1)
        frame1.grid_rowconfigure(7, weight=1)
        frame1.grid_rowconfigure(8, weight=1)
        frame1.grid_rowconfigure(9, weight=1)
        frame1.grid_rowconfigure(10, weight=1)
        frame1.grid_rowconfigure(11, weight=1)
        frame1.grid_rowconfigure(12, weight=1)
        frame1.grid_rowconfigure(13, weight=1)
        frame1.grid_rowconfigure(14, weight=1)
        frame1.grid_rowconfigure(15, weight=1)
        frame1.grid_rowconfigure(16, weight=1)

        frame2.grid_columnconfigure(0, weight=0)
        frame2.grid_columnconfigure(1, weight=0)
        frame2.grid_columnconfigure(2, weight=0)
        frame2.grid_columnconfigure(3, weight=0)
        frame2.grid_columnconfigure(4, weight=0)
        frame2.grid_columnconfigure(5, weight=0)
        frame2.grid_columnconfigure(6, weight=1)
        frame2.grid_rowconfigure(0, weight=1)
        frame2.grid_rowconfigure(1, weight=1)
        frame2.grid_rowconfigure(2, weight=1)
        frame2.grid_rowconfigure(3, weight=1)
        frame2.grid_rowconfigure(4, weight=1)
        frame2.grid_rowconfigure(5, weight=1)
        frame2.grid_rowconfigure(6, weight=1)
        frame2.grid_rowconfigure(7, weight=1)
        frame2.grid_rowconfigure(7, weight=1)
        frame2.grid_rowconfigure(8, weight=1)
        frame2.grid_rowconfigure(9, weight=1)
        frame2.grid_rowconfigure(10, weight=1)
        frame2.grid_rowconfigure(11, weight=1)
        frame2.grid_rowconfigure(12, weight=1)
        frame2.grid_rowconfigure(13, weight=1)
        frame2.grid_rowconfigure(14, weight=1)
        frame2.grid_rowconfigure(15, weight=1)
        frame2.grid_rowconfigure(16, weight=1)
        frame1.tkraise()
        checked_val = tk.BooleanVar()
        checked_val.set(checked)
        on_save_img_val = tk.BooleanVar()
        on_save_img_val.set(img_checked)
        model_val = tk.StringVar()
        global triggercheck_val
        triggercheck_val = tk.IntVar()
        # page2 = Frame(frame2, height=384, width=512, relief=GROOVE, borderwidth=2)
        # page1 = Frame(frame1, height=384, width=512, relief=GROOVE, borderwidth=2)
        # page2.grid(row=0, column=0, sticky="nsew")
        # page1.grid(row=0, column=0, sticky="nsew")
        panel2 = Label(frame2)
        panel1 = Label(frame1, height=384, width=512)
        panel2.grid(row=2, column=6, rowspan=10, padx=10, pady=10)
        panel1.grid(row=2, column=3, rowspan=10, padx=10, pady=10)
        global labelOK
        global labelNG
        global labelORIGIN
        labelOK = tk.Label(frame1, text="OK", background="green", font=('黑体', 40, 'bold'), padx=80, pady=80)
        labelNG = tk.Label(frame1, text="NG", background="red", font=('黑体', 40, 'bold'), padx=80, pady=80)
        labelORIGIN = tk.Label(frame1, text="AB", font=('黑体', 40, 'bold'), background="white", padx=80, pady=80)
        labelOK.grid(row=6, column=0, columnspan=2, sticky='wens', padx=30, pady=10)

        try:
            image = Image.open(parentdirsign)
        except:
            image = Image.open(current_file + 'logo.ico')
        resized_image = image.resize((512, 384), Image.LANCZOS)
        photo = ImageTk.PhotoImage(resized_image)
        canvas = tk.Canvas(frame1, width=photo.width(), height=photo.height())
        image_item = canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        canvas.grid(row=2, column=2, rowspan=10, padx=10, pady=10)
        # print(parentdir)
        ocr = CnOcr(rec_model_name='densenet_lite_136-gru', det_model_name='en_PP-OCRv3_det',
                    det_more_configs={'use_angle_clf': True})
        now = datetime.datetime.now()
        year = now.year
        month = now.month


        # 绑定下拉列表至设备信息索引
        def xFunc(event):
            global nSelCamIndex
            nSelCamIndex = TxtWrapBy("[", "]", device_list.get())


        # ch:枚举相机 | en:enum devices
        @logger.catch()
        def enum_devices():
            global deviceList
            global obj_cam_operation
            deviceList = MV_CC_DEVICE_INFO_LIST()
            tlayerType = MV_GIGE_DEVICE | MV_USB_DEVICE
            ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)
            if ret != 0:
                tkinter.messagebox.showerror('show error', 'enum devices fail! ret = ' + ToHexStr(ret))

            if deviceList.nDeviceNum == 0:
                tkinter.messagebox.showinfo('show info', 'find no device!')
            # print ("Find %d devices!" % deviceList.nDeviceNum)

            devList = []
            for i in range(0, deviceList.nDeviceNum):
                mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
                if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
                    # print ("\ngige device: [%d]" % i)
                    chUserDefinedName = ""
                    for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chUserDefinedName:
                        if 0 == per:
                            break
                        chUserDefinedName = chUserDefinedName + chr(per)
                    # print ("device model name: %s" % chUserDefinedName)

                    nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
                    nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
                    nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
                    nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
                    # print ("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
                    devList.append(
                        "[" + str(i) + "]GigE: " + chUserDefinedName + "(" + str(nip1) + "." + str(nip2) + "." + str(
                            nip3) + "." + str(nip4) + ")")
                elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
                    # print ("\nu3v device: [%d]" % i)
                    chUserDefinedName = ""
                    for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chUserDefinedName:
                        if per == 0:
                            break
                        chUserDefinedName = chUserDefinedName + chr(per)
                    # print ("device model name: %s" % chUserDefinedName)

                    strSerialNumber = ""
                    for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                        if per == 0:
                            break
                        strSerialNumber = strSerialNumber + chr(per)
                    # print ("user serial number: %s" % strSerialNumber)
                    devList.append("[" + str(i) + "]USB: " + chUserDefinedName + "(" + str(strSerialNumber) + ")")
            device_list["value"] = devList
            device_list.current(0)

            # ch:打开相机 | en:open device


        @logger.catch
        def open_device():
            global deviceList
            global nSelCamIndex
            global obj_cam_operation
            global b_is_run
            if True == b_is_run:
                tkinter.messagebox.showinfo('show info', 'Camera is Running!')
                return
            obj_cam_operation = CameraOperation(cam, deviceList, nSelCamIndex)
            ret = obj_cam_operation.Open_device()
            if 0 != ret:
                b_is_run = False
            else:
                model_val.set('continuous')
                b_is_run = True
            devicestatuclose.grid_forget()
            devicestatucl.grid_forget()
            devicestatuop.grid(row=1, column=1, padx=10, pady=10, sticky="w")
            devicestatuopen.grid(row=0, column=2, columnspan=2, padx=10, pady=10, sticky="w")


        # ch:开始取流 | en:Start grab image

        @logger.catch
        def start_grabbing():
            global obj_cam_operation
            obj_cam_operation.Start_grabbing(frame2, panel2)


        @logger.catch
        def start_grabbing1():
            global obj_cam_operation
            obj_cam_operation.Start_grabbing(frame1, panel1)


        # ch:停止取流 | en:Stop grab image
        @logger.catch
        def stop_grabbing():
            global obj_cam_operation
            obj_cam_operation.Stop_grabbing()


        @logger.catch
        def stop_grabbing1():
            global obj_cam_operation
            obj_cam_operation.Stop_grabbing()





        def contour_sort_key(contour):
            x, y, w, h = cv2.boundingRect(contour)
            # print(x, y, w, h ,'x, y, w, h ')
            # print(y, x, 'xyyyy')
            y_group = y // 40  # 除以10用于忽略10像素范围内的误差
            return (y_group, x, y)

        @logger.catch()
        def process_image(input_image_path, outputdir, threshold, kernel_threshold_x, kernel_threshold_y,
                          process_area_low_threshold,
                          process_area_threshold_high):
            print(threshold, kernel_threshold_x, kernel_threshold_y, process_area_low_threshold,
                  process_area_threshold_high)
            print(process_threshold_NUM, compare_threshold_NUM)
            global contour_info_list
            # 读取图像
            image = cv2.imread(input_image_path)

            # 转换为灰度图像
            gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

            # 对灰度图像进行二值化处理
            _, binary_image = cv2.threshold(gray_image, threshold, 255, cv2.THRESH_BINARY)
            # cv2.namedWindow("binary_image", cv2.WINDOW_NORMAL)
            # cv2.imshow("binary_image", binary_image)
            # cv2.waitKey(0)
            # 执行边缘检测，例如使用Canny算法
            edges = cv2.Canny(binary_image, 30, 255)
            # cv2.namedWindow("edges", cv2.WINDOW_NORMAL)
            # cv2.imshow("edges", edges)
            # cv2.waitKey(0)
            # 使用形态学操作来连接相邻的轮廓
            kernel = np.ones((kernel_threshold_y, kernel_threshold_x), np.uint8)
            closed_image = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            # cv2.namedWindow("closed_image", cv2.WINDOW_NORMAL)
            # cv2.imshow("closed_image", closed_image)
            # cv2.waitKey(0)
            # 寻找轮廓
            contours, _ = cv2.findContours(closed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 创建一个副本以绘制方框
            image_with_boxes = image.copy()

            # 创建一个列表来存储满足面积阈值条件的轮廓
            filtered_contours = []

            # 遍历轮廓
            for contour in contours:
                # 计算轮廓的面积
                area = cv2.contourArea(contour)
                # print(area)
                # 如果面积在阈值范围内，则添加到列表中
                if process_area_low_threshold < area < process_area_threshold_high:
                    filtered_contours.append(contour)
                    x, y, w, h = cv2.boundingRect(contour)
                    # 绘制方框
                    cv2.rectangle(image_with_boxes, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # 保存带有方框的图像
            output_image_path = os.path.join(imagepath, 'image_with_boxes.jpg')
            cv2.imwrite(output_image_path, image_with_boxes)
            # 列出文件夹中的所有文件
            file_list = os.listdir(outputdir)
            # 遍历文件列表并删除图片文件
            for filename in file_list:
                file_path = os.path.join(folder_path1, filename)
                if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):  # 指定图片文件扩展名
                    os.remove(file_path)

            # 保存满足条件的轮廓图像
            sorted_contours = sorted(filtered_contours, key=contour_sort_key)
            # print(sorted_contours, 'sorted_contours = sorted(filtered_contours, key=contour_sort_key)')
            for i, contour in enumerate(sorted_contours):
                x, y, w, h = cv2.boundingRect(contour)
                # print(x,y,'xxxxx')
                # print(contour_info_list[i]['h'])
                roi = image[y - 5:y + h + 5, x - 5:x + w + 5]
                filename = os.path.join(outputdir, f'cut_{i}.jpg')
                cv2.imwrite(filename, roi)
                contour_info_list.append({
                    'x': x - 5,
                    'y': y - 5,
                    'w': w + 5,
                    'h': h + 5,
                    'filename': f'cut_{i}.jpg'
                })

            if outputdir == folder_path1:
                return True
            else:
                return False


        @logger.catch()
        def process_image1(input_image_path, outputdir, threshold, kernel_threshold_x, kernel_threshold_y,
                          process_area_low_threshold,
                          process_area_threshold_high):
            # print(threshold, kernel_threshold_x, kernel_threshold_y, process_area_low_threshold,
            #       process_area_threshold_high)
            # print(process_threshold_NUM, compare_threshold_NUM)
            # 读取图像
            image = cv2.imread(input_image_path)

            # 转换为灰度图像
            gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

            # 对灰度图像进行二值化处理
            _, binary_image = cv2.threshold(gray_image, threshold, 255, cv2.THRESH_BINARY)
            cv2.namedWindow("binary_image", cv2.WINDOW_NORMAL)
            cv2.imshow("binary_image", binary_image)
            cv2.waitKey(0)
            # 执行边缘检测，例如使用Canny算法
            edges = cv2.Canny(binary_image, 30, 255)
            cv2.namedWindow("edges", cv2.WINDOW_NORMAL)
            cv2.imshow("edges", edges)
            cv2.waitKey(0)
            # 使用形态学操作来连接相邻的轮廓
            kernel = np.ones((kernel_threshold_y, kernel_threshold_x), np.uint8)
            closed_image = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            cv2.namedWindow("closed_image", cv2.WINDOW_NORMAL)
            cv2.imshow("closed_image", closed_image)
            cv2.waitKey(0)
            # 寻找轮廓
            contours, _ = cv2.findContours(closed_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 创建一个副本以绘制方框
            image_with_boxes = image.copy()

            # 创建一个列表来存储满足面积阈值条件的轮廓
            filtered_contours = []

            # 遍历轮廓
            for contour in contours:
                # 计算轮廓的面积
                area = cv2.contourArea(contour)
                # print(area)

                # 如果面积在阈值范围内，则添加到列表中
                if process_area_low_threshold < area < process_area_threshold_high:
                    filtered_contours.append(contour)
                    x, y, w, h = cv2.boundingRect(contour)
                    # 绘制方框
                    cv2.rectangle(image_with_boxes, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # 保存带有方框的图像
            output_image_path = os.path.join(imagepath, 'image_with_boxes.jpg')
            cv2.imwrite(output_image_path, image_with_boxes)
            # 列出文件夹中的所有文件
            file_list = os.listdir(outputdir)
            # 遍历文件列表并删除图片文件
            for filename in file_list:
                file_path = os.path.join(folder_path, filename)
                if filename.endswith((".jpg", ".jpeg", ".png", ".gif")):  # 指定图片文件扩展名
                    os.remove(file_path)
            # 保存满足条件的轮廓图像
            sorted_contours = sorted(filtered_contours, key=contour_sort_key)
            # print(sorted_contours,'sorted_contours = sorted(filtered_contours, key=contour_sort_key)')
            for i, contour in enumerate(sorted_contours):
                x, y, w, h = cv2.boundingRect(contour)
                # print(y, x, 'yxxxxx')
                try:
                    roi = image[y - 5:y + h + 5, x - 5:x + w + 5]
                    filename = os.path.join(outputdir, f'cut_{i}.jpg')
                    cv2.imwrite(filename, roi)
                    contour_info_list.append({
                        'x': x - 5,
                        'y': y - 5,
                        'w': w + 5,
                        'h': h + 5,
                        'filename': f'cut_{i}.jpg'
                    })
                except:
                    roi = image[y:y + h, x:x + w]
                    filename = os.path.join(outputdir, f'cut_{i}.jpg')
                    cv2.imwrite(filename, roi)
                    contour_info_list.append({
                        'x': x,
                        'y': y,
                        'w': w,
                        'h': h,
                        'filename': f'cut_{i}.jpg'
                    })

            if outputdir == folder_path1:
                return True
            else:
                return False


        @logger.catch()
        def compare_images(imageA_path, imageB_path,filename1,filename2, threshold):
            # 读取两张图片
            image1 = cv2.imread(imageA_path)
            image2 = cv2.imread(imageB_path)
            # plt.subplot(121), plt.imshow(image1),
            # plt.title('Matching Result'), plt.axis('off')
            # plt.subplot(122), plt.imshow(image2),
            # plt.title('Detected Point'), plt.axis('off')
            # plt.show()

            # 检查是否成功读取了图片
            if image1 is None or image2 is None:
                return False
            print(image1.shape, image2.shape, 'image1.shape,image2.shape1111111111')
            # 确保两张图片具有相同的尺寸
            if image1.shape != image2.shape:
                image1 = cv2.resize(image1, (image2.shape[1], image2.shape[0]))
            print(image1.shape, image2.shape, 'image1.shape,image2.shape222222222')



            # 将两张图片转换为灰度图像
            gray_image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
            gray_image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

            # 比较两张灰度图像的每个像素，找出不同之处
            difference = cv2.absdiff(gray_image1, gray_image2)
            # cv2.namedWindow(imageB_path, cv2.WINDOW_NORMAL)
            # cv2.imshow(imageB_path, difference)
            # cv2.waitKey(0)
            # 根据阈值创建二值图像
            _, thresholded_difference = cv2.threshold(difference, threshold, 255, cv2.THRESH_BINARY)
            # 计算白色像素数量
            white_pixel_count = np.sum(thresholded_difference == 255)
            black_pixel_count = np.sum(thresholded_difference == 0)
            image_area = gray_image1.shape[0] * gray_image1.shape[1]
            print(white_pixel_count, black_pixel_count, 'blacnandwhite')
            if white_pixel_count < 100:
                weighted_white_pixel_count = white_pixel_count
            else:
                white_pixel_weight = weight_threshold_NUM
                weighted_white_pixel_count = white_pixel_count * white_pixel_weight

            # 获取整张图片的像素数量
            total_pixel_count = thresholded_difference.size

            # 计算加权后的比例
            weighted_white_to_black_ratio = 1 - weighted_white_pixel_count / total_pixel_count

            # 查找轮廓
            contours, _ = cv2.findContours(thresholded_difference, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 在一张新的图像上绘制圆圈以标记不同之处
            marked_image = image1.copy()
            for contour in contours:
                area = cv2.contourArea(contour)
                # print(area)
                if area > 100:
                    x, y, w, h = cv2.boundingRect(contour)
                    # print(x, y, w, h, 'counter')
                    cv2.rectangle(image2, (x, y), (x + w, y + h), (0, 0, 255), 2)  # 使用红色绘制方框
                    cv2.imwrite(imageB_path, image2)
                    # for contour_info in contour_info_list:
                    #     filename = contour_info['filename']
                    #     # print(filename,'filename')
                    #     if filename == filename2:
                    #         print(filename,filename1,filename2,imageB_path,'filename,filename1,filename2')
                    #         image = cv2.imread(parentdirdemo)
                    #         x, y, w, h = contour_info['x'], contour_info['y'], contour_info['w'], contour_info['h']
                    #         roi = cv2.imread(imageB_path)
                    #         # 读取切割的轮廓图像
                    #         # 将切割的轮廓图像放回原位置
                    #         image[y:y + h, x:x + w] = roi
            # cv2.imwrite('marked_difference.jpg', marked_image)
            print('weighted_white_to_black_ratio', weighted_white_to_black_ratio)

        def read_all_img():
            for filename1 in os.listdir(folder_path):
                if filename1.endswith(('.jpg', '.jpeg', '.png')):  # 确保文件是图片文件
                    filepath1 = os.path.join(folder_path, filename1)
                    image = cv2.imread(filepath1)
                    image_list.append(image)

        @logger.catch()
        def read_files():
            # 遍历文件夹1中的图片
            imagetest=cv2.imread(parentdir)
            # 读取完整图片和局部图片
            full_image = cv2.imread(parentdirdemo)
            partial_match_and_paste = partial(match_and_extract_region, full_image=input_image_path2)

            # 使用进程池并行执行匹配和粘贴操作
            full_image = pool.map(partial_match_and_paste, input_image_path1)
            full_demo = process_images(full_image,imagetest)
            cv2.imwrite('marked_difference.jpg', full_demo)
            return full_demo,imagetest
        # @logger.catch()
        # def read_files():
        #     # 遍历文件夹1中的图片
        #     imagetest = cv2.imread(parentdir)
        #     # 读取完整图片和局部图片
        #     full_image = cv2.imread(parentdirdemo)
        #     for image in image_list:
        #         fulldemo = match_and_extract_region(image, full_image)
        #         # cv2.imshow('fulldemo',fulldemo)
        #     # imagetest[left_upper_NUM:right_lower_NUM, left_left_NUM:right_left_NUM] = fulldemo
        #     # cv2.imshow('imagetest',imagetest)
        #     # cv2.waitKey(0)
        #     imagetest[left_upper_NUM:right_lower_NUM, left_left_NUM:right_left_NUM] = fulldemo
        #     # cv2.imshow('imagetest',imagetest)
        #     # cv2.waitKey(0)
        #     cv2.imwrite(parentdirsign, imagetest)
        # 多线程处理图片
        def process_images(full_image,imagetest):
            start = time.time()
            # 调用函数并传入参数
            manager = Manager()
            shared_demo_image = manager.Value("i", 0)  # 创建共享的demo_image
            shared_demo_image.value = full_image
            # 使用进程池并行执行匹配和粘贴操作
            fulldemo = pool.starmap(match_and_extract_region, [(image_path, full_image) for image_path in image_list])
            # 处理匹配和粘贴的结果
            # for result in results:
            #     print(result)

            return fulldemo


        # ch:关闭设备 | Close device
        @logger.catch
        def close_device():
            global b_is_run
            global obj_cam_operation
            obj_cam_operation.Close_device()
            b_is_run = False
            # 清除文本框的数值
            text_frame_rate.delete(1.0, tk.END)
            text_exposure_time.delete(1.0, tk.END)
            text_gain.delete(1.0, tk.END)
            devicestatuopen.grid_forget()
            devicestatuop.grid_forget()
            devicestatucl.grid(row=1, column=1, padx=10, pady=10, sticky="w")
            devicestatuclose.grid(row=0, column=2, columnspan=2, padx=10, pady=10, sticky="w")


        # ch:设置触发模式 | en:set trigger mode
        @logger.catch
        def set_triggermode():
            global obj_cam_operation
            strMode = model_val.get()
            obj_cam_operation.Set_trigger_mode(strMode)


        # ch:设置触发命令 | en:set trigger software
        @logger.catch
        def trigger_once():
            global triggercheck_val
            global obj_cam_operation
            nCommand = triggercheck_val.get()
            obj_cam_operation.Trigger_once(nCommand)


        # ch:保存bmp图片 | en:save bmp image
        @logger.catch
        def bmp_save():
            global obj_cam_operation
            obj_cam_operation.b_save_bmp = True


        # ch:保存jpg图片 | en:save jpg image
        @logger.catch
        def jpg_save():
            global obj_cam_operation
            obj_cam_operation.b_save_jpg = True


        @logger.catch
        def getSerialdata():
            global ser1
            try:
                # print(COMGUNNUM)
                if ser1.is_open:
                    data = ser1.readline()
                    serialdata = data.decode().strip()
                    if (serialdata != ''):
                        serialdata = data.decode().strip()
                        # print(serialdata,'serialdata')
                        return serialdata
                    else:
                        time.sleep(0.1)
                else:
                    tkinter.messagebox.showinfo('show info', '串口未开启，将尝试为你打开串口')
                    ser1.open()
            except:
                ser1.close()
                tkinter.messagebox.showinfo('show info', '获取串口信息失败，串口已关闭！')


        @logger.catch  # 发送扫描命令
        def sendSerialOrder():
            try:
                if ser1.is_open:
                    hexStr = "03 53 80 ff 2a"
                    bytes_hex = bytes.fromhex(hexStr)
                    ser1.write(bytes_hex)
                else:
                    tkinter.messagebox.showinfo('show info', '串口未开启，将尝试为你打开串口')
                    ser1.open()
            except:
                ser1.close()
                tkinter.messagebox.showinfo('show info', '获取串口信息失败，串口已关闭！')


        # 获得图片OCR识别结果
        @logger.catch
        def get_sn_code():
            keywords = ['SN', 'PN']
            search_prefix = 'N:'
            sn_code = ''
            position = np.zeros((4, 2))

            res = ocr.ocr(parentdirdemo)

            if res:
                for i in res:
                    text = i.get('text', '')
                    if any(keyword in text for keyword in keywords) and len(text) >= 17:
                        text = ''.join(text.split())
                        sn_code = text.replace(" ", "")[-17:]
                        position = i.get('position', position)
                        break
                #需改进
                if not sn_code:
                    for i in res:
                        if 'text' in i and len(i['text']) == 17:
                            sn_code = i['text']
                            position = i['position']
                            break

                if sn_code:
                    sn_code = sn_code[0] + str(sn_code[1:]).replace('O', '0')
                else:
                    sn_code = '未识别到合适数据'
            else:
                sn_code = '没找到数据'

            return sn_code, position

        @logger.catch
        def jpg_save1(event=None):
            global obj_cam_operation
            obj_cam_operation.b_save_jpg1 = True

            return True


        @logger.catch
        def on_save_img(event=None):
            with open(saveImg, 'wb') as f:
                pickle.dump(on_save_img_val.get(), f)
            flag = on_save_img_val.get()
            global obj_cam_operation
            obj_cam_operation.flag = flag


        @logger.catch
        def file_not_exist(file_path):
            return not os.path.exists(file_path)


        @logger.catch
        def CountRows(file_name):
            try:
                df = pd.read_csv(file_name)
                ok_rows = df[df['result'] == 'OK']
                ok_count = len(ok_rows)
                ng_rows = df[df['result'] == 'NG']
                ng_count = len(ng_rows)
                all_count = len(df)
                return ok_count, ng_count, all_count
            except:
                ok_count = 0
                ng_count = 0
                all_count = 0
                return ok_count, ng_count, all_count


        @logger.catch
        def CountProducts():
            current_dir = os.path.dirname(__file__)
            file_path = os.path.abspath(os.path.join(current_dir, 'csv'))
            filenames = os.listdir(file_path)
            ok_result = 0
            ng_result = 0
            all_result = 0
            for file_name in filenames:
                file_name_path = file_path + '\\' + file_name
                ok_count, ng_count, all_count = CountRows(file_name_path)
                ok_result += ok_count
                ng_result += ng_count
                all_result += all_count
            try:
                Reliability_rate = ok_result / all_result
            except:
                Reliability_rate = 0
            percentage = "{:.2%}".format(Reliability_rate)
            return (all_result, ng_result, percentage)


        def write_to_csv(serial_data, sn_code, result):
            open_flag = file_not_exist(base_path('csv\{year}.{mon}.csv').format(year=year, mon=month).strip())
            with open(base_path('csv\{year}.{mon}.csv').format(year=year, mon=month), mode='a', encoding='utf-8',
                      newline='') as file:
                writer = csv.writer(file)
                column_names = ['serial_data', 'SnCode', 'result', 'costrat_time']
                if open_flag:
                    writer.writerow(column_names)
                costrat_time = datetime.datetime.now()
                data = [serial_data, sn_code, result, costrat_time]
                if result != 'continue':
                    writer.writerow(data)


        def save_counts_to_pickle(ok_count, ng_count, all_count):
            with open(picklename1, 'wb') as f:
                pickle.dump(ok_count, f)
                pickle.dump(ng_count, f)
                pickle.dump(all_count, f)


        @logger.catch
        def wait_for_response1():
            while True:
                serial_data = getSerialdata()
                if serial_data:
                    start = time.time()
                    # print('getSerialdata执行了一次')
                    flag = False
                    global last_result
                    result = ''
                    flag=jpg_save1()
                    time.sleep(0.3)
                    img_flag = get_pardemo(parentdir, left_left_NUM, left_upper_NUM, right_left_NUM, right_lower_NUM,
                                           parentdirdemo)
                    print(img_flag)
                    if img_flag:
                        SnCode, position = get_sn_code()
                        rect = canvas.create_rectangle(0, 0, canvas.winfo_width(), canvas.winfo_height(), fill='white',
                                                       outline='white')
                        canvas.update()
                        # start_update_img_task(position)
                        updateimg(position)

                        label_frame_rate4.config(text=last_result)
                        label_frame_rate4.grid(row=3, column=1, padx=10, pady=10, sticky="w")
                        label_frame_rate5.config(text=serial_data)
                        label_frame_rate5.grid(row=4, column=1, padx=10, pady=10, sticky="w")
                        label_frame_rate6.config(text=SnCode)
                        label_frame_rate6.grid(row=5, column=1, padx=10, pady=10, sticky="w")
                        canvas.delete(rect)
                        image1 = Image.open(parentdirsign)
                        photo1 = ImageTk.PhotoImage(image1.resize((512, 384), Image.LANCZOS))
                        canvas.itemconfig(image_item, image=photo1)
                        canvas.update()
                        # print("图片更新了")
                        if serial_data == last_result:
                            # print("请更换下一个")
                            flag = False
                            result = 'continue'
                            show_label(flag)
                        else:
                            if SnCode == serial_data:
                                flag = True
                                result = 'OK'
                                show_label(flag)
                            else:
                                flag = False
                                result = 'NG'
                                show_label(flag)
                        if checked_val.get():
                            write_to_csv(serial_data, SnCode, result)
                        else:
                            pass
                    else:
                        pass
                    last_result = serial_data
                    result_list = CountProducts()
                    ok_count = result_list[0]
                    ng_count = result_list[1]
                    all_count = result_list[2]
                    save_counts_to_pickle(ok_count, ng_count, all_count)
                    text_frame1_rate4.config(text=ok_count)
                    text_frame1_rate4.grid(row=13, column=1, padx=10, pady=10, sticky="w")
                    text_frame1_rate5.config(text=ng_count)
                    text_frame1_rate5.grid(row=14, column=1, padx=10, pady=10, sticky="w")
                    text_frame1_rate6.config(text=all_count)
                    text_frame1_rate6.grid(row=15, column=1, padx=10, pady=10, sticky="w")
                    end = time.time()
                    logger.info('Running time: %s Seconds' % (end - start))
                else:
                    pass



        @logger.catch
        def start_long_task():
            tkinter.messagebox.showinfo('show info', '已开始！')
            t = threading.Thread(target=wait_for_response1)
            t.daemon = True
            t.start()
            showimg()


        # @logger.catch
        # def start_update_img_task(position):
        #     t = threading.Thread(target=updateimg, args=(position,))
        #     t.daemon = True
        #     t.start()
        #     t.join()

        @logger.catch()
        def get_cut_params():
            left_left_text.delete("1.0", "end")
            left_left_text.insert('1.0', left_left_NUM)
            left_upper_text.delete("1.0", "end")
            left_upper_text.insert('1.0', left_upper_NUM)
            right_left_text.delete("1.0", "end")
            right_left_text.insert('1.0', right_left_NUM)
            right_lower_text.delete("1.0", "end")
            right_lower_text.insert('1.0', right_lower_NUM)


        # @logger.catch
        # def start_jpg_save1():
        #     t = threading.Thread(target=jpg_save1())
        #     t.daemon = True
        #     t.start()
        #     t.join()
        # @logger.catch
        # def start_reset_task():
        #     t=threading.Thread(target=reset_result)
        #     t.daemon=True
        #     t.start()

        @logger.catch
        def updateimg(position):
            start = time.time()
            # 遍历文件夹1中的图片
            imagetest = cv2.imread(parentdir)
            # 读取完整图片和局部图片
            full_image = cv2.imread(parentdirdemo)
            manager = Manager()
            shared_full_image = manager.Value("i", 0)  # 创建共享的full_image
            shared_full_image.value = full_image
            results = pool.starmap(match_and_extract_region, [(image, full_image) for image in image_list])

            # # full_demo = process_images(full_image, imagetest)
            # for result in results:
            #     cv2.imwrite('marked_difference.jpg', result)
            # # full_demo,imagetest=read_files()
            # if full_image is not None and np.all(position != 0):
            #     color = (0, 255, 0)
            #     x, y, w, h = cv2.boundingRect(position)
            #     # cv2.rectangle(image,(x-15,y-10),(x+w+5,y+h+5),color,6)
            #     cv2.rectangle(full_demo, (x, y), (x + w, y + h), color, 6)
            #     result_image = imagetest.copy()
            #     result_image[left_upper_NUM:right_lower_NUM, left_left_NUM:right_left_NUM] = full_demo
            #     # cv2.imshow('full_demo',full_demo)
            #     cv2.imwrite(parentdirsign, result_image)
            #     # cv2.waitKey(0)
            #     print('22222222222')
            # else:
            #     print('11111111')
            #     pass
            # end = time.time()
            # logger.info('updateimg time: %s Seconds' % (end - start))

        @logger.catch
        def showimg():
            canvas.grid(row=2, column=2, rowspan=10, padx=10, pady=10)


        @logger.catch
        def on_checked():
            with open(picklename, 'wb') as f:
                pickle.dump(checked_val.get(), f)


        @logger.catch
        def get_parameter():
            global obj_cam_operation
            obj_cam_operation.Get_parameter()
            text_frame_rate.delete(1.0, tk.END)
            text_frame_rate.insert(1.0, obj_cam_operation.frame_rate)
            text_exposure_time.delete(1.0, tk.END)
            text_exposure_time.insert(1.0, obj_cam_operation.exposure_time)
            text_gain.delete(1.0, tk.END)
            text_gain.insert(1.0, obj_cam_operation.gain)


        @logger.catch
        def set_parameter():
            global obj_cam_operation
            obj_cam_operation.exposure_time = text_exposure_time.get(1.0, tk.END)
            obj_cam_operation.exposure_time = obj_cam_operation.exposure_time.rstrip("\n")
            obj_cam_operation.gain = text_gain.get(1.0, tk.END)
            obj_cam_operation.gain = obj_cam_operation.gain.rstrip("\n")
            obj_cam_operation.frame_rate = text_frame_rate.get(1.0, tk.END)
            obj_cam_operation.frame_rate = obj_cam_operation.frame_rate.rstrip("\n")
            obj_cam_operation.Set_parameter(obj_cam_operation.frame_rate, obj_cam_operation.exposure_time,
                                            obj_cam_operation.gain)


        xVariable = tkinter.StringVar()
        device_list = ttk.Combobox(frame2, textvariable=xVariable)
        device_list.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="we")
        # device_list.bind("<<ComboboxSelected>>", xFunc)
        devicestatuopen = tk.Label(frame2, text='设备处于打开状态,请直接点击开始抓取', bg='skyblue', width=30, height=1)
        devicestatuclose = tk.Label(frame2, text='设备处于关闭状态,请点击打开设备再点击开始抓取', bg='skyblue',
                                    width=40, height=1)
        devicestatucl = tk.Label(frame1, text='设备已关闭', bg='skyblue', width=10, height=1)
        devicestatuop = tk.Label(frame1, text='设备已开启', bg='skyblue', width=10, height=1)
        # 需要解开
        enum_devices()
        time.sleep(1)
        open_device()
        start_grabbing1()
        # commonuser
        device_list1 = ttk.Combobox(frame1, textvariable=xVariable)
        device_list1.grid(column=0, row=0, columnspan=2, padx=10, pady=10, sticky="we")
        # device_list1.bind("<<ComboboxSelected>>", xFunc)

        label_exposure_time = tk.Label(frame2, text='曝光时间', width=15, height=1)
        label_exposure_time.grid(row=7, column=0, padx=10, pady=10, sticky="we")
        text_exposure_time = tk.Text(frame2, width=15, height=1)
        text_exposure_time.grid(row=7, column=1, padx=10, pady=10, sticky="we")

        label_gain = tk.Label(frame2, text='增益', width=15, height=1)
        label_gain.grid(row=8, column=0, padx=10, pady=10, sticky="we")
        text_gain = tk.Text(frame2, width=15, height=1)
        text_gain.grid(row=8, column=1, padx=10, pady=10, sticky="we")

        label_frame_rate = tk.Label(frame2, text='帧速率', width=15, height=1)
        label_frame_rate.grid(row=9, column=0, padx=10, pady=10, sticky="we")
        text_frame_rate = tk.Text(frame2, width=15, height=1)
        text_frame_rate.grid(row=9, column=1, padx=10, pady=10, sticky="we")

        btn_enum_devices = tk.Button(frame2, text='发现设备', width=35, height=1,
                                     command=enum_devices)  # , command=enum_devices
        btn_enum_devices.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="we")

        # commonuser
        btn_open_device = tk.Button(frame2, text='打开设备', width=15, height=1,
                                    command=open_device)  # , command=open_device
        btn_open_device.grid(row=2, column=0, padx=10, pady=10, sticky="we")

        btn_close_device = tk.Button(frame2, text='关闭设备', width=15, height=1,
                                     command=close_device)  # , command=close_device
        btn_close_device.grid(row=2, column=1, padx=10, pady=10, sticky="we")

        radio_continuous = tk.Radiobutton(frame2, text='持续性抓取', variable=model_val, value='continuous', width=15,
                                          height=1, command=set_triggermode)  # , command=set_triggermode
        radio_continuous.grid(row=3, column=0, padx=10, pady=10, sticky="we")

        radio_trigger = tk.Radiobutton(frame2, text='触发模式', variable=model_val, value='triggermode', width=15,
                                       height=1, command=set_triggermode)  # , command=set_triggermode
        radio_trigger.grid(row=3, column=1, padx=10, pady=10, sticky="we")
        model_val.set(1)

        btn_start_grabbing = tk.Button(frame2, text='开始抓取', width=15, height=1,
                                       command=start_grabbing)  # , command=start_grabbing
        btn_start_grabbing.grid(row=4, column=0, padx=10, pady=10, sticky="we")

        btn_stop_grabbing = tk.Button(frame2, text='停止抓取', width=15, height=1,
                                      command=stop_grabbing)  # , command=stop_grabbing
        btn_stop_grabbing.grid(row=4, column=1, padx=10, pady=10, sticky="we")

        checkbtn_trigger_software = tk.Checkbutton(frame2, text='Tigger by Software', variable=triggercheck_val,
                                                   onvalue=1, offvalue=0)
        checkbtn_trigger_software.grid(row=5, column=0, padx=10, pady=10, sticky="we")
        btn_trigger_once = tk.Button(frame2, text='触发一次', width=15, height=1,
                                     command=trigger_once)  # , command=trigger_once
        btn_trigger_once.grid(row=5, column=1, padx=10, pady=10, sticky="we")

        btn_save_bmp = tk.Button(frame2, text='Save as BMP', width=15, height=1, command=bmp_save)  # , command=bmp_save
        btn_save_bmp.grid(row=6, column=0, padx=10, pady=10, sticky="we")
        btn_save_jpg = tk.Button(frame2, text='Save as JPG', width=15, height=1, command=jpg_save)  # , command=jpg_save
        btn_save_jpg.grid(row=6, column=1, padx=10, pady=10, sticky="we")
        label_frame1_all = tk.Label(frame1, text='总数量：', bg='skyblue', width=8, height=1, anchor='e')
        label_frame1_ng = tk.Label(frame1, text='不良数量：', bg='skyblue', width=8, height=1, anchor='e')
        label_frame1_per = tk.Label(frame1, text='可靠率：', bg='skyblue', width=8, height=1, anchor='e')
        text_frame1_rate4 = tk.Label(frame1, text='', width=20, height=1, anchor='w', bg='red')
        text_frame1_rate4.grid(row=13, column=1, padx=10, pady=10, sticky="w")
        text_frame1_rate5 = tk.Label(frame1, text='', width=16, height=1, anchor='w')
        text_frame1_rate6 = tk.Label(frame1, text='', width=8, height=1, anchor='w')
        label_frame1_all.grid(row=13, column=0, padx=10, pady=10, sticky="e")
        label_frame1_ng.grid(row=14, column=0, padx=10, pady=10, sticky="e")
        label_frame1_per.grid(row=15, column=0, padx=10, pady=10, sticky="e")
        try:
            with open(picklename1, 'rb') as f:
                ok_count = pickle.load(f)
                ng_count = pickle.load(f)
                all_count = pickle.load(f)
                text_frame1_rate4.config(text=ok_count)
                text_frame1_rate4.grid(row=13, column=1, padx=10, pady=10, sticky="nsew")
                text_frame1_rate5.config(text=ng_count)
                text_frame1_rate5.grid(row=14, column=1, padx=10, pady=10, sticky="nsew")
                text_frame1_rate6.config(text=all_count)
                text_frame1_rate6.grid(row=15, column=1, padx=10, pady=10, sticky="nsew")
        except:
            result_list = ['0', '0', '0%']
            text_frame1_rate4.config(text=result_list[0])
            text_frame1_rate4.grid(row=13, column=1, padx=10, pady=10, sticky="nsew")
            text_frame1_rate5.config(text=result_list[1])
            text_frame1_rate5.grid(row=14, column=1, padx=10, pady=10, sticky="nsew")
            text_frame1_rate6.config(text=result_list[2])
            text_frame1_rate6.grid(row=15, column=1, padx=10, pady=10, sticky="nsew")

        label_frame_rate1 = tk.Label(frame1, text='上一个SN：', font=('黑体', 12, "bold"), bg='skyblue', height=1)
        label_frame_rate2 = tk.Label(frame1, text='  本次SN：', font=('黑体', 12, "bold"), bg='skyblue', height=1)
        label_frame_rate3 = tk.Label(frame1, text=' OCR结果：', font=('黑体', 12, "bold"), bg='skyblue', height=1)
        label_frame_rate4 = tk.Label(frame1, text='', font=('Arial', 12), width=18, height=1, bg='red')
        label_frame_rate5 = tk.Label(frame1, text='', font=('Arial', 12), width=18, height=1)
        label_frame_rate6 = tk.Label(frame1, text='', font=('Arial', 12), width=18, height=1)
        # label_frame_rate4.config(text='A2001021448325486')
        label_frame_rate4.grid(row=3, column=1, pady=10, sticky="nsew")
        label_frame_rate1.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        label_frame_rate2.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        label_frame_rate3.grid(row=5, column=0, padx=10, pady=10, sticky="nsew")
        text_frame1_tips = tk.Label(frame1,
                                    text='如果点击开始后扫码枪为一天内的第一次开机，请等待扫码枪开机声音结束后再次点击开始比对按钮',
                                    font=(12), width=90, height=1, anchor='w')
        text_frame1_tips.grid(row=13, column=2, columnspan=2, sticky="w", padx=10, pady=10, )

        checkbutton = tk.Checkbutton(frame1, text="保存比对数据信息", variable=checked_val, state=DISABLED)
        checkbutton.grid(row=2, column=0, padx=10, pady=10, sticky="we")
        checkbutton = tk.Checkbutton(frame2, text="保存比对数据信息", variable=checked_val,
                                     command=on_checked)  # , command=on_checked
        checkbutton.grid(row=11, column=0, padx=10, pady=10, sticky="we")

        leidiaobutton = tk.Checkbutton(frame1, text="镭雕机模式", state=DISABLED)
        leidiaobutton.grid(row=2, column=1, padx=10, pady=10, sticky="we")
        leidiaobutton = tk.Checkbutton(frame2, text="镭雕机模式")  # , command=on_checked
        leidiaobutton.grid(row=11, column=1, padx=10, pady=10, sticky="we")


        @logger.catch
        def getCOMS():
            all_comports = serial.tools.list_ports.comports()
            available_ports = []
            for comport in all_comports:
                available_ports.append(comport.device)
            return available_ports


        COMGUN = tk.Label(frame2, text='扫码枪端口', width=8, height=1)
        COMGUN.grid(row=12, column=0, padx=10, pady=10, sticky="we")
        xVariableCOM = tkinter.StringVar(value=COMGUNNUM)
        COMGUN_list = ttk.Combobox(frame2, textvariable=xVariableCOM, width=8)


        @logger.catch
        def changeCOMS(event):
            global COMGUNNUM
            global previous_COMGUNNUM
            COMGUNNUM = xVariableCOM.get()
            previous_COMGUNNUM = COMGUNNUM


        COMLIST = getCOMS()
        COMGUN_list['value'] = COMLIST
        COMGUN_list.grid(row=12, column=1, padx=10, pady=10, sticky="we")
        COMGUN_list.bind("<<ComboboxSelected>>", changeCOMS)


        @logger.catch
        def comportfunction():
            global COMGUNNUM, ser1
            COMGUNNUM = xVariableCOM.get()
            if COMGUNNUM:  # and COMSIGNAL
                with open(compickle, 'wb') as f:
                    pickle.dump(COMGUNNUM, f)
                    # pickle.dump(COMSIGNALNUM,f)
            else:
                tk.messagebox.showerror('show error', "请选择端口！")
            threshold_confirm()
            try:
                ser1.close()
                ser1 = serial.Serial(COMGUNNUM, 9600, timeout=0.5)
            except serial.SerialException as e:
                tkinter.messagebox.showinfo('show info', '串口打开失败，请选择端口后重试！')
            except Exception as e:
                pass


        combutton = tk.Button(frame2, text='提交', bg='skyblue', width=10, height=1,
                              command=comportfunction)  # , command=comportfunction
        combutton.grid(row=12, column=2, padx=10, pady=10, sticky="we")
        btn_start_jpg = tk.Button(frame1, text='开始比对', width=15, height=1,
                                  command=start_long_task)  # , command=start_long_task
        btn_start_jpg.grid(row=1, column=0, padx=10, pady=10, sticky="we")
        videostream = tk.Label(frame1, text='实时视频流', font=('黑体', 12, "bold"), width=20, height=1)
        videostream.grid(row=1, column=3, padx=10, pady=10)
        picturescreen = tk.Label(frame1, text='本次样本', font=('黑体', 12, "bold"), width=20, height=1)
        picturescreen.grid(row=1, column=2, padx=10, pady=10)
        btn_get_parameter = tk.Button(frame2, text='获取参数', width=15, height=1,
                                      command=get_parameter)  # , command=get_parameter
        btn_get_parameter.grid(row=10, column=0, padx=10, pady=10, sticky="we")
        btn_set_parameter = tk.Button(frame2, text='设置参数', width=15, height=1,
                                      command=set_parameter)  # , command=set_parameter
        btn_set_parameter.grid(row=10, column=1, padx=10, pady=10, sticky="we")


        @logger.catch
        def look_picture():
            img = cv2.imread(parentdir)
            plt.subplot(111), plt.imshow(img),
            plt.title('Detected Point'), plt.axis('off')
            plt.show()


        @logger.catch
        def add_cuts_picture():
            global process_threshold_NUM, process_kernel_x_threshold_NUM,process_kernel_y_threshold_NUM, process_area_low_threshold_NUM,process_area_threshold_high_NUM
            get_pardemo(parentdir, left_left_NUM, left_upper_NUM, right_left_NUM, right_lower_NUM, parentdirdemo)
            flag = process_image1(parentdirdemo, folder_path, process_threshold_NUM, process_kernel_x_threshold_NUM,
                                 process_kernel_y_threshold_NUM, process_area_low_threshold_NUM,
                                 process_area_threshold_high_NUM)
            # print(parentdirdemo, folder_path, process_threshold_NUM, process_kernel_x_threshold_NUM,
            #       process_kernel_y_threshold_NUM, process_area_low_threshold_NUM, process_area_threshold_high_NUM)
            read_all_img()


        @logger.catch
        def show_cut(path, left, upper, right, lower):
            """
                原图与所截区域相比较
            :param path: 图片路径
            :param left: 区块左上角位置的像素点离图片左边界的距离
            :param upper：区块左上角位置的像素点离图片上边界的距离
            :param right：区块右下角位置的像素点离图片左边界的距离
            :param lower：区块右下角位置的像素点离图片上边界的距离
             故需满足：lower > upper、right > left
            """

            img = cv2.imread(path)

            plt.figure("Image Contrast")
            plt.subplot(1, 2, 1)
            plt.title('origin')
            plt.imshow(img)  # 展示图片的颜色会改变
            plt.axis('off')

            cropped = img[upper:lower, left:right]

            plt.subplot(1, 2, 2)
            plt.title('roi')
            plt.imshow(cropped)
            plt.axis('off')
            plt.show()


        @logger.catch
        def get_pardemo(path, left, upper, right, lower, save_path):
            """
                所截区域图片保存
            :param path: 图片路径
            :param left: 区块左上角位置的像素点离图片左边界的距离
            :param upper：区块左上角位置的像素点离图片上边界的距离
            :param right：区块右下角位置的像素点离图片左边界的距离
            :param lower：区块右下角位置的像素点离图片上边界的距离
             故需满足：lower > upper、right > left
            :param save_path: 所截图片保存位置
            """
            # print(path, left, upper, right, lower, save_path)
            img = cv2.imread(path)  # 打开图像
            cropped = img[upper:lower, left:right]
            # 保存截取的图片
            cv2.namedWindow("cropped", cv2.WINDOW_NORMAL)
            cv2.imshow("cropped", cropped)
            cv2.waitKey(0)
            flag = cv2.imwrite(save_path, cropped)
            return flag


        @logger.catch
        def image_cut_save(path, left, upper, right, lower, save_path):
            """
                所截区域图片保存
            :param path: 图片路径
            :param left: 区块左上角位置的像素点离图片左边界的距离
            :param upper：区块左上角位置的像素点离图片上边界的距离
            :param right：区块右下角位置的像素点离图片左边界的距离
            :param lower：区块右下角位置的像素点离图片上边界的距离
             故需满足：lower > upper、right > left
            :param save_path: 所截图片保存位置
            """
            img = cv2.imread(path)  # 打开图像
            cropped = img[upper:lower, left:right]
            # 保存截取的图片
            cv2.imwrite(save_path, cropped)


        @logger.catch
        def add_Template_picture():
            pic_save_dir_path = parentdirdemo
            left_left_NUM = int(left_left_text.get("1.0", "end-1c"))
            left_upper_NUM = int(left_upper_text.get("1.0", "end-1c"))
            right_left_NUM = int(right_left_text.get("1.0", "end-1c"))
            right_lower_NUM = int(right_lower_text.get("1.0", "end-1c"))
            if left_left_NUM == '' or left_upper_NUM == '' or right_left_NUM == '' or right_lower_NUM == '':
                messagebox.showinfo(title='提示', message='请输入模板图片位置')
            else:
                with open(comparea, 'wb') as f:
                    pickle.dump(left_left_NUM, f)
                    pickle.dump(left_upper_NUM, f)
                    pickle.dump(right_left_NUM, f)
                    pickle.dump(right_lower_NUM, f)
                show_cut(parentdir, left_left_NUM, left_upper_NUM, right_left_NUM, right_lower_NUM)
                image_cut_save(parentdir, left_left_NUM, left_upper_NUM, right_left_NUM, right_lower_NUM,
                               pic_save_dir_path)


        @logger.catch
        def look_this_picture():
            try:
                selected_item = listbox.get(listbox.curselection())
                if selected_item:
                    file_path = os.path.join(folder_path, selected_item)
                    img = cv2.imread(file_path)
                    image_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    plt.subplot(111), plt.imshow(image_rgb),
                    plt.title(selected_item), plt.axis('off')
                    plt.show()
            except:
                messagebox.showinfo(title='提示', message='请选择图片!')


        @logger.catch
        def delete_this_picture():
            try:
                selected_indices = listbox.curselection()
                if selected_indices:
                    selected_item = listbox.get(selected_indices[0])  # 获取第一个选定的项目
                    file_path = os.path.join(folder_path, selected_item)
                    try:
                        os.remove(file_path)
                        listbox.delete(selected_indices)  # 从列表框中删除选定的项目
                        messagebox.showinfo("删除成功", f"文件 {selected_item} 已删除")
                    except Exception as e:
                        messagebox.showerror("删除失败", f"无法删除文件 {selected_item}: {str(e)}")
            except:
                messagebox.showinfo(title='提示', message='请选择图片!')


        @logger.catch
        def refresh():
            listbox.delete(0, tk.END)
            image_files = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            # 将图片文件名添加到列表框中
            for file in image_files:
                listbox.insert(tk.END, file)


        @logger.catch
        def on_mouse(event, x, y, flags, param, file_name):
            global screen_img, point1, point2, screenshotNum, left_left_NUM, left_upper_NUM, right_left_NUM, right_lower_NUM
            img2 = screen_img.copy()
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
                if file_name == imagepath:
                    # left_left_NUM = cut_Pos[0][0]
                    # left_upper_NUM = cut_Pos[1][0]
                    # right_left_NUM = cut_Pos[0][1]
                    # right_lower_NUM = cut_Pos[1][1]
                    # print(left_left_NUM, left_upper_NUM, right_left_NUM, right_lower_NUM)
                    # with open(comparea, 'wb') as f:
                    #     pickle.dump(left_left_NUM, f)
                    #     pickle.dump(left_upper_NUM, f)
                    #     pickle.dump(right_left_NUM, f)
                    #     pickle.dump(right_lower_NUM, f)
                    cv2.namedWindow('image', cv2.WINDOW_NORMAL)
                    cv2.imshow('image', screen_img[cut_Pos[1][0]:cut_Pos[1][1], cut_Pos[0][0]:cut_Pos[0][1]])
                    folder_name = file_name + f"\\demo.jpg"
                else:
                    cv2.namedWindow('image', cv2.WINDOW_NORMAL)
                    cv2.imshow('image', screen_img[cut_Pos[1][0]:cut_Pos[1][1], cut_Pos[0][0]:cut_Pos[0][1]])
                    folder_name = file_name + f"\\screen_img_{screenshotNum + 1}.jpg"
                    screenshotNum += 1
                cv2.imwrite(folder_name, screen_img[cut_Pos[1][0]:cut_Pos[1][1], cut_Pos[0][0]:cut_Pos[0][1]])


        @logger.catch
        def screen_shot(file):
            global screenshotNum
            global screen_img
            screen_img = cv2.imread('image\\test.jpg')
            cv2.namedWindow('image', cv2.WINDOW_NORMAL)
            on_mouse_callback = partial(on_mouse, file_name=file)
            cv2.setMouseCallback('image', on_mouse_callback)
            cv2.imshow('image', screen_img)
            cv2.waitKey(0)


        @logger.catch
        def threshold_confirm():
            global process_threshold_NUM, compare_threshold_NUM, process_kernel_x_threshold_NUM,\
                process_kernel_y_threshold_NUM, process_area_low_threshold_NUM, process_area_threshold_high_NUM,\
                weight_threshold_NUM,pattern_compare_threshold_NUM, image_threading_NUM,different_threshold_NUM
            param1 = process_binary_threshold_text.get(1.0, tk.END)
            param2 = compare_binary_threshold_text.get(1.0, tk.END)
            param3 = process_kernel_x_threshold_text.get(1.0, tk.END)
            param4 = process_kernel_y_threshold_text.get(1.0, tk.END)
            param5 = process_area_low_threshold_text.get(1.0, tk.END)
            param6 = process_area_threshold_high_text.get(1.0, tk.END)
            param7 = weight_threshold_text.get(1.0, tk.END)
            param8 = pattern_compar_threshold_text.get(1.0, tk.END)
            param9 = image_threading_text.get(1.0, tk.END)
            param10 = different_threshold_text.get(1.0, tk.END)

            params = (param1, param2, param3, param4, param5, param6, param7,param8,param9,param10)  # 将三个参数打包成元组
            if params:
                with open(thresholdpickle, "wb") as f:
                    pickle.dump(params, f)
                process_threshold_NUM = int(param1)
                compare_threshold_NUM = int(param2)
                process_kernel_x_threshold_NUM = int(param3)
                process_kernel_y_threshold_NUM = int(param4)
                process_area_low_threshold_NUM = int(param5)
                process_area_threshold_high_NUM = int(param6)
                weight_threshold_NUM = int(param7)
                pattern_compare_threshold_NUM = int(param8)
                image_threading_NUM = int(param9)
                different_threshold_NUM = int(param10)
                tkinter.messagebox.showinfo('show info', '提交成功！')
            else:
                tk.messagebox.showerror('show error', "填写数据！")


        btn_look_picture = tk.Button(frame2, text='查看目标图片', width=10, height=1, command=look_picture)  #
        btn_look_picture.grid(row=2, column=4, padx=10, pady=10, sticky="w")
        btn_add_picture = tk.Button(frame2, text='生成比对模板', width=12, height=1, command=add_cuts_picture)  #
        btn_add_picture.grid(row=2, column=5, padx=10, pady=10, sticky="w")
        btn_add_template = tk.Button(frame2, text='添加模板图片', width=12, height=1, command=add_Template_picture)  #
        btn_add_template.grid(row=6, column=2, padx=10, pady=10, sticky="wens")
        btn_screenshot = tk.Button(frame2, text='目标位置截图', width=12, height=1,
                                   command=lambda: screen_shot(folder_path))  #
        btn_screenshot.grid(row=6, column=3, padx=10, pady=10, sticky="wens")
        btn_refresh = tk.Button(frame2, text='刷新', width=12, height=1, command=refresh)  #
        btn_refresh.grid(row=6, column=4, padx=10, pady=10, sticky="wens")
        # 图片截取功能
        left_left = tk.Label(frame2, text='左上距左', width=8, height=1)
        left_left.grid(row=2, column=2, padx=10, pady=10, sticky="e")
        left_left_text = tk.Text(frame2, width=10, height=1)
        left_left_text.grid(row=2, column=3, padx=10, pady=10, sticky="w")
        # 图片截取功能
        left_upper = tk.Label(frame2, text='左上距上', width=8, height=1)
        left_upper.grid(row=3, column=2, padx=10, pady=10, sticky="e")
        left_upper_text = tk.Text(frame2, width=10, height=1)
        left_upper_text.grid(row=3, column=3, padx=10, pady=10, sticky="w")

        # 图片截取功能
        right_left = tk.Label(frame2, text='右下距左', width=8, height=1)
        right_left.grid(row=4, column=2, padx=10, pady=10, sticky="e")
        right_left_text = tk.Text(frame2, width=10, height=1)
        right_left_text.grid(row=4, column=3, padx=10, pady=10, sticky="w")

        # 图片截取功能
        right_lower = tk.Label(frame2, text='右下距上', width=8, height=1)
        right_lower.grid(row=5, column=2, padx=10, pady=10, sticky="e")
        right_lower_text = tk.Text(frame2, width=10, height=1)
        right_lower_text.grid(row=5, column=3, padx=10, pady=10, sticky="w")

        # 阈值
        process_binary_threshold = tk.Label(frame2, text='图片二值化阈值', width=10, height=1)
        process_binary_threshold.grid(row=8, column=2, padx=10, pady=10, sticky="we")
        process_binary_threshold_text = tk.Text(frame2, width=10, height=1)
        process_binary_threshold_text.grid(row=8, column=3, padx=10, pady=10, sticky="w")

        process_kernel_x_threshold = tk.Label(frame2, text='图片处理卷积核横向', width=15, height=1)
        process_kernel_x_threshold.grid(row=9, column=2, padx=10, pady=10, sticky="we")
        process_kernel_x_threshold_text = tk.Text(frame2, width=10, height=1)
        process_kernel_x_threshold_text.grid(row=9, column=3, padx=10, pady=10, sticky="w")

        process_kernel_y_threshold = tk.Label(frame2, text='图片处理卷积核纵向', width=15, height=1)
        process_kernel_y_threshold.grid(row=10, column=2, padx=10, pady=10, sticky="we")
        process_kernel_y_threshold_text = tk.Text(frame2, width=10, height=1)
        process_kernel_y_threshold_text.grid(row=10, column=3, padx=10, pady=10, sticky="w")

        pattern_compar_threshold = tk.Label(frame2, text='图案比对阈值', width=10, height=1)
        pattern_compar_threshold.grid(row=7, column=4, padx=10, pady=10, sticky="we")
        pattern_compar_threshold_text = tk.Text(frame2, width=10, height=1)
        pattern_compar_threshold_text.grid(row=7, column=5, padx=10, pady=10, sticky="w")

        process_area_low_threshold = tk.Label(frame2, text='图片最小保留面积', width=10, height=1)
        process_area_low_threshold.grid(row=8, column=4, padx=10, pady=10, sticky="we")
        process_area_low_threshold_text = tk.Text(frame2, width=10, height=1)
        process_area_low_threshold_text.grid(row=8, column=5, padx=10, pady=10, sticky="w")

        process_area_threshold_high = tk.Label(frame2, text='图片最大保留面积', width=10, height=1)
        process_area_threshold_high.grid(row=9, column=4, padx=10, pady=10, sticky="we")
        process_area_threshold_high_text = tk.Text(frame2, width=10, height=1)
        process_area_threshold_high_text.grid(row=9, column=5, padx=10, pady=10, sticky="w")

        compare_binary_threshold = tk.Label(frame2, text='不同像素二值化阈值', width=10, height=1)
        compare_binary_threshold.grid(row=10, column=4, padx=10, pady=10, sticky="we")
        compare_binary_threshold_text = tk.Text(frame2, width=10, height=1)
        compare_binary_threshold_text.grid(row=10, column=5, padx=10, pady=10, sticky="w")

        weight_threshold = tk.Label(frame2, text='白色像素权值', width=10, height=1)
        weight_threshold.grid(row=11, column=4, padx=10, pady=10, sticky="we")
        weight_threshold_text = tk.Text(frame2, width=10, height=1)
        weight_threshold_text.grid(row=11, column=5, padx=10, pady=10, sticky="w")

        image_threading = tk.Label(frame2, text='线程数', width=10, height=1)
        image_threading.grid(row=12, column=4, padx=10, pady=10, sticky="we")
        image_threading_text = tk.Text(frame2, width=10, height=1)
        image_threading_text.grid(row=12, column=5, padx=10, pady=10, sticky="w")

        different_threshold = tk.Label(frame2, text='不同像素阈值', width=10, height=1)
        different_threshold.grid(row=13, column=4, padx=10, pady=10, sticky="we")
        different_threshold_text = tk.Text(frame2, width=10, height=1)
        different_threshold_text.grid(row=13, column=5, padx=10, pady=10, sticky="w")
        # thresholdbutton = tk.Button(frame2, text='提交', bg='skyblue', width=10, height=1,
        #                             command=threshold_confirm)  #
        # thresholdbutton.grid(row=8, column=4, padx=10, pady=10, sticky="w")
        get_cut_params()
        try:
            read_all_img()
        except:
            pass
        try:
            with open(thresholdpickle, "rb") as f:
                loaded_params = pickle.load(f)
                param1_loaded, param2_loaded, param3_loaded, param4_loaded, param5_loaded, param6_loaded, param7_loaded,param8_loaded,param9_loaded,param10_loaded = loaded_params
                process_binary_threshold_text.delete("1.0", "end")  # 清空Text组件
                process_binary_threshold_text.insert("1.0", param1_loaded)
                process_kernel_x_threshold_text.delete("1.0", "end")
                process_kernel_x_threshold_text.insert("1.0", param3_loaded)
                process_kernel_y_threshold_text.delete("1.0", "end")
                process_kernel_y_threshold_text.insert("1.0", param4_loaded)
                process_area_low_threshold_text.delete("1.0", "end")  # 清空Text组件
                process_area_low_threshold_text.insert("1.0", param5_loaded)
                process_area_threshold_high_text.delete("1.0", "end")
                process_area_threshold_high_text.insert("1.0", param6_loaded)
                compare_binary_threshold_text.delete("1.0", "end")
                compare_binary_threshold_text.insert("1.0", param2_loaded)
                weight_threshold_text.delete("1.0", "end")
                weight_threshold_text.insert("1.0", param7_loaded)
                pattern_compar_threshold_text.delete("1.0", "end")
                pattern_compar_threshold_text.insert("1.0", param8_loaded)
                image_threading_text.delete("1.0", "end")
                image_threading_text.insert("1.0", param9_loaded)
                different_threshold_text.delete("1.0", "end")
                different_threshold_text.insert("1.0", param10_loaded)
        except FileNotFoundError:
            process_threshold_NUM = 200
            compare_threshold_NUM = 60
            process_kernel_x_threshold_NUM = 75
            process_kernel_y_threshold_NUM = 1
            process_area_low_threshold_NUM = 4000
            process_area_threshold_high_NUM = 250000
            weight_threshold_NUM = 10
            pattern_compare_threshold_NUM=30
            image_threading_NUM = 9
            different_threshold_NUM = 200
            process_binary_threshold_text.delete("1.0", "end")  # 清空Text组件
            process_binary_threshold_text.insert("1.0", process_threshold_NUM)
            process_kernel_x_threshold_text.delete("1.0", "end")
            process_kernel_x_threshold_text.insert("1.0", process_kernel_x_threshold_NUM)
            process_kernel_y_threshold_text.delete("1.0", "end")
            process_kernel_y_threshold_text.insert("1.0", process_kernel_y_threshold_NUM)
            process_area_low_threshold_text.delete("1.0", "end")  # 清空Text组件
            process_area_low_threshold_text.insert("1.0", process_area_low_threshold_NUM)
            process_area_threshold_high_text.delete("1.0", "end")
            process_area_threshold_high_text.insert("1.0", process_area_threshold_high_NUM)
            compare_binary_threshold_text.delete("1.0", "end")
            compare_binary_threshold_text.insert("1.0", compare_threshold_NUM)
            weight_threshold_text.delete("1.0", "end")
            weight_threshold_text.insert("1.0", weight_threshold_NUM)
            pattern_compar_threshold_text.delete("1.0", "end")
            pattern_compar_threshold_text.insert("1.0", pattern_compare_threshold_NUM)
            image_threading_text.delete("1.0", "end")
            image_threading_text.insert("1.0", image_threading_NUM)
            different_threshold_text.delete("1.0", "end")
            different_threshold_text.insert("1.0", different_threshold_NUM)

        img_save_button = tk.Checkbutton(frame2, text="保存比对图片", variable=on_save_img_val,
                                         command=on_save_img)  # , command=on_save_img
        img_save_button.grid(row=11, column=2, padx=10, pady=10, sticky="we")

        listbox = Listbox(frame2, width=20, height=10)
        listbox.grid(row=3, rowspan=3, column=4, padx=10, pady=10, sticky="e")
        scrollbar = Scrollbar(frame2, command=listbox.yview)
        scrollbar.grid(row=4, column=5, sticky="w", padx=10, pady=20)
        listbox.config(yscrollcommand=scrollbar.set)
        image_files = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
        # 将图片文件名添加到列表框中
        for file in image_files:
            listbox.insert(tk.END, file)
        btn_look_this = tk.Button(frame2, text='查看选中图片', width=12, height=1, command=look_this_picture)  #
        btn_look_this.grid(row=3, column=5, padx=10, pady=10, sticky="w")
        btn_delete_this = tk.Button(frame2, text='删除选中图片', width=12, height=1, command=delete_this_picture)  #
        btn_delete_this.grid(row=5, column=5, padx=10, pady=10, sticky="w")


        # @logger.catch()
        # def changeImageMethods(event):
        #     global IMAGEMatchValue
        #     IMAGEMatchValue = xVariableMatch.get()
        #     if IMAGEMatchValue:
        #         with open(imagepickle, 'wb') as f:
        #             pickle.dump(IMAGEMatchValue, f)
        #         tkinter.messagebox.showinfo('show info', '修改成功！')
        #     else:
        #         tk.messagebox.showerror('show error', "请选择方法！")
        #

        @logger.catch()
        def on_closing():
            if messagebox.askokcancel("关闭窗口", "你确定要关闭窗口吗？"):
                # 执行其他关闭窗口前需要进行的操作
                with open(screenshot, 'wb') as f:
                    pickle.dump(screenshotNum, f)
                window.destroy()


        IMAGEMatch = tk.Button(frame2, text='刷新截图参数', width=12, height=1, command=get_cut_params)
        IMAGEMatch.grid(row=7, column=2, padx=10, pady=10, sticky="wens")
        btn_cut_area = tk.Button(frame2, text='选择比对区域', width=12, height=1,
                                 command=lambda: screen_shot(imagepath))  #
        btn_cut_area.grid(row=7, column=3, padx=10, pady=10, sticky="wens")
        # xVariableMatch = tkinter.StringVar(value=IMAGEMatchValue)
        # ImageMatch_list = ttk.Combobox(frame2, textvariable=xVariableMatch)
        # methods = ['cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF_NORMED']
        # ImageMatch_list['value'] = methods
        # ImageMatch_list.grid(row=7, column=3, padx=10, pady=10, sticky="w")
        # ImageMatch_list.bind("<<ComboboxSelected>>", changeImageMethods)
        window.bind("<space>", handle_space)
        window.protocol("WM_DELETE_WINDOW", on_closing)
        window.mainloop()
        try:
            win32event.ReleaseMutex(mutex)
            win32api.CloseHandle(mutex)
        except:
            pass
